from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'
bare_metal_guest_ports=['xe-0/0/6','xe-0/0/7']
conf_switch_file = 'sw_conf.json'
switch_ip='10.9.95.25'
switch_user='ansible'
switch_password='N3tAutomation!'
tenant_net_1_name='tenant_net'
tenant_net_2_name='tenant_net2'
source_overcloud='source /home/stack/overcloudrc;'
souurce_undercloud='source /home/stack/stackrc;'

### Get controllers IPs ###
controllers = exec_command_line_command(souurce_undercloud+'openstack server list --name controller -f json')[
    'JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]

### Get Ceph IPs ###
cephs = exec_command_line_command(souurce_undercloud+'openstack server list --name cephstorage -f json')[
    'JsonOutput']
cephs_ips = [item['networks'].split('=')[-1] for item in cephs]

class AnsibleNetworkingFunctionalityTests(unittest.TestCase):
    # Check Ironic on Overcloud + ERRORs in logs #
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
        command='sudo grep -R ERROR /var/log/containers/ironic/*'
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

    def test_006_net_ansible_indication_msg_in_log(self):
        print '\ntest_006_net_ansible_indication_msg_in_log'
        commands=["grep 'networking_ansible.config' /var/log/containers/neutron/server.log* | grep 'Ansible Host'",
                  "zgrep 'networking_ansible.config' /var/log/containers/neutron/server.log* | grep 'Ansible Host'"]
        output = []
        stderr = []
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
        exec_command_line_command("sshpass -p "+switch_password+" ssh "+switch_user+"@"+switch_ip+" 'show configuration | display json' > "+conf_switch_file)
        interface_vlan=juniper_config_parser(conf_switch_file)['InterfaceVlan']
        for port in bare_metal_guest_ports:
            self.assertNotIn(port,interface_vlan.keys(),'Failed: '+port+' was found as configured' + port+' \n'+str(interface_vlan))

    def test_009_clean_bm_guests_in_parallel(self):
        baremetal_vlan_id=exec_command_line_command(source_overcloud+'openstack network show baremetal -f json')['JsonOutput']['provider:segmentation_id']
        baremetal_node_ids=[item['uuid'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node manage '+id)
        for id in baremetal_node_ids:
            states=[item['provisioning state'] for item in exec_command_line_command(source_overcloud+'openstack baremetal node list -f json')['JsonOutput']]
        self.assertEqual(['manageable','manageable'], states, 'Failed: baremetal node states are: '+str(states))
        for id in baremetal_node_ids:
            exec_command_line_command(source_overcloud+'openstack baremetal node provide '+id)
        start_time=time.time()
        to_stop=False
        while to_stop==False or time.time()>(start_time+300):
            all_valans=exec_command_line_command(
                "sshpass -p " + switch_password + " ssh " + switch_user + "@" + switch_ip + " 'show configuration | display json' > " + conf_switch_file)
            interface_vlans = juniper_config_parser(conf_switch_file)['InterfaceVlan']
            actual_vlans=[]
            for port in bare_metal_guest_ports:
                if port in interface_vlans.keys():
                    actual_vlans.append(interface_vlans[port]['members'])
            if len(actual_vlans)==2:
                to_stop=True
        self.assertEqual(actual_vlans,[[baremetal_vlan_id],[baremetal_vlan_id]], 'Failed: baremetal ports are set to incorrect vlans:\n'+str(actual_vlans))


    # def create_and_delete_bm_guest(self):
    #     create_command='openstack server create --flavor baremetal --image overcloud -full --key default --nic net-id=<ID> t1'





if __name__ == '__main__':
    unittest.main()
