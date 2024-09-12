#!/usr/bin/env python3
# coding=utf-8
"""
locust runner
"""
import json
import math
import multiprocessing
import os
import signal
import sys
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import locust.main

import qianfan.dataset.stress_test.yame.listeners  # required
from qianfan.dataset.stress_test.yame import GlobalData
from qianfan.dataset.stress_test.yame.logger import console_logger
from qianfan.dataset.stress_test.yame.utils import select_a_free_port, strftime

_listeners = qianfan.dataset.stress_test.yame.listeners


class LocustRunner(object):
    """class: LocustRunner"""

    def __init__(
        self,
        locustfile: str = "lucustfile.py",
        user_num: int = 1,
        worker_num: int = 1,
        runtime: str = "1m",
        spawn_rate: int = 1,
        host: Optional[str] = None,
        master_host: Optional[str] = None,
        master_port: Optional[int] = None,
        enable_web: bool = False,
        web_port: Optional[int] = None,
        web_host: Optional[str] = None,
        recording: bool = False,
        record_dir: Optional[str] = None,
        loglevel: Optional[str] = None,
        logfile: Optional[str] = None,
        report: Optional[str] = None,
        csv_prefix: Optional[str] = None,
        csv_full_history: bool = False,
        json: bool = False,
        only_summary: bool = False,
        **kwargs: Any,
    ):
        self.locustfile = locustfile
        # headless开启时有效
        self.user_num = user_num
        self.runtime = runtime
        self.spawn_rate = spawn_rate
        self.host = host

        # workers>1时有效
        self.worker_num = worker_num
        self.master_host = master_host or "127.0.0.1"
        self.master_port = (
            master_port or select_a_free_port(self.master_host)
            if self.worker_num > 1
            else None
        )

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
        GlobalData.data.update(kwargs)

    def generate_record_path(self) -> Optional[str]:
        """
        生成记录保存路径
        """
        if self.recording:
            if not self.record_dir:
                self.record_dir = "record/%s" % time.strftime(
                    "%Y%m%dT%H%M%SZ", time.localtime()
                )
            if not os.path.exists(self.record_dir):
                os.makedirs(self.record_dir)
            sub_dir_name = f"round-user_num_{self.user_num}"
            sub_dir = os.path.join(self.record_dir, sub_dir_name)
            os.makedirs(sub_dir)
            # if not self.logfile:
            self.logfile = os.path.join(sub_dir, "run.log")
            # if not self.report:
            round_report_name = f"report_user_num_{self.user_num}.html"
            self.report = os.path.join(sub_dir, round_report_name)
            # if not self.csv_prefix:
            self.csv_prefix = os.path.join(sub_dir, "statistics")
            return sub_dir
        return None

    def generate_command(self, role: str) -> str:
        """
        生成locust执行命令
        """
        if not os.path.isfile(self.locustfile):
            raise FileNotFoundError(self.locustfile)

        cmd = f"locust -f {self.locustfile} "
        if self.enable_web:
            if self.web_port:
                cmd += f"--web-port {self.web_port} "
            if self.web_host:
                cmd += f"--web-host {self.web_host} "
        else:
            cmd += "--headless "
            if role == "master" or role == "local":
                cmd += f"-u {self.user_num} -t {self.runtime} "
                if self.host:
                    cmd += f"-H {self.host} "
            if role == "master":
                cmd += f"--expect-workers {self.worker_num} "
            cmd += f"--spawn-rate {self.spawn_rate} "

        if role == "master":
            cmd += (
                f"--{role} --master-bind-host {self.master_host} --master-bind-port"
                f" {self.master_port} "
            )
        elif role == "worker":
            cmd += (
                f"--{role} --master-host {self.master_host} --master-port"
                f" {self.master_port} "
            )

        if self.loglevel:
            cmd += f"--loglevel {self.loglevel} "
        if self.logfile:
            cmd += f"--logfile {self.logfile} "
        if role != "worker":
            if self.report:
                cmd += f"--html {self.report} "
            if self.csv_prefix:
                cmd += f"--csv {self.csv_prefix} "
            if self.csv_full_history:
                cmd += "--csv-full-history "
        if self.json:
            cmd += "--json "
        if self.only_summary:
            cmd += "--only-summary "

        return cmd

    def master(self) -> None:
        """
        run master in process
        """
        cmd = self.generate_command("master")
        console_logger.debug(cmd)
        sys.argv = cmd.split()
        locust.main.main()

    def worker(self, wid: int) -> None:
        """
        run worker in process
        """
        os.environ["WORKER_INDEX"] = str(wid)
        cmd = self.generate_command("worker")
        console_logger.debug(cmd)
        sys.argv = cmd.split()
        locust.main.main()

    def local(self) -> None:
        """
        run local runner
        """
        cmd = self.generate_command("local")
        console_logger.debug(cmd)
        sys.argv = cmd.split()
        locust.main.main()

    @staticmethod
    def _kill_process(process: multiprocessing.Process) -> None:
        """kill master or worker process"""
        if (
            isinstance(process, multiprocessing.Process)
            and process.is_alive()
            and process.pid is not None
        ):
            import platform

            if platform.system().lower() == "windows":
                os.kill(process.pid, getattr(signal, "CTRL_C_EVENT"))
            else:
                os.kill(process.pid, getattr(signal, "SIGKILL"))

    @staticmethod
    def _kill_master_and_workers(master: Any, workers: Any) -> None:
        """
        kill locust master and all workers processes
        """
        LocustRunner._kill_process(master)
        if isinstance(workers, (list, tuple)):
            for worker in workers:
                LocustRunner._kill_process(worker)

    def run(self, user_num: int) -> Dict[str, Any]:
        """
        run load test job
        """
        self.user_num = user_num
        if self.host:
            os.environ["HOST"] = (
                urlparse(self.host).scheme + "://" + urlparse(self.host).netloc
            )
        os.environ["WORKER_NUM"] = str(self.worker_num)
        os.environ["USER_NUM"] = str(self.user_num)

        if self.spawn_rate is None:
            self.spawn_rate = max(1, math.ceil(self.user_num / self.worker_num))

        record_dir = self.generate_record_path()
        GlobalData.data["record_dir"] = record_dir
        start_time = time.time()
        if self.worker_num == 1:
            process = multiprocessing.Process(target=self.local)
            process.start()
            process.join()
            if not process.is_alive() and process.exitcode != 0:
                console_logger.error(
                    f"local runner pid={process.pid} exitcode={process.exitcode}."
                )
            exit_code = process.exitcode
        else:
            master = None
            workers = []
            try:
                master = multiprocessing.Process(target=self.master)
                master.start()

                time.sleep(0.5)
                if not master.is_alive():
                    console_logger.error(
                        f"locust master pid={master.pid} exitcode={master.exitcode}."
                    )
                    exit(1)

                for i in range(self.worker_num):
                    worker = multiprocessing.Process(target=self.worker, args=(i,))
                    workers.append(worker)
                    worker.start()

                while True:
                    time.sleep(1)
                    if not master.is_alive():
                        if master.exitcode == 0:
                            for worker in workers:
                                worker.join()
                        else:
                            console_logger.error(
                                f"locust master exitcode={master.exitcode}."
                            )
                            for worker in workers:
                                self._kill_process(worker)
                        break
                    else:
                        is_error = False
                        for worker in workers:
                            if not worker.is_alive() and worker.exitcode != 0:
                                console_logger.error(
                                    "locust worker"
                                    f" pid={worker.pid} exitcode={worker.exitcode}."
                                )
                                is_error = True
                                break

                        if is_error:
                            self._kill_master_and_workers(master, workers)
                            exit(2)
            except Exception as e:
                self._kill_master_and_workers(master, workers)
                raise e
            exit_code = master.exitcode
        end_time = time.time()
        console_logger.info("run completed.")
        result: Dict[str, Any] = {
            "exitcode": exit_code,
            "start_time": strftime(start_time),
            "end_time": strftime(end_time),
            "duration": end_time - start_time,
            "start_timestamp": start_time,
            "end_timestamp": end_time,
            "spawn_rate": self.spawn_rate,
            "workers": self.worker_num,
            "users": self.user_num,
            "record_dir": record_dir,
            "csv_prefix": self.csv_prefix,
            "html_report": self.report,
            "logfile": self.logfile,
            "performance_dir": self.record_dir,
            "loglevel": self.loglevel or "INFO" if self.logfile else None,
            "stats_csv_file": None,
            "all_csv_files": [],
        }
        if self.csv_prefix:
            result["stats_csv_file"] = (self.csv_prefix or "") + "_stats.csv"
            csv_files = []
            csv_dir = os.path.dirname(self.csv_prefix) or ""
            csv_filename_prefix = os.path.basename(self.csv_prefix)
            if not csv_dir or os.path.isdir(csv_dir):
                for subfile in os.listdir(csv_dir or "."):
                    if subfile.startswith(csv_filename_prefix) and subfile.endswith(
                        ".csv"
                    ):
                        csv_files.append(os.path.join(csv_dir or "", subfile))
            csv_files.sort()
            result["all_csv_files"] = csv_files

        console_logger.debug(json.dumps(result, indent=4, ensure_ascii=False))
        return result
