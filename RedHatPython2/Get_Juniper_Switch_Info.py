from Common import *

# QE Setup #
setup_parameters={
    'baremetal_guest_ports':['xe-0/0/6', 'xe-0/0/7'],
    'switch_type':'juniper_physical_sw',
    'switch_ip':'10.10.191.221',
    'switch_user':'ansible',
    'switch_password':'N3tAutomation!',
    'tenant_nets':['tenant-net','tenant-net2'],
    'setup':'QE_Setup'
}
vlans=get_juniper_sw_get_port_vlan(
    setup_parameters['switch_ip'],
    setup_parameters['switch_user'],
    setup_parameters['switch_password'],
    setup_parameters['baremetal_guest_ports'])


for k in vlans.keys():
    print k,' --> ', vlans[k]


# print run_command_on_switch(
#     setup_parameters['switch_ip'],
#     setup_parameters['switch_user'],
#     setup_parameters['switch_password'],
#     #command='edit;delete interfaces xe-0/0/7 unit 0 family ethernet-switching vlan members 1202;commit')
#     command='edit;set interfaces xe-0/0/7 unit 0 family ethernet-switching vlan members 1202;commit')