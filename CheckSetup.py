from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'
source_overcloud='source /home/stack/overcloudrc;'
source_undercloud='source /home/stack/stackrc;'
overcloud_log_path='/var/log/containers'
manageable_timeout=300 #Test 009 "Clean"
available_timeout=600 #Test 009 "Clean"
create_bm_server_timeout=1200
delete_server_timeouts=300

# QE Setup #
qe_setup_parameters={
    'baremetal_guest_ports':['xe-0/0/6', 'xe-0/0/7'],
    'switch_type':'juniper_physical_sw',
    'switch_ip':'10.9.95.25',
    'switch_user':'ansible',
    'switch_password':'N3tAutomation!',
    'tenant_nets':['tenant-net','tenant-net2'],
    'setup':'QE_Setup'
}

# Virtual Setup #
virt_setup_parameters={
    'baremetal_guest_ports':['xe-0/0/7', 'xe-0/0/8'],
    'switch_type':'juniper_emulator_sw',
    'switch_ip':'172.16.0.24',
    'switch_user':'ansible',
    'switch_password':'Juniper',
    'tenant_nets':['tempest-shared','tempest-shared'], #Duplicated in order to create 2 BM in parallel in test 010
    'setup':'Virtual_Setup'
}

# Create key pair #
source_command='source /home/stack/overcloudrc;'
existing_key_pairs=[item['name'] for item in exec_command_line_command(source_command+'openstack keypair list -f json')['JsonOutput']]
print 'Keypairs --> ',existing_key_pairs
if 'default' not in existing_key_pairs:
    result=exec_command_line_command(source_command+'openstack keypair create --public-key /home/stack/.ssh/id_rsa.pub default')

