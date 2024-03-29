# install pytest 4.0.2
# uninstall pytest 4.6.2
import pytest
import re
import paramiko
import time
import os
import json

class test_node_performance():
    def __init__(self):
        # self.node_ip = '172.16.231.31'
        self.performance_write_data = []
        self.ssh_port = 22
        self.ssh_name = 'root'
        self.ssh_password = "admin123"

    def run(self, cmd):
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

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

    # @pytest.mark.parametrize("index, value", self.stuple_list)
    def test_performance(self, index, preset, source_video, source_res, bitrate, ip, runflag):
    
        print('')
        # print(ip)
        self.node_ip = ip

        if runflag == 'ffmpeg':
            # ffmpeg build 8
            # basic_cmd = "cd /tmp/;time ffmpeg -y -c:v v205h264 -i /tmp/{}  -c:v v205h264 -an -preset {} -bf 3 -vsync 0  -b:v {} -r 30 -g 90 -ratetol 1 -s {} /tmp/output01.264".format(source_video, preset, bitrate,source_res)

            # ffmpeg build 4 
            source_res_w = source_res.split('x')[0]
            source_res_h = source_res.split('x')[1]
            basic_cmd = "cd /tmp/;time ffmpeg -y -c:v v205h264 -i /tmp/{}  -c:v v205h264 -an -preset {} -bf 3   -b:v {} -r 30 -g 90 -ratetol 1 -outw {} -outh {} /tmp/output01.264".format(source_video, preset, bitrate,source_res_w, source_res_h)
        elif runflag == 'stream_mixer':
            # stream_mixer
            source_res_w = source_res.split('x')[0]
            source_res_h = source_res.split('x')[1]
            basic_cmd = "cd /tmp/;time stream_mixer -port tmp_port  -i /tmp/{}  -an -c:v v205h264  -bgw {} -bgh {}  -outw {} -outh {} -preset {} -bf 3 -r 30 -g 90 -b:v {} -ratetol 1 -in_plugin mp -out_plugin mp -o /tmp/output01.264".format(source_video,source_res_w, source_res_h ,source_res_w, source_res_h, preset, bitrate)
        else:
            print("Error: no runflag, please input runflag")
            exit(-1)
        
        self.kill_task(runflag)
        time.sleep(2)
        del_dir = self.exec_cmdline(self.node_ip ,"cd /tmp/;rm -fr txt/")
        make_dir = self.exec_cmdline(self.node_ip ,"cd /tmp/;mkdir txt")
        for task_num in range(1, index+1):
            cmd_use = basic_cmd[0:basic_cmd.rindex(' ')] + ' /tmp/out{}.mp4 2>&1 | tee txt/264_{}.txt &'.format(str(task_num),str(task_num))
            if runflag == 'stream_mixer':
                run_port = str(51880 + task_num)
                cmd_use = cmd_use.replace("tmp_port", run_port)
            performance = self.exec_cmdline(self.node_ip, cmd_use)
            time.sleep(1)
        time.sleep(2)
        while True:
            check_num = self.exec_cmdline(self.node_ip, 'ps aux | grep {} | grep -v grep | wc -l'.format(runflag))
            print('{} threads: {}'.format(runflag, check_num))
            if int(check_num[0]) == 0:
                break
            time.sleep(30)
        time.sleep(1)
        time_get = '_'
        for task_num in range(1, index+1):
            run_time="cd /tmp/txt;cat 264_{}.txt | grep real | awk '{{print $2 $3}}'".format(str(task_num))
            run_times=self.exec_cmdline(self.node_ip, run_time)
            print(run_times)
            time_get = time_get+'_'+run_times[0]
        print(time_get)
        x = time_get.lstrip('_')
        time_get_list = x.split('_')
        for i in time_get_list:
            print("each loop time: {}".format(i))
        time_list = [float(i.split('m')[0])*60 + float(i.split('m')[1].rstrip('s')) for i in time_get_list]
        avg_time = sum(time_list) / len(time_list)
        print('avg_time:{}'.format(round(avg_time,2)))
        frames_cmdline = 'ffprobe -v error -count_frames -select_streams v:0  -show_entries stream=nb_read_frames -of default=nokey=1:noprint_wrappers=1 {}'.format(source_video)
        video_frames = self.run(frames_cmdline)
        fpss = [round(float(float(video_frames)/(float(i.split('m')[0])*60 + float(i.split('m')[1].rstrip('s')))),2) for i in time_get_list]
        cal_fps = sum(fpss)
        avg_fps = cal_fps / len(fpss)
        print('avg_fps:{}'.format(round(avg_fps,2)))
        print('total_fps:{}'.format(round(cal_fps,2)))
        option_list = '-'.join([str(index), preset, source_video, source_res, bitrate])
        self.performance_write_data.append([option_list, round(avg_time,2), round(avg_fps,2), round(cal_fps,2)])
        
        self.kill_task(runflag)
        # while True:
        time.sleep(5)
        return self.performance_write_data
