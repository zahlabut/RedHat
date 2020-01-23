from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'
source_overcloud='source /home/stack/overcloudrc;'
source_undercloud='source /home/stack/stackrc;'
source_tenant_user='source /home/stack/userrc;'
overcloud_log_path='/var/log'
manageable_timeout=600 #Test 009 "Clean"
available_timeout=600 #Test 009 "Clean"
create_bm_server_timeout=1200
delete_server_timeouts=300
if '15' in exec_command_line_command('cat /etc/rhosp-release')['CommandOutput']:
    use_podman=True
if '16' in exec_command_line_command('cat /etc/rhosp-release')['CommandOutput']:
    use_podman=True

'''
#####################################################################################
To run a single test, execute:
python2 CheckSetup.py AnsibleNetworkingFunctionalityTests.test_001_ironic_in_catalog
#####################################################################################
'''

# QE Setup #
qe_setup_parameters={
    'baremetal_guest_ports':['xe-0/0/6', 'xe-0/0/7'],#,'xe-0/0/42','xe-0/0/43','xe-0/0/44','xe-0/0/45'],
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
    # Create key pair #
    source_command = 'source /home/stack/overcloudrc;'
    existing_key_pairs = [item['name'] for item in
                          exec_command_line_command(source_command + 'openstack keypair list -f json')['JsonOutput']]
    print 'Keypairs --> ', existing_key_pairs
    if 'default' not in existing_key_pairs:
        result = exec_command_line_command(
            source_command + 'openstack keypair create --public-key /home/stack/.ssh/id_rsa.pub default')
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

    def setUp(self):
        print "\n--> SetUp Start"
        # Chack that BM guest are imported on Overcloud #
        self.baremetal_node_ids=[item['uuid'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        print '-- Existing BM node IDs are: '+str(self.baremetal_node_ids)
        self.assertNotEqual(0,len(self.baremetal_node_ids),'Failed, no baremetal nodes detected')
        # Check provisioning state
        self.baremetal_node_states=[item['provisioning state'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        if list(set(self.baremetal_node_states))!=['enroll']:
            # Make sure that BM Nodes are in "available" and wait some time if needed
            status=wait_till_bm_is_in_state(source_overcloud, 'available')
            self.assertEquals(True,status,'Failed, not all BM are in "available" Provisioning State!')

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
                if use_podman==True:
                    command=command.replace('docker','podman')
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
            if use_podman == True:
                command = command.replace('docker', 'podman')
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
            if len(output)>10000:
                output=output[0:1000]+'...\n'*5+output[-10000:-1]
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

    """ This test is planed to validate that "indication string" which is indicates that
    Ansible Networking Feature configuration is done, exists in Controllers' logs
    Note: this test may fail after log rotation is done, so this 'indication string'
    won't be existing anymore.
    """
    def test_006_net_ansible_indication_msg_in_log(self):
        print '\ntest_006_net_ansible_indication_msg_in_log'
        for ip in controller_ips:
            commands=[]
            output, stderr = [], []
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            log_files=ssh_object.ssh_command('sudo ls /var/log/containers/neutron | grep -i server')['Stdout']
            log_files=[fil.strip() for fil in log_files.splitlines()]
            for fil in log_files:
                if fil.endswith('.gz') == True:
                    commands.append("sudo zgrep -i 'networking_ansible.config' /var/log/containers/neutron/"+fil+" | grep -i 'ansible host'")
                else:
                    commands.append("sudo grep -i 'networking_ansible.config' /var/log/containers/neutron/" +fil+" | grep -i 'ansible host'")
            for com in commands:
                out=ssh_object.ssh_command(com)
                output.append(out['Stdout'])
                stderr.append(out['Stderr'])
            ssh_object.ssh_close()
            self.assertIn('Ansible Host'.lower(), str(output).lower(), 'Failed: ' + ip +
                          ' no indication for Ansible Networking configuration in log'+'\n'+str(output)+'\n'+str(stderr))

    """ This test is planed to validate that Ceph (once included in Setup) is OK (up and running) """
    @unittest.skipIf(prms['setup']=='Virtual_Setup','Ceph is not installed on virtual setup!')
    def test_007_check_ceph_status(self):
        print '\ntest_007_check_ceph_status'
        ceph_status= source_overcloud+" cinder service-list | grep ceph"
        out = exec_command_line_command(ceph_status)['CommandOutput']
        self.assertIn('ceph',out,'Failed: ceph is not running')
        # ### Now since OSP15 it's inside docker, see Eliad Cohen email to me
        # ceph_health_command='ceph health'
        # ssh_object = SSH(controller_ips[0],user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
        # ssh_object.ssh_connect_key()
        # com_output=ssh_object.ssh_command(ceph_health_command)['Stdout'].lower()
        # ssh_object.ssh_close()
        # print com_output
        # self.assertIn('up',com_output,'Failed: "up" not found in output of \n"'+com_output+'" command')

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
        baremetal_node_ids=[item['uuid'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        baremetal_vlan_id = exec_command_line_command(source_overcloud + 'openstack network show baremetal -f json')['JsonOutput']['provider:segmentation_id']
        # Change state to "manageable"
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node manage '+id)
        status=wait_till_bm_is_in_state(source_overcloud, 'manageable')
        self.assertEquals(True,status,'Failed, BM are not in "manageable" Provisioning State!')
        # Start "Clean"
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
        status=wait_till_bm_is_in_state(source_overcloud, 'available')
        self.assertEquals(True,status,'Failed, BM are not in "available" Provisioning State!')

    """ This test is planed to validate that Bare Metal guests creation (as Servers on Overcloud) is successfully done and that
    Ansible Networking feature sets proper VLAN on switch, depending on "network" which is used for creation.
    Note: this test will try to create server per existing Tenant network in "tenant_nets" parameter.
    In addition to that, floating IP will be added to each server and then it will use SSH+PING to validate that
    there is no connectivity between servers not in the same VLAN, VMs are also covered in this test. 
    """
    def test_010_create_bm_guests_in_parallel_and_check_connectivity(self):
        print '\ntest_010_create_bm_guests_in_parallel'
        # Create Servers
        bm_name='BM_Guest_'
        vm_name='VM_'
        counter=0
        tenant_nets=prms['tenant_nets']
        tenant_net_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack network list -f json')['JsonOutput'] if item['name'] in tenant_nets]
        self.assertNotEqual(0,len(tenant_net_ids),'Failed, no tenant networks detected')
        expected_vlans_on_switch=[]
        # Create servers
        for net in tenant_net_ids:
            counter+=1
            vlan_id=exec_command_line_command(source_overcloud+'openstack network show '+net+' -f json')['JsonOutput']['provider:segmentation_id']
            create_bm_command=source_overcloud+'openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+net+' '+bm_name+str(counter)
            result=exec_command_line_command(create_bm_command)
            self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest, command return non Zero status code\n'+result['CommandOutput'])
            create_vm_command=source_overcloud+'openstack server create --flavor small --image overcloud-full --key default --nic net-id='+net+' '+vm_name+str(counter)
            result=exec_command_line_command(create_vm_command)
            self.assertEqual(0, result['ReturnCode'], 'Failed: create VM, command return non Zero status code\n'+result['CommandOutput'])
            expected_vlans_on_switch.append(str(vlan_id))

        # Wait till all servers are getting into "active"
        result=wait_till_servers_are_active(source_overcloud)
        self.assertEquals(True, result, 'Failed, not all Servers are in "active" status!')

        # Make sure that each server was created on proper network, basing on VLAN id comparison
        actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        actual_vlans=[actual_vlans[key] for key in actual_vlans.keys()]
        for vlan in expected_vlans_on_switch:
            self.assertIn(str(vlan),str(actual_vlans),
                            'Failed, detected VLANs on swith are not as expected:''\n'+str(actual_vlans)+'\n'+str(expected_vlans_on_switch))
        # Add Floating IP to each server
        server_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
        servers_info=[]
        for id in server_ids:
            server_info={}
            server_info['InternalIp']=exec_command_line_command(source_overcloud+'openstack server show '+id+' -f json')['JsonOutput']['addresses'].split('=')[1]
            result=exec_command_line_command(source_overcloud+'openstack floating ip create external -f json')['JsonOutput']
            server_info['FloatingIpId']=result['id']
            server_info['FloatingIp']=result['floating_ip_address']
            server_info['Name']=exec_command_line_command(source_overcloud+'openstack server show '+id+' -f json')['JsonOutput']['name']
            add_result=exec_command_line_command(source_overcloud+'openstack server add floating ip '+id+' '+server_info['FloatingIpId'])
            print server_info
            self.assertEquals(add_result['ReturnCode'],0,'Failed to add Floating Ip to Server: '+id)
            servers_info.append(server_info)
        # Ping test, should fail, because BM guests are not on the same VLAN

        # BM_Guest_1 VM_1 --> OK
        # BM_Guest_1 VM_2 --> FAIL
        # BM_Guest_2 VM_2 --> OK
        # BM_Guest_1 VM_1 --> FAIL

        print servers_info
        first_bm_ip=[server['FloatingIp'] for server in servers_info if server['Name']=='BM_Guest_1'.lower()][0]
        print first_bm_ip
        for server in servers_info:
            ping_command = 'ssh cloud-user@' + first_bm_ip + ' ping ' + server['InternalIp'] + ' -c 2'
            print '--> '+ping_command
            ping_result = exec_command_line_command(ping_command)['CommandOutput']
            if server['Name'].split('_')[-1]=='1':
                self.assertIn('time=',ping_result, 'Failed, PING \n'+ping_result)
            else:
                self.assertNotIn('time=', ping_result, 'Failed, PING did worked somehow :(\n' + ping_result)


    """ This test is planed to validate that "Delete Bare Metal Guests" procedure is successfully completed.
    Note: it will try to delete all detected Servers on Overcloud.
    """
    def test_011_delete_bm_guests_in_parallel(self):
        print '\ntest_011_delete_bm_guests_in_parallel'
        # Create BM Guests
        bm_name='BM_Guest_'
        bm_index=0
        tenant_nets=prms['tenant_nets']
        tenant_net_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack network list -f json')['JsonOutput'] if item['name'] in tenant_nets]
        self.assertNotEqual(0,len(tenant_net_ids),'Failed, no tenant networks detected')
        expected_vlans_on_switch=[]
        # Create servers
        for net in tenant_net_ids:
            bm_index+=1
            vlan_id=exec_command_line_command(source_overcloud+'openstack network show '+net+' -f json')['JsonOutput']['provider:segmentation_id']
            create_bm_command=source_overcloud+'openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+net+' '+bm_name+str(bm_index)
            result=exec_command_line_command(create_bm_command)
            self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest command return non Zero status code\n'+result['CommandOutput'])
            expected_vlans_on_switch.append(str(vlan_id))

        # Wait till all servers are getting into "active"
        result=wait_till_servers_are_active(source_overcloud)
        self.assertEquals(True, result, 'Failed, not all Servers are in "active" status!')

        # Make sure that each server was created on proper network, basing on VLAN id comparison
        actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        actual_vlans=[actual_vlans[key] for key in actual_vlans.keys()]
        for vlan in expected_vlans_on_switch:
            self.assertIn(str(vlan),str(actual_vlans),
                            'Failed, detected VLANs on swith are not as expected:''\n'+str(actual_vlans)+'\n'+str(expected_vlans_on_switch))
        # Delete BM Guests
        existing_server_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']]
        self.assertNotEqual(len(existing_server_ids),0,'Failed: no existing servers detected')
        print '--> Existing servers IDs: ',existing_server_ids
        if existing_server_ids!=[]:
            delete_result=delete_server(source_overcloud, existing_server_ids, 300)
            self.assertEquals(True, delete_result, 'Failed to delete existing servers: '+str(existing_server_ids))

    """This test is a negative test, that is trying to create a VXLAN network type which is not supported when
    on physical switches, so proper error message should be displayed to user"""
    def test_012_negative_create_vxlan_network(self):
        print '\ntest_012_negative_create_vxlan_network'
        command=source_overcloud+"openstack network create --provider-network-type xvlan --provider-physical-network baremetal zababun_vxlan"
        command_result=exec_command_line_command(command)['CommandOutput']
        self.assertIn('not supported',command_result,"Failed, VXLAN network was successfully created, not supported option!")

    """This test is planned to check that once Overcloud admin user delete user (userrc) that has active server, physical
    port on switch will remain associated to the same VLAN it was before (no change on Switch)"""
    def test_013_delete_tenant_user(self):
        print '\ntest_013_delete_tenant_user'
        # Check if tenant user and projects exists at all
        existing_users = [item['name'] for item in
                          exec_command_line_command(source_overcloud + 'openstack user list -f json')['JsonOutput']]
        self.assertIn('new-user',existing_users,'Failed, there is no existing tenant user: "new-user"')
        self.assertEqual(os.path.exists(source_tenant_user.replace('source ','').replace(';','')),True,'Failed, no source file for tenant user exists (userrc file)')
        existing_projects = [item['name'] for item in
                             exec_command_line_command(source_overcloud + 'openstack project list -f json')['JsonOutput']]
        self.assertIn('new-project',existing_projects,'Failed, there is no existing project: "new-project"')
        # Create server as tenant user
        bm_name='BM_Guest_Tenant_User'
        tenant_net=prms['tenant_nets'][0]
        tenant_net_id=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack network list -f json')['JsonOutput'] if item['name'] == tenant_net][0]
        expected_vlans_on_switch=[]
        vlan_id=exec_command_line_command(source_overcloud+'openstack network show '+tenant_net+' -f json')['JsonOutput']['provider:segmentation_id']
        create_bm_command=source_tenant_user+'openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+str(tenant_net_id)+' '+bm_name+' -f json'
        result=exec_command_line_command(create_bm_command)
        self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest command has failed with:\n'+result['CommandOutput'])
        expected_vlans_on_switch.append(str(vlan_id))
        start_time=time.time()
        to_stop=False


        # Wait till all servers are getting into "active"
        result=wait_till_servers_are_active(source_overcloud)
        self.assertEquals(True, result, 'Failed, not all Servers are in "active" status!')

        # Make sure that each server was created on proper network, basing on VLAN id comparison
        actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        actual_vlans=[actual_vlans[key] for key in actual_vlans.keys()]
        for vlan in expected_vlans_on_switch:
            self.assertIn(str(vlan),str(actual_vlans),
                            'Failed, detected VLANs on swith are not as expected:''\n'+str(actual_vlans)+'\n'+str(expected_vlans_on_switch))

        # As admin user delete tenant user with existing BM guest
        delete_user_command=source_overcloud+'openstack user delete new-user'
        self.assertEqual(0,exec_command_line_command(delete_user_command)['ReturnCode'], 'Failed, delete tenant user command has failed')
        new_actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        new_actual_vlans=[new_actual_vlans[key] for key in new_actual_vlans.keys()]
        self.assertEqual(new_actual_vlans,actual_vlans,'Failed, VLAN was changed after deleting tenant user\n'+str(actual_vlans)+' --> '+str(new_actual_vlans))

    """This test is planned to check that when BM guest is powered off, physical
    port on switch will remain associated to the same VLAN it was before (no change on Switch)"""
    def test_014_power_off_bm_guest(self):
        print '\ntest_014_power_off_bm_guest'
        # Create server as admin user
        bm_name='BM_Guest'
        tenant_net=prms['tenant_nets'][0]
        tenant_net_id = [item['id'] for item in exec_command_line_command(source_overcloud + 'openstack network list -f json')['JsonOutput'] if item['name'] == tenant_net][0]
        expected_vlans_on_switch=[]
        vlan_id=exec_command_line_command(source_overcloud+'openstack network show '+tenant_net+' -f json')['JsonOutput']['provider:segmentation_id']
        create_bm_command=source_overcloud+'openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+str(tenant_net_id)+' '+bm_name+' -f json'
        result=exec_command_line_command(create_bm_command)
        self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest command has failed with:\n'+result['CommandOutput'])
        expected_vlans_on_switch.append(str(vlan_id))

        # Wait till all servers are getting into "active"
        result=wait_till_servers_are_active(source_overcloud)
        self.assertEquals(True, result, 'Failed, not all Servers are in "active" status!')

        # Make sure that each server was created on proper network, basing on VLAN id comparison
        actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        actual_vlans=[actual_vlans[key] for key in actual_vlans.keys()]
        for vlan in expected_vlans_on_switch:
            self.assertIn(str(vlan),str(actual_vlans),
                            'Failed, detected VLANs on swith are not as expected:''\n'+str(actual_vlans)+'\n'+str(expected_vlans_on_switch))
        # As admin user power off BM guest and check that port on Swich is not changed after doing that
        baremetal_node_id = [item['uuid'] for item in
                             exec_command_line_command(source_overcloud + 'openstack baremetal node list -f json')[
                                 'JsonOutput'] if item['provisioning state'] == 'active'][0]
        power_off_command=source_overcloud+'openstack baremetal node power off '+baremetal_node_id
        self.assertEqual(0,exec_command_line_command(power_off_command)['ReturnCode'],'Failed, power off BM guest command has failed')
        new_actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        new_actual_vlans=[new_actual_vlans[key] for key in new_actual_vlans.keys()]
        self.assertEqual(new_actual_vlans,actual_vlans,'Failed, VLAN was changed after deleting tenant user\n'+str(actual_vlans)+' --> '+str(new_actual_vlans))

    """This test is planned to check that there are no garbage strings (In comments for example) set by developers on Switch"""
    def test_015_no_garbage_strings_on_switch(self):
        print '\ntest_015_no_garbage_strings_on_switch'
        # Receive switch configuration file content
        switch_conf_content = get_switch_configuration_file(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['switch_type'])
        profanity_result=profanity_check(switch_conf_content, 'description')
        self.assertEqual(False, profanity_result['ProfanityCheckResult'],'Failed, profanity check failed on line: "'+str(profanity_result['Failed_Line'])+'" check switch configuration file content')

    """This test is planed to test Trunk, so it will try to create BM guest connected to port set as Trunk
    one or more Vlans.
    Test will verify that the BM Guest is created and that Ansible Networking took care to configure Trunk port as expected
    """
    def test_016_create_trunk_bm_guest(self):
        # Check if parent port exists, create if needed.
        ports=exec_command_line_command(source_overcloud+'openstack port list -f json')
        if ports['ReturnCode']==0:
            ports=[item['name'] for item in ports['JsonOutput']]
            if 'PARENT_PORT_1'.lower() not in ports:
                port=exec_command_line_command(source_overcloud+'openstack port create --network tenant-net PARENT_PORT_1')
                self.assertEqual(port['ReturnCode'], 0,'Failed to create TRUNK port!')
        # Check in trunk network exists, create if needed.
        networks=exec_command_line_command(source_overcloud+'openstack network trunk list -f json')
        if networks['ReturnCode']==0:
            networks=[item['name'] for item in networks['JsonOutput']]
            if 'TRUNK_NET_1'.lower() not in networks:
                port=exec_command_line_command(source_overcloud+'openstack network trunk create --parent-port PARENT_PORT_1 TRUNK_NET_1')
                self.assertEqual(port['ReturnCode'], 0,'Failed to create TRUNK network!')
        # Check in subport exists, create if needed.
        ports=exec_command_line_command(source_overcloud+'openstack port list -f json')
        if ports['ReturnCode']==0:
            ports=[item['name'] for item in ports['JsonOutput']]
            if 'SUB_PORT_1'.lower() not in ports:
                port=exec_command_line_command(source_overcloud+'openstack port create --network tenant-net2 SUB_PORT_1')
                self.assertEqual(port['ReturnCode'], 0,'Failed to create SubPort port!')
        # Add subport to trunk network
        net_details=exec_command_line_command(source_overcloud+'openstack network show tenant-net2 -f json')
        if net_details['ReturnCode']==0:
            segmantation_id=net_details['JsonOutput']['provider:segmentation_id']
            segmantation_id=str(segmantation_id)
        subport_id=exec_command_line_command(source_overcloud+'openstack port list -f json')
        if subport_id['ReturnCode']==0:
            subport_id=[item['id'] for item in subport_id['JsonOutput'] if 'SUB_PORT_1'.lower() in item['name']][0]
        trunk_network_info=exec_command_line_command(source_overcloud+'source /home/stack/overcloudrc;openstack network trunk show TRUNK_NET_1')
        if trunk_network_info['ReturnCode']==0:
            if subport_id not in str(trunk_network_info['CommandOutput']).lower():
                add_subport_to_net=exec_command_line_command(source_overcloud+'openstack network trunk set --subport port=SUB_PORT_1,segmentation-type=vlan,segmentation-id='+segmantation_id+' TRUNK_NET_1')
                self.assertEqual(add_subport_to_net['ReturnCode'],0, 'Failed to add subport to trunk network!')
        # Create servers
        admin_project_id=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack project list -f json')['JsonOutput']
                          if item['name']=='admin'][0]
        default_sec_gr_id=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack security group list -f json')['JsonOutput'] if
                           item['project']==admin_project_id][0]
        create_bm_command=source_overcloud+'openstack server create --image overcloud-full --security-group '+default_sec_gr_id+' --flavor baremetal --port PARENT_PORT_1 --key default BM_Guest1'
        result=exec_command_line_command(create_bm_command)
        self.assertEqual(0, result['ReturnCode'], 'Failed: create BM guest command return non Zero status code\n'+result['CommandOutput'])


        # Wait till all servers are getting into "active"
        result=wait_till_servers_are_active(source_overcloud)
        self.assertEquals(True, result, 'Failed, not all Servers are in "active" status!')

        # Check Trunk on Switch port
        actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        print 'Detected Vlans on Switch Port are: '+str(actual_vlans)
        test_pass=False
        for key in actual_vlans.keys():
            if actual_vlans[key]!=None:
                if len(actual_vlans[key])>1:
                    test_pass=True
                    break
        self.assertEquals(True, test_pass, 'Failed, no port with more than one Vlan was detected, existing configuration on '
                                                          'Switch is: '+str(actual_vlans))


    """ This test is planed to search for ERRORs messages in all Overcloud logs and will fail if NEW messages (ERRORS while
    tests execution) will be detected
    Note: current implementation is not efficient, it just saves all ERRORs before tests are being executed and then
    (once tests are completed) it does the same "saving" procedure again and prints NEW/DELTA messages.
    In case when there is a bunch of ERRORs on Overcloud, this test will take some time to complete.
    """
    def test_017_no_errors_in_logs(self):
        print '\ntest_016_no_errors_in_logs'
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
        for ip in actual_errors.keys():
            errors_file.write('-' * 50 + node_ip_name_dic[ip] + '-' * 50+'\n')
            for line in actual_errors[ip]:
                if line not in existing_errors[ip]:
                    #print line
                    test_failed=True
                    errors_file.write(line+'\n')
        errors_file.close()
        self.assertEqual(test_failed,False,'Failed, open '+error_file_name+' for more details!')



    def tearDown(self):
        print '\n--> TearDown start'
        # Delete all existing BM guests if any #
        self.existing_servers_ids=[node['id'] for node in exec_command_line_command(source_overcloud+'openstack server list --all -f json')['JsonOutput']]
        print '--> Existing servers IDs: ',self.existing_servers_ids
        if self.existing_servers_ids!=[]:
            print '--> Delete all existing BM Guests'
            delete_result=delete_server(source_overcloud, self.existing_servers_ids, 300)
            self.assertEquals(True, delete_result, 'Failed to delete existing servers: '+str(self.existing_servers_ids))

        # Delete all existing Floating IPs if any
        self.existing_floating_ip_ids=[item['id'] for item in exec_command_line_command(source_overcloud+'openstack floating ip list -f json')['JsonOutput']]
        for id in self.existing_floating_ip_ids:
            exec_command_line_command(source_overcloud+'openstack floating ip delete '+id)

if __name__ == '__main__':
    unittest.main()
