from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'
source_overcloud='source /home/stack/overcloudrc;'
source_undercloud='source /home/stack/stackrc;'
overcloud_log_path='/avr/log/containers'
manageable_timeout=300 #Test 009 "Clean"
available_timeout=600 #Test 009 "Clean"
create_bm_server_timeout=800
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
    'switch_ip':'172.16.0.92',
    'switch_user':'ansible',
    'switch_password':'Juniper',
    'tenant_nets':['tempest-shared','tempest-shared'], #Duplicated in order to create 2 BM in parallel in test 010
    'setup':'Virtual_Setup'
}


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
    command = "sudo grep -Rn ' ERROR ' *"
    existing_errors[ip]=ssh_object.ssh_command_only(command)['Stdout'].split('\n')
    print ip+'--> All existing Overcloud ERRORs are now saved!'
    ssh_object.ssh_close()




class AnsibleNetworkingFunctionalityTests(unittest.TestCase):
    #Check Ironic on Overcloud + ERRORs in logs #
    def test_001_ironic_in_catalog(self):
        print '\ntest_001_ironic_in_catalog'
        #spec_print(['Check Ironic on Overcloud + ERRORs in logs'])
        catalog_output=exec_command_line_command(source_overcloud+'openstack catalog show ironic -f json')
        self.assertEqual(catalog_output['JsonOutput']['name'], 'ironic','Failed: ironic was not found in catalog output')

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

    def test_003_errors_in_ironic_logs(self):
        print '\ntest_003_errors_in_ironic_logs'
        command="sudo grep -R ' ERROR ' /var/log/containers/ironic/*"
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            output = ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

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

    def test_005_errors_in_neutron_api(self):
        print '\ntest_005_errors_in_neutron_api'
        command='grep -i error /var/log/containers/neutron/server.log*'
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            output = ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

    @unittest.skipIf(prms['setup'] == 'Virtual_Setup','No indication string on virtual setup!')
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

    def test_008_switch_no_vlans_for_bm_ports(self):
        print '\ntest_008_switch_no_vlans_for_bm_ports'
        interface_vlan=get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        for port in prms['baremetal_guest_ports']:
            self.assertEqual(interface_vlan[port],None,'Failed: '+port+' was found as configured' + port+'\n'+str(interface_vlan))
