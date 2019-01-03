from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'
source_overcloud='source /home/stack/overcloudrc;'
source_undercloud='source /home/stack/stackrc;'
manageable_timeout=300 #Test 009 "Clean"
available_timeout=300 #Test 009 "Clean"
create_bm_server_timeout=300


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
    'tenant_nets':['tempest-shared'],
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

### No Ceph = Virt Setup ###
if cephs==[]:
    prms=virt_setup_parameters
else:
    prms=qe_setup_parameters


class AnsibleNetworkingFunctionalityTests(unittest.TestCase):
    # Check Ironic on Overcloud + ERRORs in logs #
    # def test_001_ironic_in_catalog(self):
    #     print '\ntest_001_ironic_in_catalog'
    #     #spec_print(['Check Ironic on Overcloud + ERRORs in logs'])
    #     catalog_output=exec_command_line_command(source_overcloud+'openstack catalog show ironic -f json')
    #     self.assertEqual(catalog_output['JsonOutput']['name'], 'ironic','Failed: ironic was not found in catalog output')
    #
    # def test_002_ironic_dockers_status(self):
    #     print '\ntest_002_ironic_dockers_status'
    #     ironic_dockers=['ironic_pxe_http','ironic_pxe_tftp','ironic_neutron_agent','ironic_conductor','ironic_api']
    #     for ip in controller_ips:
    #         ssh_object = SSH(ip,user=overclud_user,key_path=overcloud_ssh_key)
    #         ssh_object.ssh_connect_key()
    #         for doc in ironic_dockers:
    #             command='sudo docker ps | grep '+doc
    #             output=ssh_object.ssh_command(command)['Stdout']
    #             self.assertNotIn('unhealthy', output, 'Failed: ' + ip + ' ' + doc + ' status is unhealthy')
    #             self.assertIn(doc, output, 'Failed: ' + doc + ' is not running')
    #         ssh_object.ssh_close()
    #
    # def test_003_errors_in_ironic_logs(self):
    #     print '\ntest_003_errors_in_ironic_logs'
    #     command="sudo grep -R ' ERROR ' /var/log/containers/ironic/*"
    #     for ip in controller_ips:
    #         ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
    #         ssh_object.ssh_connect_key()
    #         output = ssh_object.ssh_command(command)['Stdout']
    #         ssh_object.ssh_close()
    #         self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)
    #
    # def test_004_dockers_neutron_api_status(self):
    #     print '\ntest_004_dockers_neutron_api_status'
    #     for ip in controller_ips:
    #         ssh_object = SSH(ip,user=overclud_user,key_path=overcloud_ssh_key)
    #         ssh_object.ssh_connect_key()
    #         command='sudo docker ps | grep -i neutron_api'
    #         output=ssh_object.ssh_command(command)['Stdout']
    #         ssh_object.ssh_close()
    #         self.assertNotIn('unhealthy', output, 'Failed: '+ip+' '+'neutron_api status is unhealthy')
    #         self.assertIn('neutron_api', output, 'Failed: neutron_api is not running')
    #
    # def test_005_errors_in_neutron_api(self):
    #     print '\ntest_005_errors_in_neutron_api'
    #     command='grep -i error /var/log/containers/neutron/server.log*'
    #     for ip in controller_ips:
    #         ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
    #         ssh_object.ssh_connect_key()
    #         output = ssh_object.ssh_command(command)['Stdout']
    #         ssh_object.ssh_close()
    #         self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)
    #
    # @unittest.skipIf(setup_params['setup'] == 'Virtual_Setup','No indication string on virtual setup!')
    # def test_006_net_ansible_indication_msg_in_log(self):
    #     print '\ntest_006_net_ansible_indication_msg_in_log'
    #     commands=["grep -i 'networking_ansible.config' /var/log/containers/neutron/server.log* | grep -i 'ansible host'",
    #               "zgrep -i 'networking_ansible.config' /var/log/containers/neutron/server.log* | grep -i 'ansible host'"]
    #     output = []
    #     stderr = []
    #     for ip in controller_ips:
    #         ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
    #         ssh_object.ssh_connect_key()
    #         for com in commands:
    #             out = ssh_object.ssh_command(com)
    #             output.append(out['Stdout'])
    #             stderr.append(out['Stderr'])
    #         ssh_object.ssh_close()
    #     self.assertIn('Ansible Host', str(output), 'Failed: ' + ip +
    #                   ' no indication for Ansible Networking configuration in log'+'\n'+str(output)+'\n'+str(stderr))
    #
    # @unittest.skipIf(setup_params['setup']=='Virtual_Setup','Ceph is not installed on virtual setup!')
    # def test_007_check_ceph_status(self):
    #     print '\ntest_007_check_ceph_status'
    #     ceph_status= source_overcloud+" cinder service-list | grep ceph"
    #     out = exec_command_line_command(ceph_status)['CommandOutput']
    #     self.assertIn('ceph',out,'Failed: ceph is not running')
    #     ceph_health_command='ceph health'
    #     ssh_object = SSH(controller_ips[0],user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
    #     ssh_object.ssh_connect_key()
    #     com_output=ssh_object.ssh_command(ceph_health_command)['Stdout']
    #     ssh_object.ssh_close()
    #     self.assertIn('HEALTH_OK',com_output,'Failed: "HEALTH_OK" not found in output of \n'+ceph_status+' command')

    def test_008_switch_no_vlans_for_bm_ports(self):
        print '\ntest_008_switch_no_vlans_for_bm_ports'
        interface_vlan=get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
        for port in prms['baremetal_guest_ports']:
            self.assertEqual(interface_vlan[port],[],'Failed: '+port+' was found as configured' + port+'\n'+str(interface_vlan))

    def test_009_clean_bm_guests_in_parallel(self):
        print '\ntest_009_clean_bm_guests_in_parallel'
        baremetal_vlan_id=exec_command_line_command(source_overcloud+'openstack network show baremetal -f json')['JsonOutput']['provider:segmentation_id']
        baremetal_node_ids=[item['uuid'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node manage '+id)
        for id in baremetal_node_ids:
            states=[item['provisioning state'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        self.assertEqual(['manageable','manageable'], states, 'Failed: baremetal node states are: '+str(states)+' expected:manageable')
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node provide '+id)
        start_time=time.time()
        to_stop=False
        while to_stop or (time.time()>(start_time+manageable_timeout)):
            print '----',to_stop or (time.time()>(start_time+manageable_timeout))
            time.sleep(5)
            actual_vlans = get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])
            print actual_vlans
            actual_vlans=list(set([item[key] for key in actual_vlans.keys()]))
            if actual_vlans[0]==baremetal_vlan_id:
                to_stop=True
        print actual_vlans
        self.assertEqual(actual_vlans[0], baremetal_vlan_id, 'Failed: baremetal ports are set to incorrect vlans:\n' +
                         str(get_juniper_sw_get_port_vlan(prms['switch_ip'], prms['switch_user'], prms['switch_password'], prms['baremetal_guest_ports'])))
        start_time = time.time()
        to_stop=False
        while to_stop or (time.time()>(start_time+available_timeout)):
            print '----', to_stop or (time.time() > (start_time + manageable_timeout))
            time.sleep(5)
            states = [item['provisioning state'] for item in exec_command_line_command(source_overcloud + 'openstack baremetal node list -f json')['JsonOutput']]
            if states==['available','available']:
                to_stop=True
            print states
            print to_stop

        self.assertEqual(['available','available'], states, 'Failed: baremetal node states are: '+str(states)+' expected:available')





    # def test_010_create_bm_guests_in_parallel(self):
    #     print '\ntest_010_create_bm_guests_in_parallel'
    #     # Get VLAN tag per tenant network
    #     tenant_net1_vlan=exec_command_line_command(source_overcloud+'openstack network show '+tenant_net_1_name+' -f json')['JsonOutput']['provider:segmentation_id']
    #     tenant_net2_vlan=exec_command_line_command(source_overcloud+'openstack network show '+tenant_net_2_name+' -f json')['JsonOutput']['provider:segmentation_id']
    #     # Create BM Guests
    #     for net in tenant_nets:
    #         create_bm1_command='openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+net+' t'+net
    #         create_bm2_command='openstack server create --flavor baremetal --image overcloud-full --key default --nic net-id='+net+' t'+net
    #         exec_command_line_command(source_overcloud+create_bm1_command)
    #         exec_command_line_command(source_overcloud+create_bm2_command)
    #     start_time=time.time()
    #     to_stop=False
    #     while to_stop == False or time.time() > (start_time + create_bm_server_timeout):
    #         time.sleep(5)
    #         list_servers_result=exec_command_line_command(source_overcloud+'openstack server list -f json')['JsonOutput']
    #         ids=sort([item['id'] for item in list_servers_result])
    #         statuses=sort([item['status'] for item in list_servers_result])
    #         print names
    #         print statuses
    #         if names==len(ids)==2 and statuses==['active','active']:
    #             to_stop=True
    #     self.assertEqual(to_stop,True,'Failed: No BM servers detected, "openstack server list" result is:\n'+str(list_servers_result))
    #
    #
    #



if __name__ == '__main__':
    unittest.main()
