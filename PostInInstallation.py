from Common import *
source_command='source /home/stack/overcloudrc;'

existing_baremetal_nodes=[item['name'] for item in exec_command_line_command(source_command+'openstack baremetal node list -f json')['JsonOutput']]
print existing_baremetal_nodes
existing_networks=[item['name'] for item in exec_command_line_command(source_command+'openstack network list -f json')['JsonOutput']]
print existing_networks
existing_subnets=[item['name'] for item in exec_command_line_command(source_command+'openstack subnet list -f json')['JsonOutput']]
print existing_subnets
existing_routers=[item['name'] for item in exec_command_line_command(source_command+'openstack router list -f json')['JsonOutput']]
print existing_routers
existing_images=[item['name'] for item in exec_command_line_command(source_command+'openstack image list -f json')['JsonOutput']]
print existing_images
existing_flavors=[item['name'] for item in exec_command_line_command(source_command+'openstack flavor list -f json')['JsonOutput']]
print existing_flavors


# Import BM nodes #
if len(existing_baremetal_nodes)!=2:
    import_bm_nodes_command='source /home/stack/overcloudrc; openstack baremetal create bm_guests_env.yaml'
    print exec_command_line_command(import_bm_nodes_command)

# Create baremetal network #
if 'baremetal' not in existing_networks:
    exec_command_line_command(source_command+'openstack network create --provider-network-type vlan --provider-physical-network baremetal baremetal')

# Create dummy network #
if 'dummy' not in existing_networks:
    exec_command_line_command(source_command+'openstack network create --provider-network-type vlan --provider-physical-network baremetal dummy')

# Create baremetal-subnet subnet #
if 'baremetal-subnet' not in existing_subnets:
    exec_command_line_command(source_command+'openstack subnet create --network baremetal --subnet-range 192.168.25.0/24 --ip-version 4 --allocation-pool start=192.168.25.30,end=192.168.25.50 --dhcp baremetal-subnet')

# Create dummy-subnet subnet #
if 'dummy-subnet' not in existing_subnets:
    exec_command_line_command(source_command+'openstack subnet create --network dummy --subnet-range 192.168.24.0/24 --ip-version 4 --gateway 192.168.24.111 --allocation-pool start=192.168.24.30,end=192.168.24.50 --no-dhcp dummy-subnet')

# Create ProvisionRouter router #
if 'ProvisionRouter' not in existing_routers:
    commands=['openstack router create ProvisionRouter',
              'openstack router add subnet ProvisionRouter baremetal-subnet',
              'openstack router add subnet ProvisionRouter dummy-subnet']
    for com in commands:
        exec_command_line_command(source_command+com)





