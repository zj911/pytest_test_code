# install pytest 4.0.2
# uninstall pytest 4.6.2
import pytest
import re
from collections import OrderedDict
import paramiko
import time


class test_node_transcode():
    def __init__(self):
        # self.node_ip = '172.16.231.31'
        self.transcode_write_data = []
        self.ssh_port = 22
        self.ssh_name = 'root'
        self.ssh_password = "admin123"
    
    def option_mark(self, options):
        dict_mark = options.split(' ')
        dict_mark_info = {}
        for index, value in enumerate(dict_mark):
            if value.startswith('-'):
                dict_mark_info[value] = dict_mark[index+1]
        return dict_mark_info

    def get_connect(self, ssh_server):
        for i in range(1,10):
            ssh_flag = 1
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # client.connect(hostname=ssh_server, port=self.ssh_port, username=self.ssh_name, password=self.ssh_password,allow_agent=False, look_for_keys=False)
                client.connect(hostname=ssh_server, port=self.ssh_port, username=self.ssh_name, password=self.ssh_password)
            except Exception as e:
                print(e)
                ssh_flag = 0
                print("try reconnect {}".format(str(i)))
                time.sleep(10)
                client.close()
            if ssh_flag == 1:
                print("connect success")
                break
        return client

    def exec_cmdline(self, ssh_server ,cmdline):
        client = self.get_connect(ssh_server)    
        print('\nThe command to be executed is: \n' + cmdline)
        stdin, stdout, stderr = client.exec_command(str('{}'.format(cmdline)))
        # print('\n******* exec cmdline...\n')
        info_list = [line.strip('\n') for line in stdout]
        for line in stdout:
            pass
        client.close()
        return info_list

    def dict_get(self, dict1, objkey, default):
        tmp = dict1
        for k,v in tmp.items():
            if k == objkey:
                return v
            else:
                if type(v) is dict:
                    ret = self.dict_get(v, objkey, default)
                    if ret is not default:
                        return ret
                if type(v) is list:
                    ret = self.dict_get(v[0], objkey, default)
                    if ret is not default:
                        return ret
        return default

    def kill_task(self, runflag):
        task_clear = self.exec_cmdline(self.node_ip, 'killall -15 {}'.format(runflag))
        time.sleep(2)
        task_clear = self.exec_cmdline(self.node_ip, 'ps aux | grep {} | grep -v grep | wc -l'.format(runflag))
        if int(task_clear[0]) > 0:
            task_clear = self.exec_cmdline(self.node_ip, 'killall -2 {}'.format(runflag))
            time.sleep(5)
            task_clear = self.exec_cmdline(self.node_ip, 'ps aux | grep {} | grep -v grep | wc -l'.format(runflag))
            if int(task_clear[0]) > 0:
                task_clear = self.exec_cmdline(self.node_ip, 'killall -9 {}'.format(runflag))
                print("warning: task killall -9")

    # @pytest.mark.parametrize("index, value", stuple_list)
    def test_transcode(self, index, value, source_video, source_res, bitrate, ip, runflag):
        # print(ip)
        self.node_ip = ip
        if runflag == 'ffmpeg':
            # build 8
            # basic_cmd = "cd /tmp;ffmpeg -y -c:v v205h264 -i /tmp/{}  -c:v v205h264 -an -preset veryfast -bf 3  -vsync 0 -rc-lookahead 40 -b:v {} -r 30 -g 90 -ratetol 1 -s {} /tmp/output1.mp4".format(source_video, bitrate,source_res)

            # build 4 
            source_res_w = source_res.split('x')[0]
            source_res_h = source_res.split('x')[1]
            basic_cmd = "cd /tmp;ffmpeg -y -c:v v205h264 -i /tmp/{}  -c:v v205h264 -an -preset veryfast -bf 3  -rc-lookahead 40 -b:v {} -r 30 -g 90 -ratetol 1 -outw {} -outh {} /tmp/output1.mp4".format(source_video, bitrate,source_res_w, source_res_h)
        elif runflag == 'stream_mixer':
            # stream_mixer
            source_res_w = source_res.split('x')[0]
            source_res_h = source_res.split('x')[1]
            basic_cmd = "cd /tmp/;stream_mixer -port tmp_port  -i /tmp/{}  -an -c:v v205h264  -bgw {} -bgh {}  -outw {} -outh {} -preset veryfast -bf 3 -r 30 -g 90 -b:v {} -ratetol 1 -in_plugin mp -out_plugin mp -o /tmp/output01.mp4".format(source_video,source_res_w, source_res_h ,source_res_w, source_res_h, bitrate)
        else:
            print("Error: no runflag, please input runflag")
            exit(-1)

        self.kill_task(runflag)
        time.sleep(2)

        value_dicts = self.option_mark(value)
        basic_cmd_list = [i for i in basic_cmd.split(' ') if i != ' ']
        for dict_key, dict_value in value_dicts.items():
            for list_index, list_value in enumerate(basic_cmd_list):
                if dict_key == '-bf' and dict_value == '0' and dict_key == list_value: 
                    basic_cmd_list[list_index+1] = str(dict_value) + ' -b-adapt 0'
                elif dict_key == list_value: 
                    basic_cmd_list[list_index+1] = dict_value
        transcode_cmd = ' '.join(basic_cmd_list)
        print('')
        for task_num in range(1,36):
            cmd_use = transcode_cmd[0:transcode_cmd.rindex(' ')] + ' /tmp/out{}.mp4 2>&1 | tee thread{}.log &'.format(str(task_num), str(task_num))
            if runflag == 'stream_mixer':
                # print(cmd_use)
                run_port = str(51880 + task_num)
                cmd_use = cmd_use.replace("tmp_port", run_port)
                # print(cmd_use)
            transcode = self.exec_cmdline(self.node_ip, cmd_use)
            # if source_res == '480x360' or source_res == '640x480':
            #     time.sleep(0.5)
            # else:
            time.sleep(0.5)
            check_num = self.exec_cmdline(self.node_ip, 'ps aux | grep {} | grep -v grep | wc -l'.format(runflag))
            if isinstance(check_num, list):
                check_num = check_num[0]
            else:
                print("warning: check num is none, set check num 0 and fail this task")
                check_num = 0
            print("task_num: {}".format(task_num))
            print("check_num: {}".format(check_num))
            if task_num != int(check_num):
                print("waring: task_num != check_num")
                print("task_num: {}".format(task_num))
                print("check_num: {}".format(check_num))
                err_info = self.exec_cmdline(self.node_ip ,"tail -n 4 /tmp/thread{}.log".format(str(task_num)))
                print("error message:")
                for i in err_info:
                    print(i)
                break
            # time.sleep(1)
        print("**********")

        self.kill_task(runflag)
        # while True:
        time.sleep(5)
        option_list = '-'.join([str(index), value, source_video, source_res, bitrate])
        self.transcode_write_data.append([option_list, task_num, check_num, err_info])
        return self.transcode_write_data


