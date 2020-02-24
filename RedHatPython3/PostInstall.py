### To delete all related to openstack project purge --project admin ###



from Common import *
source_command='source /home/stack/overcloudrc;'
source_undercloud='source /home/stack/stackrc;'
virt_setup_overcloud_images='/home/stack/overcloud_images'

# Is Virt or Baremetal setup check
nodes = exec_command_line_command(source_undercloud+'openstack server list -f json')['JsonOutput']
nodes_names = [item['name'].lower() for item in nodes]
if 'ceph' in str(nodes_names):
    setup_type='baremetal'
else:
    setup_type='virt'
print (setup_type)
sys.exit(1)


existing_baremetal_nodes=[item['name'] for item in exec_command_line_command(source_command+'openstack baremetal node list -f json')['JsonOutput']]
print('BareMetals --> ',existing_baremetal_nodes)
existing_networks=[item['name'] for item in exec_command_line_command(source_command+'openstack network list -f json')['JsonOutput']]
print('Networks --> ',existing_networks)
existing_subnets=[item['name'] for item in exec_command_line_command(source_command+'openstack subnet list -f json')['JsonOutput']]
print('Subnets --> ',existing_subnets)
existing_routers=[item['name'] for item in exec_command_line_command(source_command+'openstack router list -f json')['JsonOutput']]
print('Routers --> ',existing_routers)
existing_images=[item['name'] for item in exec_command_line_command(source_command+'openstack image list -f json')['JsonOutput']]
print('images --> ',existing_images)
existing_flavors=[item['name'] for item in exec_command_line_command(source_command+'openstack flavor list -f json')['JsonOutput']]
print('Flavors --> ',existing_flavors)
existing_aggregates=[item['name'] for item in exec_command_line_command(source_command+'openstack aggregate list -f json')['JsonOutput']]
print('Aggregates --> ',existing_aggregates)
default_security_group_id=[item['id'] for item in exec_command_line_command(source_command+'openstack security group list -f json')['JsonOutput'] if len(item['project'])!=0][0]
print('Security Group ID --> ',default_security_group_id)
existing_key_pairs=[item['name'] for item in exec_command_line_command(source_command+'openstack keypair list -f json')['JsonOutput']]
print('Keypairs --> ',existing_key_pairs)
existing_users=[item['name'] for item in exec_command_line_command(source_command+'openstack user list -f json')['JsonOutput']]
print('Users --> ',existing_users)
existing_projects=[item['name'] for item in exec_command_line_command(source_command+'openstack project list -f json')['JsonOutput']]
print('Projects --> ',existing_projects)


def empty_file_content(log_file_name):
    f = open(log_file_name, 'w')
    f.write('')
    f.close()

def append_to_file(log_file, msg):
    log_file = open(log_file, 'a')
    log_file.write(msg)

all_errors=[]
# Import BM nodes #
if len(existing_baremetal_nodes)!=2:
    import_bm_nodes_command=source_command+'openstack baremetal create bm_guests_env.yaml'
    result=exec_command_line_command(import_bm_nodes_command)
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create baremetal network #
if 'baremetal' not in existing_networks:
    result=exec_command_line_command(source_command+'openstack network create --provider-network-type vlan --provider-physical-network baremetal baremetal')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create dummy network #
if 'dummy' not in existing_networks:
    result=exec_command_line_command(source_command+'openstack network create --provider-network-type flat --provider-physical-network baremetal dummy')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create baremetal-subnet subnet #
if 'baremetal-subnet' not in existing_subnets:
    result=exec_command_line_command(source_command+'openstack subnet create --network baremetal --subnet-range 192.168.25.0/24 --ip-version 4 --allocation-pool start=192.168.25.30,end=192.168.25.50 --dhcp baremetal-subnet')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create dummy-subnet subnet #
if 'dummy-subnet' not in existing_subnets:
    result=exec_command_line_command(source_command+'openstack subnet create --network dummy --subnet-range 192.168.24.0/24 --ip-version 4 --gateway 192.168.24.111 --allocation-pool start=192.168.24.30,end=192.168.24.50 --no-dhcp dummy-subnet')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create ProvisionRouter router #
if 'ProvisionRouter'.lower() not in existing_routers:
    commands=['openstack router create ProvisionRouter',
              'openstack router add subnet ProvisionRouter baremetal-subnet',
              'openstack router add subnet ProvisionRouter dummy-subnet']
    for com in commands:
        result=exec_command_line_command(source_command+com)
        if result['ReturnCode'] != 0:
            all_errors.append(result['CommandOutput'])

