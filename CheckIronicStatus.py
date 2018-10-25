from Common import *

print "Make sure you are sourced to Overcloud"
print "Run source /home/stack/overcloudrc"
exec_command_line_command('source /home/stack/overcloudrc')
exec_command_line_command('openstack server list')