### Get controllers IPs ###
controllers = exec_command_line_command(source_undercloud+'openstack server list --name controller -f json')[
    'JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]

### Get Ceph IPs ###
cephs = exec_command_line_command(source_undercloud+'openstack server list --name cephstorage -f json')[
    'JsonOutput']
cephs_ips = [item['networks'].split('=')[-1] for item in cephs]

### Get Overcloud Node IPs ###
nodes = exec_command_line_command(source_undercloud+'openstack server list -f json')['JsonOutput']
nodes_ips = [item['networks'].split('=')[-1] for item in nodes]
node_ip_name_dic={}
for ip in nodes_ips:
    for node in nodes:
        if ip in str(node):
            node_ip_name_dic[ip] = node['name']

### No Ceph = Virt Setup ###
if cephs==[]:
    prms=virt_setup_parameters
else:
    prms=qe_setup_parameters

### Save all log ERRORs up untill now ###
existing_errors={}
for ip in nodes_ips:
    ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
    ssh_object.ssh_connect_key()
    command = "sudo grep -Rn ' ERROR ' "+overcloud_log_path
    existing_errors[ip]=ssh_object.ssh_command_only(command)['Stdout'].split('\n')
    ssh_object.ssh_close()


class AnsibleNetworkingFunctionalityTests(unittest.TestCase):

    """ This test is planed to validate that Ironic service is in Catalog List (exists on Overcloud) """
    def test_001_ironic_in_catalog(self):
        print '\ntest_001_ironic_in_catalog'
        catalog_output=exec_command_line_command(source_overcloud+'openstack catalog show ironic -f json')
        self.assertEqual(catalog_output['JsonOutput']['name'], 'ironic','Failed: ironic was not found in catalog output')

    """ This test is planed to validate that all Ironic's dockers on controllers are up and running """
    def test_002_ironic_dockers_status(self):
        print '\ntest_002_ironic_dockers_status'
        ironic_dockers=['ironic_pxe_http','ironic_pxe_tftp','ironic_neutron_agent','ironic_conductor','ironic_api']
        for ip in controller_ips:
            ssh_object = SSH(ip,user=overclud_user,key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            for doc in ironic_dockers:
                command='sudo docker ps | grep '+doc
                output=ssh_object.ssh_command(command)['Stdout']
                self.assertNotIn('unhealthy', output, 'Failed: ' + ip + ' ' + doc + ' status is unhealthy')
                self.assertIn(doc, output, 'Failed: ' + doc + ' is not running')
            ssh_object.ssh_close()

    """ This test is planed to validate that no ERRORs exists in Ironic's logs on Overcloud """
    def test_003_errors_in_ironic_logs(self):
        print '\ntest_003_errors_in_ironic_logs'
        command="sudo grep -R ' ERROR ' /var/log/containers/ironic/*"
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            output = ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

    """ This test is planed to validate that neutron_api docker is up and running on all Controllers """
    def test_004_dockers_neutron_api_status(self):
        print '\ntest_004_dockers_neutron_api_status'
        for ip in controller_ips:
            ssh_object = SSH(ip,user=overclud_user,key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            command='sudo docker ps | grep -i neutron_api'
            output=ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('unhealthy', output, 'Failed: '+ip+' '+'neutron_api status is unhealthy')
            self.assertIn('neutron_api', output, 'Failed: neutron_api is not running')

    """ This test is planed to validate that no ERRORS exists in Neutron Server log on all Controllers """
    def test_005_errors_in_neutron_api(self):
        print '\ntest_005_errors_in_neutron_api'
        command='grep -i error /var/log/containers/neutron/server.log*'
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            output = ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

    """ This test is planed to validate that "indication string" which is indicates that 
    Ansible Networking Feature configuration is done, exists in Controllers' logs
    Note: this test may fail after log rotation is done, so this 'indication string'
    won't be existing anymore.
    """
    def test_006_net_ansible_indication_msg_in_log(self):
        print '\ntest_006_net_ansible_indication_msg_in_log'
        output, stderr=[],[]
        commands=["grep -i 'networking_ansible.config' /var/log/containers/neutron/server.log* | grep -i 'ansible host'",
                  "zgrep -i 'networking_ansible.config' /var/log/containers/neutron/server.log* | grep -i 'ansible host'"]
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            for com in commands:
                out = ssh_object.ssh_command(com)
                output.append(out['Stdout'])
                stderr.append(out['Stderr'])
            ssh_object.ssh_close()
        self.assertIn('Ansible Host', str(output), 'Failed: ' + ip +
                      ' no indication for Ansible Networking configuration in log'+'\n'+str(output)+'\n'+str(stderr))

    """ Tis test is planed to validate that Ceph (once included in Setup) is OK (up and running) """
    @unittest.skipIf(prms['setup']=='Virtual_Setup','Ceph is not installed on virtual setup!')
    def test_007_check_ceph_status(self):
        print '\ntest_007_check_ceph_status'
        ceph_status= source_overcloud+" cinder service-list | grep ceph"
        out = exec_command_line_command(ceph_status)['CommandOutput']
        self.assertIn('ceph',out,'Failed: ceph is not running')
        ceph_health_command='ceph health'
        ssh_object = SSH(controller_ips[0],user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
        ssh_object.ssh_connect_key()
        com_output=ssh_object.ssh_command(ceph_health_command)['Stdout']
        ssh_object.ssh_close()
        self.assertIn('HEALTH_OK',com_output,'Failed: "HEALTH_OK" not found in output of \n'+ceph_status+' command')

    """ This test is planed to validate that the Bare Metal Ports on Switch are not set to any VLAN, either: Bremetal or Tenant """
    def test_008_switch_no_vlans_for_bm_ports(self):
        print '\ntest_008_switch_no_vlans_for_bm_ports'
        interface_vlan=get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        for port in prms['baremetal_guest_ports']:
            self.assertEqual(interface_vlan[port],None,'Failed: '+port+' was found as configured' + port+'\n'+str(interface_vlan))

    """ This test is planed to validate that "Clean" procedure is running as expected, in addition it will also
    validate that the Bare Metal Ports on Switch are set to proper VLAN by Ansible Networking, while "Clean" procedure
    Note: this test will clean all existing BM Guest in parallel.
    """
    def test_009_clean_bm_guests_in_parallel(self):
        print '\ntest_009_clean_bm_guests_in_parallel'
        baremetal_vlan_id=exec_command_line_command(source_overcloud+'openstack network show baremetal -f json')['JsonOutput']['provider:segmentation_id']
        baremetal_node_ids=[item['uuid'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node manage '+id)
        for id in baremetal_node_ids:
            states=[item['provisioning state'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        self.assertEqual(['manageable','manageable'], states, 'Failed: baremetal node states are: '+str(states)+' expected: "manageable"')
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node provide '+id)
        start_time=time.time()
        to_stop=False
        while to_stop==False and (time.time()<(start_time+manageable_timeout)):
            time.sleep(10)
            actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
            print actual_vlans
            if str(actual_vlans).count(str(baremetal_vlan_id))==len(prms['baremetal_guest_ports']):
                to_stop=True
        self.assertIn(str(baremetal_vlan_id),str(actual_vlans), 'Failed: baremetal ports are not set to baremetal network vlan:\n' +str(actual_vlans))
        start_time = time.time()
        to_stop=False
        while to_stop == False and (time.time()<(start_time+available_timeout)):
            time.sleep(5)
            states = [item['provisioning state'] for item in exec_command_line_command(source_overcloud + 'openstack baremetal node list -f json')['JsonOutput']]
            print states
            if states==['available','available']:
                to_stop=True
        self.assertEqual(['available','available'], states, 'Failed: baremetal node states are: '+str(states)+' expected:available')

    """ This test is planed to validate that Bare Metal guests creation (as Servers on Overcloud) is successfully done and that
    Ansible Networking feature sets proper VLAN on switch, depending on "network" which is used for creation.
    Note: this test will try to create server per existing Tenant network in "tenant_nets" parameter.
    """
    def test_010_create_bm_guests_in_parallel(self):
        print '\ntest_010_create_bm_guests_in_parallel'
        # Create BM Guests
        bm_name='BM_Guest_'
        bm_index=0
        created_bm=[]
        tenant_nets=prms['tenant_nets']
        expected_vlans_on_switch=[]
        # If servers exists, exit #
        existing_servers_ids=[node['id'] for node in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
        print '--> Existing servers IDs: ',existing_servers_ids
        self.assertEqual(0,len(existing_servers_ids),'Failed: existing nodes have been detected IDs:\n'+str(existing_servers_ids))
        # Create servers
        for net in tenant_nets:
            bm_index+=1
            vlan_id=exec_command_line_command(source_overcloud+'openstack network show '+net+' -f json')['JsonOutput']['provider:segmentation_id']
            create_bm_command=source_overcloud+'openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+net+' '+bm_name+str(bm_index)
            result=exec_command_line_command(source_overcloud+create_bm_command)
            self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest command return non Zero status code\n'+result['CommandOutput'])
            expected_vlans_on_switch.append(str(vlan_id))
        start_time=time.time()
        to_stop=False
        # Wait till all servers are getting into "active"
        while to_stop == False and time.time() < (start_time + create_bm_server_timeout):
            time.sleep(10)
            list_servers_result=exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']
            statuses=[item['status'] for item in list_servers_result]
            print '--> Servers statuses are: ',statuses
            if str(statuses).count('active')==len(tenant_nets):
                to_stop=True
        self.assertEqual(to_stop,True,'Failed: No BM servers detected as "active", "openstack server list" result is:\n'+str(list_servers_result))
        # Make sure that each server was created on proper network, basing on VLAN id comparison
        actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        actual_vlans=[actual_vlans[key] for key in actual_vlans.keys()]
        for vlan in expected_vlans_on_switch:
            self.assertIn(vlan,str(actual_vlans),
                            'Failed, detected VLANs on swith are not as expected:''\n'+str(actual_vlans)+'\n'+str(expected_vlans_on_switch))

    """ This test is planed to validate that "Delete Bare Metal Guests" procedure is successfully completed.
    Note: it will try to delete all detected Servers on Overcloud.
    """
    def test_011_delete_bm_guests_in_parallel(self):
        print '\ntest_011_delete_bm_guests_in_parallel'
        time.sleep(10)
        existing_server_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
        self.assertNotEqual(len(existing_server_ids),0,'Failed: no existing servers detected')
        for id in existing_server_ids:
            exec_command_line_command(source_overcloud+'openstack server delete '+id)
        existing_server_ids = [item['id'] for item in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
        start_time=time.time()
        to_stop=False
        # Wait till all servers are deleted "
        while to_stop == False and time.time() < (start_time + create_bm_server_timeout):
            time.sleep(10)
            list_servers_result=exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']
            print list_servers_result
            if len(list_servers_result)!=0:
                names=[item['name'] for item in list_servers_result]
                print '-- Existing servers are: ',names
            if len(list_servers_result)==0:
                to_stop=True
        self.assertEqual(len(list_servers_result), 0, 'Failed: existing servers detected, IDs:\n'+str(list_servers_result))
    #
    """ This test is planed to search for ERRORs messages in all Overcloud logs and will fail if NEW messages (ERRORS while
    tests execution) will be detected
    Note: current implementation is not efficient, it just saves all ERRORs before tests are being executed and then
    (once tests are completed) it does the same "saving" procedure again and prints NEW/DELTA messages.
    In case when there is a bunch of ERRORs on Overcloud, this test will take some time to complete.
    """
    def test_012_no_errors_in_logs(self):
        print '\ntest_012_no_errors_in_logs'
        error_file_name='Overcloud_Errors.log'
        errors_file=open(error_file_name,'w')
        actual_errors={}
        for ip in nodes_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            command = "sudo grep -Rn ' ERROR ' " + overcloud_log_path
            actual_errors[ip] = ssh_object.ssh_command_only(command)['Stdout'].split('\n')
            ssh_object.ssh_close()
        test_failed=False
        for key in actual_errors.keys():
            errors_file.write('-' * 50 + node_ip_name_dic[key] + '-' * 50+'\n')
            for line in actual_errors[key]:
                if line not in existing_errors[key]:
                    test_failed=True
                    errors_file.write(line+'\n')
        errors_file.close()
        self.assertEqual(test_failed,False,'Failed, see details here: \n'+open(error_file_name,'r').read())

if __name__ == '__main__':
    unittest.main()
