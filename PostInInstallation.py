from Common import *


existing_baremetal_nodes=[item['name'] for item in exec_command_line_command('source /home/stack/overcloudrc; openstack baremetal node list -f json')['JsonOutput']]
print existing_baremetal_nodes
existing_networks=[item['name'] for item in exec_command_line_command('source /home/stack/overcloudrc; openstack network list -f json')['JsonOutput']]
print existing_networks
existing_subnets=[item['name'] for item in exec_command_line_command('source /home/stack/overcloudrc; openstack subnet list -f json')['JsonOutput']]
print existing_subnets
existing_routers=[item['name'] for item in exec_command_line_command('source /home/stack/overcloudrc; openstack router list -f json')['JsonOutput']]
print existing_routers
existing_images=[item['name'] for item in exec_command_line_command('source /home/stack/overcloudrc; openstack image list -f json')['JsonOutput']]
print existing_images
existing_flavors=[item['name'] for item in exec_command_line_command('source /home/stack/overcloudrc; openstack flavor list -f json')['JsonOutput']]
print existing_flavors


# Import BM nodes #
if len(existing_baremetal_nodes)!=2:
    import_bm_nodes_command='source /home/stack/overcloudrc; openstack baremetal create bm_guests_env.yaml'
    print exec_command_line_command(import_bm_nodes_command)





# Create baremetal and dummy networks, subnet and connect to router
