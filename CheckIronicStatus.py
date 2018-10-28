from Common import *

### Get controllers IPs ###
spec_print(["Make sure you are sourced to Undercloud","Run source /home/stack/stackrc"])
print exec_command_line_command('source /home/stack/overcloudrc')
controllers = exec_command_line_command('openstack server list --name controller -f json')['JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]

for ip in controller_ips:
    print ip
    ssh_object = SSH(ip,user='heat-admin',key_path='/home/stack/.ssh/id_rsa')
    ssh_object.ssh_connect_key()
    ironics=ssh_object.ssh_command('sudo docker ps | grep -i ironic')
    #print ironics
    #print type(ironics)
    #print ironics.keys()
    for k in ironics.keys():
        print k#, '-->', ironics['k']
    # #for k in ironics.iteritems():
    # #    print k,'-->',ironics[k]
    # for i in str(ironics).split('\r'):
    #     print i
    ssh_object.ssh_close()
