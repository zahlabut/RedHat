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
        result = subprocess.check_output(command, shell=True)
        json_output = None
        try:
            json_output = json.loads(result.lower())
        except:
            pass
        return {'ReturnCode': 0, 'CommandOutput': result, 'JsonOutput': json_output}
    except subprocess.CalledProcessError as e:
        print e
        return {'ReturnCode': e.returncode, 'CommandOutput': 'Failed to execute: \n'+command+'with:\n'+str(e)}



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

