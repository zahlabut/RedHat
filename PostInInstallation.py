from Common import *

# Import BM nodes #
check_if_bm_exists='source /home/stack/overcloudrc; openstack baremetal node list -f json'
result=exec_command_line_command(check_if_bm_exists)
print result

#import_bm_nodes_command='source /home/stack/overcloudrc; openstack baremetal create bm_guests_env.yaml'
#print exec_command_line_command(import_bm_nodes_command)