from Common import *

spec_print(["Make sure you are sourced to Undercloud","Run source /home/stack/stackrc"])
print exec_command_line_command('source /home/stack/overcloudrc')
controllers = exec_command_line_command('openstack server list --name controller -f json')['JsonOutput']
controller_ips = [item['networks'].split('=')[-1] for item in controllers]
print controller_ips


