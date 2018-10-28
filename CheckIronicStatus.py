from Common import *

### Get controllers IPs ###
spec_print(["Make sure you are sourced to Undercloud","Run source /home/stack/stackrc"])
#print exec_command_line_command('source /home/stack/overcloudrc')
controllers = exec_command_line_command('openstack server list --name controller -f json')['JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]

# # Check Ironoic on Undercloud#
# for ip in controller_ips:
#     print ip
#     ssh_object = SSH(ip,user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
#     ssh_object.ssh_connect_key()
#     ironics=ssh_object.ssh_command('sudo docker ps | grep -i ironic')
#     for k in ironics.keys():
#         print k, '-->', ironics[k]
#     ssh_object.ssh_close()


# Check Ironic on Overcloud + ERRORs in logs #
catalog_output=exec_command_line_command('openstack catalog show ironic -f json')
for k in catalog_output['JsonOutput'].keys():
    print k, '-->', catalog_output['JsonOutput'][k]
ironic_status= "for i in ironic_pxe_http ironic_pxe_tftp ironic_neutron_agent ironic_conductor ironic_api; do sudo docker ps|grep $i; done"
ironic_errors='grep -i error /var/log/containers/ironic *'
commands_to_execute=[ironic_status,ironic_errors]
for ip in controller_ips:
    print '---',ip,'---'
    ssh_object = SSH(ip,user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
    ssh_object.ssh_connect_key()
    for com in commands_to_execute:
        print '-->',com
        com_output=ssh_object.ssh_command(ironic_status)
        for k in com_output.keys():
            print k, '-->', com_output[k]
    ssh_object.ssh_close()
