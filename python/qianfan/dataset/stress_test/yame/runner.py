#!/usr/bin/env python3
# coding=utf-8
"""
locust runner
"""
import json
import os
import sys
import time
import math
import signal
import multiprocessing
from urllib.parse import urlparse

import locust.main

from yame.utils import select_a_free_port, strftime
from yame.logger import console_logger
import yame.listeners  # required


class LocustRunner(object):
    """class: LocustRunner"""

    def __init__(self, locustfile='lucustfile.py',
                 user_num=1, worker_num=1, runtime='1m', spawn_rate=1, host=None,
                 master_host=None, master_port=None, enable_web=False, web_port=None, web_host=None,
                 recording=False, record_dir=None, loglevel=None, logfile=None, report=None,
                 csv_prefix=None, csv_full_history=False, json=False, only_summary=False,
                 **kwargs):
        self.locustfile = locustfile
        # headless开启时有效
        self.user_num = user_num
        self.runtime = runtime
        self.spawn_rate = spawn_rate
        self.host = host

        # workers>1时有效
        self.worker_num = worker_num
        self.master_host = master_host or '127.0.0.1'
        self.master_port = master_port or select_a_free_port(self.master_host) if self.worker_num > 1 else None

        # 打开web interface时有效
        self.enable_web = enable_web
        self.web_port = web_port
        self.web_host = web_host

        # 日志记录参数
        self.recording = recording  # 是否开启自动记录
        self.record_dir = record_dir
        self.loglevel = loglevel
        self.logfile = logfile
        self.report = report
        self.csv_prefix = csv_prefix
        self.csv_full_history = csv_full_history
        self.json = json
        self.only_summary = only_summary

        # 自定义参数
        self.custom_params = kwargs

    def generate_record_path(self):
        """
        生成记录保存路径
        """
        if self.recording:
            if not self.record_dir:
                self.record_dir = 'record/%s' % time.strftime('%Y%m%dT%H%M%SZ', time.localtime())
            if not os.path.exists(self.record_dir):
                os.makedirs(self.record_dir)
            if not self.logfile:
                self.logfile = os.path.join(self.record_dir, 'run.log')
            if not self.report:
                self.report = os.path.join(self.record_dir, 'report.html')
            if not self.csv_prefix:
                self.csv_prefix = os.path.join(self.record_dir, 'statistics')
            return self.record_dir

    def generate_command(self, role):
        """
        生成locust执行命令
        """
        if not os.path.isfile(self.locustfile):
            raise FileNotFoundError(self.locustfile)

        cmd = f'locust -f {self.locustfile} '
        if self.enable_web:
            if self.web_port:
                cmd += f'--web-port {self.web_port} '
            if self.web_host:
                cmd += f'--web-host {self.web_host} '
        else:
            cmd += '--headless '
            if role == 'master' or role == 'local':
                cmd += f'-u {self.user_num} -t {self.runtime} '
                if self.host:
                    cmd += f'-H {self.host} '
            if role == 'master':
                cmd += f'--expect-workers {self.worker_num} '
            cmd += f'--spawn-rate {self.spawn_rate} '

        if role == 'master':
            cmd += f'--{role} --master-bind-host {self.master_host} --master-bind-port {self.master_port} '
        elif role == 'worker':
            cmd += f'--{role} --master-host {self.master_host} --master-port {self.master_port} '

        for k, v in self.custom_params.items():
            cmd += f'--{k} {v} '

        if self.loglevel:
            cmd += f'--loglevel {self.loglevel} '
        if self.logfile:
            cmd += f'--logfile {self.logfile} '
        if role != 'worker':
            if self.report:
                cmd += f'--html {self.report} '
            if self.csv_prefix:
                cmd += f'--csv {self.csv_prefix} '
            if self.csv_full_history:
                cmd += '--csv-full-history '
        if self.json:
            cmd += '--json '
        if self.only_summary:
            cmd += '--only-summary '

        return cmd
        
    def master(self):
        """
        run master in process
        """
        cmd = self.generate_command('master')
        console_logger.debug(cmd)
        sys.argv = cmd.split()
        locust.main.main()

    def worker(self, wid):
        """
        run worker in process
        """
        os.environ['WORKER_INDEX'] = str(wid)
        cmd = self.generate_command('worker')
        console_logger.debug(cmd)
        sys.argv = cmd.split()
        locust.main.main()

    def local(self):
        """
        run local runner
        """
        cmd = self.generate_command('local')
        console_logger.debug(cmd)
        sys.argv = cmd.split()
        locust.main.main()

    @staticmethod
    def _kill_process(process: multiprocessing.Process):
        """kill master or worker process"""
        if isinstance(process, multiprocessing.Process) and process.is_alive():
            os.kill(process.pid, signal.SIGKILL)

    @staticmethod
    def _kill_master_and_workers(master, workers):
        """
        kill locust master and all workers processes
        """
        LocustRunner._kill_process(master)
        if isinstance(workers, (list, tuple)):
            for worker in workers:
                LocustRunner._kill_process(worker)

    def run(self):
        """
        run load test job
        """
        if self.host:
            os.environ['HOST'] = urlparse(self.host).scheme + '://' + urlparse(self.host).netloc
        os.environ["WORKER_NUM"] = str(self.worker_num)
        os.environ["USER_NUM"] = str(self.user_num)

        if self.spawn_rate is None:
            self.spawn_rate = max(1, math.ceil(self.user_num / self.worker_num))

        self.generate_record_path()

        start_time = time.time()
        if self.worker_num == 1:
            process = multiprocessing.Process(target=self.local)
            process.start()
            process.join()
            if not process.is_alive() and process.exitcode != 0:
                console_logger.error(f'local runner pid={process.pid} exitcode={process.exitcode}.')
        else:
            master = None
            workers = []
            try:
                master = multiprocessing.Process(target=self.master)
                master.start()

                time.sleep(0.5)
                if not master.is_alive():
                    console_logger.error(f'locust master pid={master.pid} exitcode={master.exitcode}.')
                    exit(1)

                for i in range(self.worker_num):
                    worker = multiprocessing.Process(target=self.worker, args=(i, ))
                    workers.append(worker)
                    worker.start()

                while True:
                    time.sleep(1)
                    if not master.is_alive():
                        if master.exitcode == 0:
                            for worker in workers:
                                worker.join()
                        else:
                            console_logger.error(f'locust master exitcode={master.exitcode}.')
                            for worker in workers:
                                self._kill_process(worker)
                        break
                    else:
                        is_error = False
                        for worker in workers:
                            if not worker.is_alive() and worker.exitcode != 0:
                                console_logger.error(f'locust worker pid={worker.pid} exitcode={worker.exitcode}.')
                                is_error = True
                                break

                        if is_error:
                            self._kill_master_and_workers(master, workers)
                            exit(2)
            except Exception as e:
                self._kill_master_and_workers(master, workers)
                raise e
        end_time = time.time()
        console_logger.info('run completed.')
        result = {
            'start_time': strftime(start_time),
            'end_time': strftime(end_time),
            'duration': end_time - start_time,
            'start_timestamp': start_time,
            'end_timestamp': end_time,

            'spawn_rate': self.spawn_rate,
            'workers': self.worker_num,
            'users': self.user_num,

            'record_dir': self.record_dir,
            'csv_prefix': self.csv_prefix,
            'html_report': self.report,
            'logfile': self.logfile,
            'loglevel': self.loglevel or 'INFO' if self.logfile else None,
            'stats_csv_file': None,
            'all_csv_files': [],
        }
        if self.csv_prefix:
            result['stats_csv_file'] = (self.csv_prefix or '') + '_stats.csv'
            csv_files = []
            csv_dir = os.path.dirname(self.csv_prefix) or ''
            csv_filename_prefix = os.path.basename(self.csv_prefix)
            if not csv_dir or os.path.isdir(csv_dir):
                for subfile in os.listdir(csv_dir or '.'):
                    if subfile.startswith(csv_filename_prefix) and subfile.endswith('.csv'):
                        csv_files.append(os.path.join(csv_dir or '', subfile))
            csv_files.sort()
            result['all_csv_files'] = csv_files

        console_logger.debug(json.dumps(result, indent=4, ensure_ascii=False))
        return result