#
#     def test_009_clean_bm_guests_in_parallel(self):
#         print '\ntest_009_clean_bm_guests_in_parallel'
#         baremetal_vlan_id=exec_command_line_command(source_overcloud+'openstack network show baremetal -f json')['JsonOutput']['provider:segmentation_id']
#         baremetal_node_ids=[item['uuid'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
#         for id in baremetal_node_ids:
#             exec_command_line_command(source_overcloud+'openstack baremetal node manage '+id)
#         for id in baremetal_node_ids:
#             states=[item['provisioning state'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
#         self.assertEqual(['manageable','manageable'], states, 'Failed: baremetal node states are: '+str(states)+' expected: "manageable"')
#         for id in baremetal_node_ids:
#             exec_command_line_command(source_overcloud+'openstack baremetal node provide '+id)
#         start_time=time.time()
#         to_stop=False
#         while to_stop==False and (time.time()<(start_time+manageable_timeout)):
#             time.sleep(5)
#             actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
#             if str(actual_vlans).count(str(baremetal_vlan_id))==len(prms['baremetal_guest_ports']):
#                 to_stop=True
#         self.assertIn(str(baremetal_vlan_id),str(actual_vlans), 'Failed: baremetal ports are not set to baremetal network vlan:\n' +str(actual_vlans))
#         start_time = time.time()
#         to_stop=False
#         while to_stop == False and (time.time()<(start_time+available_timeout)):
#             time.sleep(5)
#             states = [item['provisioning state'] for item in exec_command_line_command(source_overcloud + 'openstack baremetal node list -f json')['JsonOutput']]
#             if states==['available','available']:
#                 to_stop=True
#         self.assertEqual(['available','available'], states, 'Failed: baremetal node states are: '+str(states)+' expected:available')
#
#
#     def test_010_create_bm_guests_in_parallel(self):
#         print '\ntest_010_create_bm_guests_in_parallel'
#         # Create BM Guests
#         bm_name='BM_Guest_'
#         bm_index=0
#         created_bm=[]
#         tenant_nets=prms['tenant_nets']
#         expected_vlans_on_switch=[]
#         # If servers exists, exit #
#         existing_servers_ids=[node['id'] for node in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
#         print existing_servers_ids
#         self.assertEqual(0,len(existing_servers_ids),'Failed: existing nodes have been detected IDs:\n'+str(existing_servers_ids))
#         # Create servers
#         for net in tenant_nets:
#             bm_index+=1
#             vlan_id=exec_command_line_command(source_overcloud+'openstack network show '+net+' -f json')['JsonOutput']['provider:segmentation_id']
#             create_bm_command=source_overcloud+'openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+net+' '+bm_name+str(bm_index)
#             result=exec_command_line_command(source_overcloud+create_bm_command)
#             self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest command return non Zero status code\n'+result['CommandOutput'])
#             expected_vlans_on_switch.append(str(vlan_id))
#         start_time=time.time()
#         to_stop=False
#         # Wait till all servers are getting into "active"
#         while to_stop == False and time.time() < (start_time + create_bm_server_timeout):
#             time.sleep(5)
#             list_servers_result=exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']
#             statuses=[item['status'] for item in list_servers_result]
#             print statuses
#             if str(statuses).count('active')==len(tenant_nets):
#                 to_stop=True
#         self.assertEqual(to_stop,True,'Failed: No BM servers detected as "active", "openstack server list" result is:\n'+str(list_servers_result))
#         # Make sure that each server was created on proper network, basing on VLAN id comparison
#         actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
#         actual_vlans=[actual_vlans[key][0] for key in actual_vlans.keys()]
#         self.assertEqual(set(expected_vlans_on_switch),set(actual_vlans),
#                          'Failed, detected VLANs on swith are not as expected:''\n'+str(actual_vlans)+'\n'+str(expected_vlans_on_switch))
#
#     def test_011_delete_bm_guests_in_parallel(self):
#         print '\ntest_011_delete_bm_guests_in_parallel'
#         existing_server_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
#         self.assertNotEqual(len(existing_server_ids),0,'Failed: no existing servers detected')
#         for id in existing_server_ids:
#             exec_command_line_command(source_overcloud+'openstack server delete '+id)
#         existing_server_ids = [item['id'] for item in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
#         start_time=time.time()
#         to_stop=False
#         # Wait till all servers are deleted "
#         while to_stop == False and time.time() < (start_time + create_bm_server_timeout):
#             time.sleep(5)
#             list_servers_result=exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']
#             if len(list_servers_result)==0:
#                 to_stop=True
#         self.assertEqual(len(list_servers_result), 0, 'Failed: existing servers detected, IDs:\n'+str(list_servers_result))
#
#


    def test_012_no_errors_in_logs(self):
        actual_errors={}
        for ip in nodes_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            command = "sudo grep -Rn ' ERROR ' *"
            actual_errors[ip] = ssh_object.ssh_command_only(command)['Stdout'].split('\n')
            print ip+'--> All existing Overcloud ERRORs are now saved!'
            ssh_object.ssh_close()
        test_failed=False
        for key in actual_errors.keys():
            print '-' * 50 + node_ip_name_dic[ip] + '-' * 50
            for line in actual_errors[key]:
                if line not in existing_errors[key]:
                    print line
                    test_failed=True
        self.assertEqual(test_failed,False,'Failed, ERRORs detected while tests execution:\n')




if __name__ == '__main__':
    unittest.main()
