from Common import *
import unittest

### Parameters ###
overclud_user='heat-admin'
overcloud_ssh_key='/home/stack/.ssh/id_rsa'

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
            spec_print([ip])
            ssh_object = SSH(ip,user=overclud_user,key_path=overcloud_ssh_key)
            ssh_object.ssh_connect_key()
            for doc in ironic_dockers:
                output=ssh_object.ssh_command('sudo docker ps | grep '+doc)['Stdout']
                print output
                ssh_object.ssh_close()
                self.assertNotIn('unhealthy', output, 'Failed: '+ip+' '+doc + ' status is unhealthy')




        #ironic_errors='grep -i error /var/log/containers/ironic/*'


    # # Check Network Ansible (neutron_api) + ERRORs in logs
    # spec_print(['Check Network Ansible (neutron_api) + ERRORs in logs'])
    # net_ans_status= "sudo docker ps | grep -i neutron_api"
    # net_ans_errors='grep -i error /var/log/containers/neutron/server.log*'
    # expected_message='cat /var/log/containers/neutron/server.log* | grep -i networking_ansible.config; ' \
    #                  'zcat /var/log/containers/neutron/server.log* | grep -i networking_ansible.config'
    # commands_to_execute=[net_ans_status,net_ans_errors,expected_message]
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
    # # Check Ceph Status + ERRORs in logs #
    # spec_print(['Check Ceph Status + ERRORs in logs'])
    # ceph_status= "source /home/stack/overcloudrc; cinder service-list | grep ceph"
    # print exec_command_line_command(ceph_status)['CommandOutput']
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
