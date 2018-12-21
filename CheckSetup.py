from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'
bare_metal_guest_ports=['006','007']


### Get controllers IPs ###
controllers = exec_command_line_command('source /home/stack/stackrc;openstack server list --name controller -f json')[
    'JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]

### Get Ceph IPs ###
cephs = exec_command_line_command('source /home/stack/stackrc;openstack server list --name cephstorage -f json')[
    'JsonOutput']
cephs_ips = [item['networks'].split('=')[-1] for item in cephs]

class AnsibleNetworkingRegressionTests(unittest.TestCase):
    # Check Ironic on Overcloud + ERRORs in logs #
    def test_ironic_in_catalog(self):
        #spec_print(['Check Ironic on Overcloud + ERRORs in logs'])
        catalog_output=exec_command_line_command('source /home/stack/overcloudrc;openstack catalog show ironic -f json')
        self.assertEqual(catalog_output['JsonOutput']['name'], 'ironic','Failed: ironic was not found in catalog output')

    def test_ironic_dockers_status(self):
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

    def test_errors_in_ironic_logs(self):
        command='sudo grep -R ERROR /var/log/containers/ironic/*'
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            output = ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

    def test_dockers_neutron_api_status(self):
        for ip in controller_ips:
            ssh_object = SSH(ip,user=overclud_user,key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            command='sudo docker ps | grep -i neutron_api'
            output=ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('unhealthy', output, 'Failed: '+ip+' '+'neutron_api status is unhealthy')
            self.assertIn('neutron_api', output, 'Failed: neutron_api is not running')

    def test_errors_in_neutron_api(self):
        command='grep -i error /var/log/containers/neutron/server.log*'
        for ip in controller_ips:
            ssh_object = SSH(ip, user=overclud_user, key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            output = ssh_object.ssh_command(command)['Stdout']
            ssh_object.ssh_close()
            self.assertNotIn('ERROR', output, 'Failed: ' + ip + ' ERROR detected in log\n'+output)

    def test_net_ansible_indication_msg_in_log(self):
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



    def test_check_ceph_status(self):
        ceph_status= "source /home/stack/overcloudrc; cinder service-list | grep ceph"
        out = exec_command_line_command(ceph_status)['CommandOutput']
        self.assertIn('ceph',out,'Failed: ceph is not running')


        # ceph_health_command='ceph health'
        # commands_to_execute=[ceph_health_command]
        # for ip in controller_ips:
        #     spec_print([ip])
        #     ssh_object = SSH(ip,user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
        #     ssh_object.ssh_connect_key()
        #     for com in commands_to_execute:
        #         print '-->',com
        #         com_output=ssh_object.ssh_command(com)
        #         for k in com_output.keys():
        #             print k, '-->', com_output[k]
        #     ssh_object.ssh_close()
    #
    #
    #
    # ### Check Switch Vlans ###
    # conf_data_file='sw_conf.json'
    # exec_command_line_command("sshpass -p N3tAutomation! ssh ansible@10.9.95.25 'show configuration | display json' > "+conf_data_file)
    # interface_vlan=juniper_config_parser(conf_data_file)['InterfaceVlan']
    # for k in interface_vlan.keys():
    #     print k,'-->',interface_vlan[k]


if __name__ == '__main__':
    unittest.main()
