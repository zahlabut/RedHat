### To delete all related to openstack project purge --project admin ###

from Common import *
source_command='source /home/stack/overcloudrc;'

existing_baremetal_nodes=[item['name'] for item in exec_command_line_command(source_command+'openstack baremetal node list -f json')['JsonOutput']]
print 'BareMetals --> ',existing_baremetal_nodes
existing_networks=[item['name'] for item in exec_command_line_command(source_command+'openstack network list -f json')['JsonOutput']]
print 'Networks --> ',existing_networks
existing_subnets=[item['name'] for item in exec_command_line_command(source_command+'openstack subnet list -f json')['JsonOutput']]
print 'Subnets --> ',existing_subnets
existing_routers=[item['name'] for item in exec_command_line_command(source_command+'openstack router list -f json')['JsonOutput']]
print 'Routers --> ',existing_routers
existing_images=[item['name'] for item in exec_command_line_command(source_command+'openstack image list -f json')['JsonOutput']]
print 'images --> ',existing_images
existing_flavors=[item['name'] for item in exec_command_line_command(source_command+'openstack flavor list -f json')['JsonOutput']]
print 'Flavors --> ',existing_flavors
existing_aggregates=[item['name'] for item in exec_command_line_command(source_command+'openstack aggregate list -f json')['JsonOutput']]
print existing_aggregates


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
if 'ProvisionRouter'.lower() not in existing_routers:
    commands=['openstack router create ProvisionRouter',
              'openstack router add subnet ProvisionRouter baremetal-subnet',
              'openstack router add subnet ProvisionRouter dummy-subnet']
    for com in commands:
        exec_command_line_command(source_command+com)

# Create tenant-net network #
if 'tenant-net' not in existing_networks:
    exec_command_line_command(source_command+'openstack network create tenant-net')

# Create tenant-net2 network #
if 'tenant-net' not in existing_networks:
    exec_command_line_command(source_command+'openstack network create tenant-net2')

# Create external network #
if 'tenant-net' not in existing_networks:
    exec_command_line_command(source_command+'openstack network create --share --provider-network-type flat --provider-physical-network datacentre --external external')

# Create tenant-subnet subnet #
if 'tenant-subnet' not in existing_subnets:
    exec_command_line_command(source_command+'openstack subnet create --network tenant-net --subnet-range 192.168.3.0/24 --allocation-pool start=192.168.3.10,end=192.168.3.20 tenant-subnet')

# Create tenant-subnet2 subnet #
if 'tenant-subnet2' not in existing_subnets:
    exec_command_line_command(source_command+'openstack subnet create --network tenant-net2 --subnet-range 192.168.30.0/24 --allocation-pool start=192.168.30.10,end=192.168.30.20 tenant-subnet2')

# Create external-subnet subnet #
if 'external-subnet' not in existing_subnets:
    exec_command_line_command(source_command+'openstack subnet create --network external --subnet-range 10.9.92.16/28 --gateway 10.9.92.30 --no-dhcp --allocation-pool start=10.9.92.17,end=10.9.92.22 external-subnet')

# Create external router #
if 'external' not in existing_routers:
    exec_command_line_command(source_command+'openstack router create external')
    exec_command_line_command(source_command+'openstack router add subnet external tenant-subnet')
    exec_command_line_command(source_command+'openstack router set --external-gateway external external')

# Create external2 router #
if 'external2' not in existing_routers:
    exec_command_line_command(source_command+'openstack router create external2')
    exec_command_line_command(source_command+'openstack router add subnet external2 tenant-subnet2')
    exec_command_line_command(source_command+'openstack router set --external-gateway external external2')

# Create baremetal flavor #
if 'baremetal' not in existing_flavors:
    exec_command_line_command(source_command+'openstack flavor create --id auto --ram 4096 --vcpus 2 --disk 10 --property baremetal=true --property resources:VCPU=0 --property resources:MEMORY_MB=0 --property resources:DISK_GB=0 --property resources:CUSTOM_BAREMETAL=1 --public baremetal')

# Create small flavor #
if 'small' not in existing_flavors:
    exec_command_line_command(source_command+'openstack flavor create --id auto --ram 2048 --vcpus 2 --disk 20 --public small')

# Create bm-deploy-kernel image #
if 'bm-deploy-kernel' not in existing_images:
    kernel_id=exec_command_line_command(source_command+'openstack image create --container-format aki  --disk-format aki --public --file /home/stack/ironic-python-agent.kernel bm-deploy-kernel -f json')['JsonOutput']['id']

# Create bm-deploy-ramdisk image #
if 'bm-deploy-ramdisk' not in existing_images:
    ram_id=exec_command_line_command(source_command+'openstack image create --container-format ari  --disk-format ari --public  --file /home/stack/ironic-python-agent.initramfs bm-deploy-ramdisk -f json')['JsonOutput']['id']
    # Associate image per BM Guest #
    exec_command_line_command(source_command+'openstack baremetal node set ironic-0 --driver-info deploy_kernel='+kernel_id+' --driver-info deploy_ramdisk='+ram_id)
    exec_command_line_command(source_command+'openstack baremetal node set ironic-1 --driver-info deploy_kernel='+kernel_id+' --driver-info deploy_ramdisk='+ram_id)


# Create image from qcow2 file #
if 'overcloud-full.vmlinuz' not in existing_images:
    id1=exec_command_line_command(source_command+'openstack image create --file overcloud-full.vmlinuz --public --container-format aki --disk-format aki -f value -c id  /home/stack/overcloud-full.vmlinuz')
if 'id overcloud-full.initrd' not in existing_images:
    id2=exec_command_line_command(source_command+'openstack image create --file overcloud-full.initrd --public --container-format ari --disk-format ari -f value -c id /home/stack/overcloud-full.initrd')
if 'overcloud-full' not in existing_images:
    exec_command_line_command(source_command+'openstack image create --file overcloud-full.qcow2 --public --container-format bare --disk-format qcow2 --property kernel_id='+id1+' --property ramdisk_id='+id2+' overcloud-full')
if 'baremetal-hosts' not in existing_aggregates:
    exec_command_line_command(source_command+'openstack aggregate create --property baremetal=true baremetal-hosts')
if 'virtual-hosts' not in existing_aggregates:
    exec_command_line_command(source_command+'openstack aggregate create --property baremetal=false virtual-hosts')
if 'compute' not in str(existing_aggregates):
    exec_command_line_command(source_command+'for vm_host in $(openstack hypervisor list -f value -c "Hypervisor Hostname" | grep compute); do openstack aggregate add host virtual-hosts $vm_host ; done')
if 'controller-0' not in str(existing_aggregates):
    exec_command_line_command(source_command+'openstack aggregate add host baremetal-hosts overcloud-controller-0.localdomain')
if 'controller-1' not in str(existing_aggregates):
    exec_command_line_command(source_command+'openstack aggregate add host baremetal-hosts overcloud-controller-1.localdomain')
if 'controller-2' not in str(existing_aggregates):
    exec_command_line_command(source_command+'openstack aggregate add host baremetal-hosts overcloud-controller-2.localdomain')

