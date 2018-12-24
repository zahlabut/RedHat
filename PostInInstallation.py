from Common import *

ironic_names=['ironic-0','ironic-1'] #As hardcoded in bm_guests_env.yaml file

# Import BM nodes #
to_import=[]
check_if_bm_exists='source /home/stack/overcloudrc; openstack baremetal node list -f json'
result=exec_command_line_command(check_if_bm_exists)
if result['JsonOutput']!=None:
    names=[]
    for item in result['JsonOutput']:
        if item['name'] in ironic_names:
            to_import.append(False)
        else:
            to_import.append(True)
    print to_import
if True in to_import:
    import_bm_nodes_command='source /home/stack/overcloudrc; openstack baremetal create bm_guests_env.yaml'
    print exec_command_line_command(import_bm_nodes_command)