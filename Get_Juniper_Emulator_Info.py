from Common import *

# Virtual Setup #
setup_parameters={
    'baremetal_guest_ports':['xe-0/0/7', 'xe-0/0/8'],
    'switch_type':'juniper_emulator_sw',
    'switch_ip':'172.16.0.81',
    'switch_user':'ansible',
    'switch_password':'Juniper',
    'tenant_nets':['tempest-shared'],
    'setup':'Virtual_Setup'
}
vlans=get_juniper_sw_get_port_vlan(
    setup_parameters['switch_ip'],
    setup_parameters['switch_user'],
    setup_parameters['switch_password'],
    setup_parameters['baremetal_guest_ports'])

print vlans

