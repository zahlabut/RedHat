from Common import *
import ipaddr
source_command='source /home/stack/overcloudrc;'

all_errors=[]


existing_networks=[item['name'] for item in exec_command_line_command(source_command+'openstack network list -f json')['JsonOutput']]
print 'Networks --> ',existing_networks
existing_subnets=[item['name'] for item in exec_command_line_command(source_command+'openstack subnet list -f json')['JsonOutput']]
print 'Subnets --> ',existing_subnets

number_of_networks_to_create=10
start_ip = ipaddr.IPAddress('192.168.100.1')
networks_to_create=[]
for i in range(number_of_networks_to_create):
    networks_to_create.append(('tenant-net-'+str(i),'tenant-subnet-'+str(i),start_ip+i))


for item in networks_to_create:
    if item[0] not in existing_networks:
        result=exec_command_line_command(source_command+'openstack network create '+item[0])
        if result['ReturnCode']!=0:
            all_errors.append(result['CommandOutput'])
    if item[1] not in existing_subnets:
        result=exec_command_line_command(source_command+'openstack subnet create --network '+item[0]+' --subnet-range '+item[2]+'.0/24 --allocation-pool start='+item[2]+'.10,end='+item[2]+'.20 '+item[1])
        if result['ReturnCode']!=0:
            all_errors.append(result['CommandOutput'])


if len(all_errors)!=0:
    print '\n\n\nFailed commands has been detected!!!'
    for item in list(set(all_errors)):
        print item
        print '-'*100
else:
    print "SUCCESS"