# Create tenant-net networks and subnets #
tenant_networks=[
    ('tenant-net','tenant-subnet','192.168.3'),
    ('tenant-net2','tenant-subnet2','192.168.30'),
    ('tenant-net3','tenant-subnet3','192.168.4'),
    ('tenant-net4','tenant-subnet4','192.168.40'),
    ('tenant-net5','tenant-subnet5','192.168.5'),
    ('tenant-net6','tenant-subnet6','192.168.50')]
for item in tenant_networks:
    if item[0] not in existing_networks:
        result=exec_command_line_command(source_command+'openstack network create --provider-network-type vlan '+item[0])
        if result['ReturnCode']!=0:
            all_errors.append(result['CommandOutput'])
    if item[1] not in existing_subnets:
        result=exec_command_line_command(source_command+'openstack subnet create --network '+item[0]+' --subnet-range '+item[2]+'.0/24 --allocation-pool start='+item[2]+'.10,end='+item[2]+'.20 '+item[1])
        if result['ReturnCode']!=0:
            all_errors.append(result['CommandOutput'])


# Create external network #
if 'tenant-net' not in existing_networks:
    result=exec_command_line_command(source_command+'openstack network create --share --provider-network-type flat --provider-physical-network datacentre --external external')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])



# Create external-subnet subnet #
if 'external-subnet' not in existing_subnets:
    result=exec_command_line_command(source_command+'openstack subnet create --network external --subnet-range 10.9.92.16/28 --gateway 10.9.92.30 --no-dhcp --allocation-pool start=10.9.92.17,end=10.9.92.22 external-subnet')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create external router #
if 'external' not in existing_routers:
    result=exec_command_line_command(source_command+'openstack router create external')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack router add subnet external tenant-subnet')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack router set --external-gateway external external')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create external2 router #
if 'external2' not in existing_routers:
    result=exec_command_line_command(source_command+'openstack router create external2')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack router add subnet external2 tenant-subnet2')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack router set --external-gateway external external2')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create baremetal flavor #
if 'baremetal' not in existing_flavors:
    result=exec_command_line_command(source_command+'openstack flavor create --id auto --ram 4096 --vcpus 2 --disk 10 --property baremetal=true --property resources:VCPU=0 --property resources:MEMORY_MB=0 --property resources:DISK_GB=0 --property resources:CUSTOM_BAREMETAL=1 --public baremetal')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create small flavor #
if 'small' not in existing_flavors:
    result=exec_command_line_command(source_command+'openstack flavor create --id auto --ram 2048 --vcpus 2 --disk 10 --public small')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create bm-deploy-kernel image #
if 'bm-deploy-kernel' not in existing_images:
    result=exec_command_line_command(source_command+'openstack image create --container-format aki  --disk-format aki --public --file /home/stack/ironic-python-agent.kernel bm-deploy-kernel -f json')
    kernel_id=result['JsonOutput']['id']
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
else:
    kernel_id=exec_command_line_command(source_command+'openstack image show bm-deploy-kernel -c id -f json')['JsonOutput']['id']

# Create bm-deploy-ramdisk image #
if 'bm-deploy-ramdisk' not in existing_images:
    result=exec_command_line_command(source_command+'openstack image create --container-format ari  --disk-format ari --public  --file /home/stack/ironic-python-agent.initramfs bm-deploy-ramdisk -f json')
    ram_id=result['JsonOutput']['id']
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
else:
    ram_id=exec_command_line_command(source_command+'openstack image show bm-deploy-ramdisk -c id -f json')['JsonOutput']['id']

if kernel_id or ram_id not in str(exec_command_line_command(source_command+'openstack baremetal node show ironic-0 -f json')['JsonOutput']):
    # Associate image per BM Guest #
    result=exec_command_line_command(source_command+'openstack baremetal node set ironic-0 --driver-info deploy_kernel='+kernel_id+' --driver-info deploy_ramdisk='+ram_id)
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

if kernel_id or ram_id not in str(exec_command_line_command(source_command + 'openstack baremetal node show ironic-1 -f json')['JsonOutput']):
    result=exec_command_line_command(source_command+'openstack baremetal node set ironic-1 --driver-info deploy_kernel='+kernel_id+' --driver-info deploy_ramdisk='+ram_id)
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create image from qcow2 file #
if 'overcloud-full.vmlinuz' not in existing_images:
    result=exec_command_line_command(source_command+'openstack image create --file /home/stack/overcloud-full.vmlinuz --public --container-format aki --disk-format aki -f value -c id  overcloud-full.vmlinuz')
    id1=result['CommandOutput'].strip()
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

