from Common import *

### Get controllers IPs ###
spec_print(["Make sure you are sourced to Undercloud","Run source /home/stack/stackrc"])
print exec_command_line_command('source /home/stack/overcloudrc')
controllers = exec_command_line_command('openstack server list --name controller -f json')['JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]


### Check The Ironic Status ###
# for ip in controller_ips:
#     print 'ssh heat-admin@'+ip+'; docker ps | grep -i ironic; exit'
#     print exec_command_line_command('ssh heat-admin@'+ip+'; docker ps | grep -i ironic; exit')['CommandOutput']


for ip in controller_ips:
    ssh_object = SSH(ip,'heat-admin',key_path='/home/stack/.ssh/id_rsa')
    ssh_object.ssh_connect_key()
    ssh_object.ssh_command('date')
    ssh_object.ssh_close()


 #ssh heat-admin@192.168.24.9 -i /home/stack/.ssh/id_rsa
