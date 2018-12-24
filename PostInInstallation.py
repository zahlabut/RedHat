from Common import *

# Import BM nodes #
import_bm_nodes_command='source /home/stack/overcloudrc; openstack baremetal create bm_guests_env.yaml'
print exec_command_line_command(import_bm_nodes_command)