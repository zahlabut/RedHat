import os
import paramiko
import time
import subprocess
import json

class SSH():
    def __init__(self, host, user, password='', key_path=''):
        self.host=host
        self.user=user
        self.password=password
        self.key_path=key_path

    def ssh_connect_password(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.user, password=self.password)
            return {'Status':True}
        except Exception, e:
            return {'Status':False,'Exception':e}

    def ssh_connect_key(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.user, key_filename=self.key_path)
            return {'Status':True}
        except Exception, e:
            return {'Status':False,'Exception':e}

    def ssh_command(self, command):
        stdin,stdout,stderr=self.client.exec_command(command)
        #stdin.close()
        self.output=''
        self.stderr=''
        for line in stdout.read().splitlines():
            self.output+=line+'\n'
        for line in stderr.read().splitlines():
            self.stderr+=line+'\n'
        return {'Stdout':self.output, 'Stderr':self.stderr}

    def ssh_command_only(self, command):
        self.stdin,self.stdout,self.stderr=self.client.exec_command(command)
        return {'Stdout':self.stdout.read(),'Stderr':self.stderr.read()}

    def scp_upload(self, src_abs_path, dst_abs_path):
        try:
            file_size=os.path.getsize(src_abs_path)
            ftp = self.client.open_sftp()
            t1=time.time()
            ftp.put(src_abs_path,dst_abs_path)
            t2=time.time()
            return {'Status':True,'AverageBW':file_size/(t2-t1),'ExecutionTime':t2-t1}
        except  Exception, e:
            return {'Status':False,'Exception':e}

    def scp_download(self,remote_abs_path,local_abs_path):
        try:
            ftp=self.client.open_sftp()
            t1 = time.time()
            ftp.get(remote_abs_path, local_abs_path)
            t2 = time.time()
            file_size=os.path.getsize(local_abs_path)
            return {'Status': True,'AverageBW':file_size/(t2-t1),'ExecutionTime':t2-t1}
        except  Exception, e:
            return {'Status': False, 'Exception': e}

    def ssh_close(self):
        self.client.close()

def exec_command_line_command(command):
    try:
        command_as_list = command.split(' ')
        command_as_list = [item.replace(' ', '') for item in command_as_list if item != '']
        result = subprocess.check_output(command, stdin=True, stderr=subprocess.STDOUT, shell=True)
        json_output = None
        try:
            json_output = json.loads(result.lower())
        except:
            pass
        return {'ReturnCode': 0, 'CommandOutput': result, 'JsonOutput': json_output}
    except subprocess.CalledProcessError as e:
        print e
        return {'ReturnCode': e.returncode, 'CommandOutput': 'Failed to execute: \n'+command+'with:\n'+str(e)}



def collect_log_paths(log_root_path):
    logs=[]
    for root, dirs, files in os.walk(log_root_path):
        for name in files:
            if '.log' in name:
                file_abs_path=os.path.join(os.path.abspath(root), name)
                if os.path.getsize(file_abs_path)!=0 and 'LogTool' not in file_abs_path:
                    to_add = True
                    for item in not_supported_logs:
                        if item in file_abs_path:
                            to_add = False
                    if to_add==True:
                        logs.append(file_abs_path)
    logs=list(set(logs))
    return logs

def spec_print(string_list):
    len_list=[]
    for item in string_list:
        len_list.append(len('### '+item.strip()+' ###'))
    max_len=max(len_list)
    print ''
    print"#"*max_len
    for item in string_list:
        print "### "+item.strip()+" "*(max_len-len("### "+item.strip())-4)+" ###"
    print"#"*max_len+'\n'

def juniper_config_parser(path_to_config_json):
    json_output=json.loads(open(path_to_config_json,'r').read().lower())
    interfaces=json_output['configuration']['interfaces']['interface']
    int_vlan_dic={}
    for inter in interfaces:
        inter_vlans=None
        name=inter['name']
        try:
            inter_vlans=inter['unit'][0]['family']['ethernet-switching']['vlan']
        except Exception, e:
            print e
        int_vlan_dic[name]=inter_vlans
    vlans=json_output['configuration']['vlans']
    return {'Interfaces':interfaces,'Vlans':vlans, 'InterfaceVlan':int_vlan_dic}

def get_switch_conf_as_json(ip,user,password,sw_type=None):
    #types: juniper_physical_sw juniper_emulator_sw
    if sw_type=='juniper_physical_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
        json_output=json.loads(str(out))
        vlans=json_output['configuration']['vlans']
        interfaces=json_output['configuration']['interfaces']['interface']
        int_vlan_dic={}
        for inter in interfaces:
            inter_vlans=None
            name=inter['name']
            try:
                inter_vlans=inter['unit'][0]['family']['ethernet-switching']['vlan']
            except Exception, e:
                print e
            int_vlan_dic[name]=inter_vlans
        return {'Interfaces':interfaces,'Vlans':vlans, 'InterfaceVlan':int_vlan_dic}

    if sw_type=='juniper_emulator_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
        json_output = json.loads(str(out))
        vlans = json_output['configuration'][0]['vlans']
        interfaces = json_output['configuration'][0]['interfaces'][0]['interface']
        int_vlan_dic = {}
        for inter in interfaces:
            inter_vlans = None
            name = inter['name']['data']
            try:
                inter_vlans = inter['unit'][0]['family'][0]['ethernet-switching'][0]['vlan'][0]
            except Exception, e:
                print e
            int_vlan_dic[name] = inter_vlans
    return {'Interfaces': interfaces,'Vlans':vlans,'InterfaceVlan':int_vlan_dic}

def get_switch_configuration_file(ip,user,password,sw_type=None):
    #types: juniper_physical_sw juniper_emulator_sw
    if sw_type=='juniper_physical_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
    if sw_type=='juniper_emulator_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
    return out

def get_juniper_sw_get_port_vlan(ip, user, password, ports):
    ssh_object = SSH(ip, user, password)
    ssh_object.ssh_connect_password()
    result_dic={}
    for port in ports:
        try:
            command='show configuration interfaces '+port
            out=ssh_object.ssh_command_only(command)['Stdout']
            vlans=[line.split('members')[1].strip(';').replace('[','').replace(']','') for line in out.split('\n') if 'members' in line]
            vlans=[item for item in vlans[0].split(' ') if item!='']
            result_dic[port]=vlans
        except:
            result_dic[port]=None
    ssh_object.ssh_close()
    return result_dic




