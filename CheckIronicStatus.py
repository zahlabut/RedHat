from Common import *

print "Make sure you are sourced to Overcloud"
print "Run source /home/stack/overcloudrc"
print exec_command_line_command('source /home/stack/overcloudrc')
controllers = exec_command_line_command('openstack server list -f json --name controller')['JsonOutput']

controller_ips = [item['JsonOutput']['Networks'].split('=')[-1] for item in controllers]
print controller_ips