if 'overcloud-full.initrd' not in existing_images:
    result=exec_command_line_command(source_command+'openstack image create --file /home/stack/overcloud-full.initrd --public --container-format ari --disk-format ari -f value -c id overcloud-full.initrd')
    id2=result['CommandOutput'].strip()
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

if 'overcloud-full' not in existing_images:
    result=exec_command_line_command(source_command+'openstack image create --file /home/stack/overcloud-full.qcow2 --public --container-format bare --disk-format qcow2 --property kernel_id='+id1+' --property ramdisk_id='+id2+' overcloud-full')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

if 'baremetal-hosts' not in existing_aggregates:
    result=exec_command_line_command(source_command+'openstack aggregate create --property baremetal=true baremetal-hosts')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack aggregate add host baremetal-hosts overcloud-controller-0.localdomain')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack aggregate add host baremetal-hosts overcloud-controller-1.localdomain')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'openstack aggregate add host baremetal-hosts overcloud-controller-2.localdomain')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

if 'virtual-hosts' not in existing_aggregates:
    result=exec_command_line_command(source_command+'openstack aggregate create --property baremetal=false virtual-hosts')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])
    result=exec_command_line_command(source_command+'for vm_host in $(openstack hypervisor list -f value -c "Hypervisor Hostname" | grep compute); do openstack aggregate add host virtual-hosts $vm_host ; done')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Add ICMP and SSH to the Default security group #
if '22' not in str(exec_command_line_command(source_command+'openstack security group show '+default_security_group_id+' -f json')['JsonOutput']):
    result=exec_command_line_command(source_command+'openstack security group rule create --dst-port 22 '+default_security_group_id)
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

if 'icmp' not in str(exec_command_line_command(source_command+'openstack security group show '+default_security_group_id+' -f json')['JsonOutput']):
    result=exec_command_line_command(source_command+'openstack security group rule create --protocol icmp '+default_security_group_id)
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])

# Create admin pair #
if 'default' not in existing_key_pairs:
    result=exec_command_line_command(source_command+'openstack keypair create --public-key /home/stack/.ssh/id_rsa.pub default')
    if result['ReturnCode']!=0:
        all_errors.append(result['CommandOutput'])


# Create new Overcloud users
users=[
    {'name':'new-user','project':'new-project','project_info':'new_project','user_password':'PASSWORD','rc_file':'userrc'},
    {'name':'new-user1','project':'new-project1','project_info':'new_project_1','user_password':'PASSWORD1','rc_file':'userrc1'}
]
for user in users:
    if user['project'] not in existing_projects:
        result=exec_command_line_command(source_command+
                                         "openstack project create --description "+user['project_info']+" "+user['project']+" --domain default")
        if result['ReturnCode']!=0:
            all_errors.append(result['CommandOutput'])
    if user['name'] not in existing_users:
        commands=["openstack user create --project "+user['project']+" --password "+user['user_password']+" "+user['name'],
                  "openstack role add --user "+user['name']+" --project "+user['project']+" admin",
                  "openstack network set --share tenant-net"
                  ]
        for com in commands:
            result=exec_command_line_command(source_command+com)
        overcloudrc_content=open('/home/stack/overcloudrc','r').readlines()
        empty_file_content('/home/stack/'+user['rc_file'])
        for line in overcloudrc_content:
            if "OS_USERNAME" in line:
                line='export OS_USERNAME='+user['name']+'\n'
            if "OS_PASSWORD" in line:
                line='export OS_PASSWORD='+user['user_password']+'\n'
            if "OS_PROJECT_NAME" in line:
                line='export OS_PROJECT_NAME='+user['project']+'\n'
            append_to_file('/home/stack/'+user['rc_file'],line)

    if 'default' not in exec_command_line_command('source /home/stack/'+user['rc_file']+';openstack keypair list') ['CommandOutput']:
        keypair_create="source /home/stack/"+user['rc_file']+";openstack keypair create --public-key ~/.ssh/id_rsa.pub default"
        exec_command_line_command(keypair_create)






if len(all_errors)!=0:
    print('\n\n\nFailed commands has been detected!!!')
    for item in list(set(all_errors)):
        print(item)
        print('-'*100)
else:
    print("SUCCESS")
