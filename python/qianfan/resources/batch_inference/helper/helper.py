# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import concurrent.futures
import json
import os
import re
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, cast

from qianfan import QfResponse, resources
from qianfan.config import encoding, get_config
from qianfan.errors import RequestError
from qianfan.utils.bos_uploader import BosHelper
from qianfan.utils.logging import log_debug, log_error, log_info
from qianfan.utils.utils import generate_letter_num_random_id, uuid

# 最大支持300mb
MAX_SUPPORTED_FILE_SIZE = 100 * 1024 * 1024
MAX_SUPPORTED_FILE_COUNT = 100
SLEEP_INTERVAL = 15
RETRY_COUNT = 5
LOCAL_QUEUE_SIZE = 128
MAX_REMOTE_TASKS = 40
MIN_BF_LIST_POLLING_INTERVAL = 1


class BaseClient(object):
    def put(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        raise NotImplementedError

    def du(self, file_path: List[str], *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError

    def get(self, remote_path: str, local_path: str) -> str:
        raise NotImplementedError

    def rmr(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError

    def rm(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError

    def mv(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        raise NotImplementedError

    def mkdir(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError

    def cp(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        raise NotImplementedError

    def get_modify_time(self, path: str, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError


class AFSClient(BaseClient):
    def __init__(self, **kwargs: Any):
        self.host = kwargs.get("host", None)
        self.ugi = kwargs.get("ugi", None)

    def put(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        return self._exec("put", *local_paths, remote_path, *args)

    def du(self, file_path: List[str], *args: Any, **kwargs: Any) -> str:
        return self._exec("du", *file_path, *args)

    def get(self, remote_path: str, local_path: str) -> str:
        return self._exec("get", remote_path, local_path)

    def rmr(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        return self._exec("rmr", *remote_paths, *args)

    def rm(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        return self._exec("rm", *remote_paths, *args)

    def _get_exec_cmd(self, cmd: str, *params: Any) -> str:
        log_debug(f"run cmd {cmd} {params}")

        host = str(self.host).replace("'", r"\'")
        ugi = str(self.ugi).replace("'", r"\'")

        exec_cmd = (
            f"hadoop fs '-Dfs.default.name={host}' '-Dhadoop.job.ugi={ugi}'"
            f" {shlex.quote('-{}'.format(cmd))} "
            f"{' '.join([shlex.quote(str(p)) for p in params])} "
        )
        return exec_cmd

    def _exec(self, cmd: str, *params: Any) -> str:
        exec_cmd = self._get_exec_cmd(cmd, *params)
        result = subprocess.run(exec_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            log_error(
                f"run {exec_cmd} ret code {result.returncode}, res {result.stderr}"
            )
            raise ValueError(f"failed to execute command {exec_cmd}: {result.stderr}")
        return result.stdout

    def mv(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        return self._exec("mv", *local_paths, remote_path, *args)

    def mkdir(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        try:
            return self._exec("mkdir", *remote_paths, *args)
        except ValueError as e:
            if "File exists" in str(e):
                pass
            else:
                raise e
        return ""

    def cp(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        return self._exec("cp", *local_paths, remote_path, *args)

    def get_modify_time(self, path: str, *args: Any, **kwargs: Any) -> str:
        return self._exec("stat", "%y", path)

    def test(self, path: str, *args: Any, **kwargs: Any) -> int:
        try:
            self._exec("test", *[*args, path])
            return 0
        except ValueError:
            return 1


class BosClient(BaseClient):
    def __init__(
        self,
        region: str,
        bucket: str,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ):
        self.region = region
        self.bucket = bucket
        self.ak = ak if ak is not None else get_config().ACCESS_KEY
        self.sk = sk if sk is not None else get_config().SECRET_KEY
        self.bos_helper = BosHelper(self.region, self.ak, self.sk)

    def put(
        self,
        local_paths: List[str],
        remote_path: str,
        is_remote_dir: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        if remote_path.endswith("/"):
            is_remote_dir = True

        if len(local_paths) == 1:
            ext = Path(remote_path).suffix
            if not ext and is_remote_dir:
                remote_path = str(Path(remote_path).joinpath(Path(local_paths[0]).name))

            self.bos_helper.upload_file_to_bos(local_paths[0], remote_path, self.bucket)

        else:
            base_remote_path = remote_path
            for local_path in local_paths:
                remote_path = str(
                    Path(base_remote_path).joinpath(Path(local_path).name)
                )
                self.bos_helper.upload_file_to_bos(local_path, remote_path, self.bucket)

        return ""

    def du(self, file_path: List[str], *args: Any, **kwargs: Any) -> str:
        ret_str = ""
        for path in file_path:
            files = self.bos_helper.list_dir(self.bucket, path)

            for file in files:
                ret_str += f"{file.size} /{file.key}\n"
        return ret_str

    def get(self, remote_path: str, local_path: str) -> str:
        self.bos_helper.get_object_as_file(self.bucket, remote_path, local_path)
        return ""

    def rmr(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        for path in remote_paths:
            files = self.bos_helper.list_dir(self.bucket, path, False)

            for file in files:
                self.bos_helper.delete_bos_file_anyway(self.bucket, str(file.key))

        return ""

    def rm(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        for path in remote_paths:
            files = self.bos_helper.list_dir(self.bucket, path)

            for file in files:
                if not str(file.key).endswith("/"):
                    self.bos_helper.delete_bos_file_anyway(self.bucket, str(file.key))

        return ""

    def mv(
        self, local_paths: List[str], remote_path: str, *args: Any, **kwargs: Any
    ) -> str:
        self.cp(local_paths, remote_path)
        self.rmr(local_paths, remote_path)

        return ""

    def mkdir(self, remote_paths: List[str], *args: Any, **kwargs: Any) -> str:
        # 不实现
        return ""

    def cp(
        self,
        local_paths: List[str],
        remote_path: str,
        is_remote_dir: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        if remote_path.endswith("/"):
            is_remote_dir = True

        def _copy_one(local_path: str, remote_path: str) -> None:
            ext = Path(remote_path).suffix
            if not ext and is_remote_dir:
                remote_path = str(Path(remote_path).joinpath(Path(local_path).name))

            self.bos_helper.copy_object(self.bucket, local_path, remote_path)

        for local_path in local_paths:
            if self.bos_helper.is_dir(self.bucket, local_path):
                files = self.bos_helper.list_dir(self.bucket, local_path, False)

                for file in files:
                    sub_file_path = f"/{str(file.key)}"
                    if sub_file_path == local_path:
                        pass

                    t_remote_path = str(
                        Path(remote_path).joinpath(sub_file_path.lstrip(local_path))
                    )
                    self.bos_helper.copy_object(
                        self.bucket, sub_file_path, t_remote_path
                    )
            else:
                _copy_one(local_path, remote_path)

        return ""

    def get_modify_time(self, path: str, *args: Any, **kwargs: Any) -> str:
        return self.bos_helper.get_metadata(self.bucket, path)["last_modified"]


def call_bf(
    afs_config: Optional[dict] = None, bos_config: Optional[dict] = None, **kwargs: Any
) -> QfResponse:
    if not kwargs.get("retry_count"):
        kwargs["retry_count"] = RETRY_COUNT

    def retry_if_error(error: Exception) -> bool:
        if isinstance(error, RequestError):
            if error.status_code == 403:
                try:
                    assert isinstance(error.body, (str, bytes))
                    err_resp = json.loads(error.body)
                    if err_resp.get("code") == "AccessDenied":
                        # try cover 403 AccessDenied
                        return True
                except Exception as e:
                    log_error(f"failed to parse error response: {error.body} {e}")
        return False

    if afs_config is not None:
        create_bf_resp = resources.Data.create_offline_batch_inference_task(
            name=kwargs.get("name") or f"bf_{generate_letter_num_random_id(10)}",
            afs_config=afs_config,
            retry_err_handler=retry_if_error,
            **kwargs,
        )
    elif bos_config is not None:
        create_bf_resp = resources.Data.create_offline_batch_inference_task(
            name=kwargs.get("name") or f"bf_{generate_letter_num_random_id(10)}",
            retry_err_handler=retry_if_error,
            **bos_config,
            **kwargs,
        )
    else:
        raise Exception("no param has been provided")
    return create_bf_resp


def infer_task_status(task_id: str, **kwargs: Any) -> QfResponse:
    if not kwargs.get("retry_count"):
        kwargs["retry_count"] = RETRY_COUNT
    return resources.Data.get_offline_batch_inference_task(task_id=task_id, **kwargs)


def wait_bf_task(
    task_id: str,
    wait_finished: bool = True,
    polling_interval: float = SLEEP_INTERVAL,
    **kwargs: Any,
) -> Any:
    while True:
        if not wait_finished:
            break
        result = infer_task_status(task_id=task_id, **kwargs).body
        run_status = result.get("runStatus")
        if run_status == "Running":
            log_info(
                f"task {task_id} is running. done_query_count:"
                f" {result.get('progress', 'Unknown')}"
            )
        elif run_status == "Done":
            log_info(f"task {task_id} is succeed.{result}")
            break
        else:
            log_error(f"task status is {run_status}, exiting")
            break
        time.sleep(polling_interval)
    return result


class BatchInferenceHelper:
    # 使用正则表达式来匹配文件名和大小
    jsonl_files_pattern = re.compile(r"(\d+)\s+(\S+jsonl)")

    def __init__(
        self,
        host: Optional[str] = None,
        ugi: Optional[str] = None,
        bos_region: Optional[str] = None,
        bos_bucket: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        # TODO 抽象一个统一的client or DataSource，实现put，get, du, mkdir等操作
        if host is not None and ugi is not None:
            self.client: BaseClient = AFSClient(host=host, ugi=ugi, **kwargs)
        elif bos_region is not None and bos_bucket is not None:
            self.client = BosClient(bos_region, bos_bucket, **kwargs)
        else:
            raise Exception("no sufficient argument has been provided")

        self.max_single_file_size = kwargs.get(
            "max_single_file_size", MAX_SUPPORTED_FILE_SIZE
        )
        self.polling_interval = kwargs.get("polling_interval", SLEEP_INTERVAL)
        self.queue: Queue = Queue(self.max_single_file_size or LOCAL_QUEUE_SIZE)
        self.max_remote_tasks = kwargs.get("max_remote_tasks", MAX_REMOTE_TASKS)
        self._monitor_task_pool: Dict[str, InferTask] = {}
        self._running = False
        self._queue_process_thread = threading.Thread(
            target=self._start_process_queue, daemon=True
        )
        self._queue_process_thread.start()
        self._monitor_task_pool_lock = threading.Lock()

    def __del__(self) -> None:
        self._running = False
        if self._queue_process_thread:
            self._queue_process_thread.join()

    def _get_all_tasks(self, run_status: str) -> List[Dict]:
        result: List[Dict] = []
        while True:
            cur_resp = resources.Data.list_offline_batch_inference_task(
                max_keys=100,
                run_status=run_status,
                page_reverse=True,
                retry_count=RETRY_COUNT,
            )
            page_info = cur_resp.body.get("result", {}).get("pageInfo", {})
            task_list = cur_resp.body.get("result", {}).get("taskList", [])
            result.append(task_list)
            if len(task_list) == 0 or not page_info.get("isTruncated"):
                break
            time.sleep(0.5)
        return result

    def _start_process_queue(self) -> None:
        task: Optional[InferTask] = None
        self._running = True
        while self._running:
            if not task:
                try:
                    task = self.queue.get(False)
                except Empty:
                    time.sleep(1)
                    continue
            try:
                running_tasks = self._get_all_tasks(run_status="Running")
            except Exception as e:
                log_error(f"get running tasks error {e}")
                time.sleep(15)
                continue
            if self.max_remote_tasks > len(running_tasks):
                try:
                    assert task is not None
                    resp = call_bf(**task.request_input)
                except Exception as e:
                    #  无限重试。
                    log_error(f"create batch inference task error {e}")
                    continue
                task_id = resp.body.get("result", {}).get("taskId")
                log_info(f"created infer_task:{ task_id}, {task}")
                with self._monitor_task_pool_lock:
                    self._monitor_task_pool[task.id].infer_id = task_id
                task = None
            else:
                time.sleep(MIN_BF_LIST_POLLING_INTERVAL)

    def filter_jsonl_files(self, output: str) -> List:
        # 找到所有匹配项
        matches = BatchInferenceHelper.jsonl_files_pattern.findall(output)

        res = []
        # 打印结果
        for size, filename in matches:
            log_debug(f"File: {filename}, Size: {size}")
            res.append({"path": filename, "size": int(size)})
        return res

    def split_file(self, input_file: str) -> List:
        file_rand_num = generate_letter_num_random_id(8)
        path, input_file_name = input_file.split(".")[0].split("/")
        part_num = 0
        output_files = []
        output_file = f"{path}/{file_rand_num}-{input_file_name}-part{part_num}.jsonl"
        output_files.append(output_file)
        with open(input_file, "r", encoding="utf-8") as infile:
            outfile = open(output_file, "w", encoding="utf-8")
            current_size = 0

            for line in infile:
                current_size += len(line.encode("utf-8"))
                if current_size > self.max_single_file_size:
                    outfile.close()
                    part_num += 1
                    output_file = (
                        f"{path}/{file_rand_num}-{input_file_name}-part{part_num}.jsonl"
                    )
                    output_files.append(output_file)
                    outfile = open(output_file, "w", encoding="utf-8")
                    outfile.write(line)
                    current_size = len(line.encode("utf-8"))
                else:
                    outfile.write(line)

            outfile.close()

        return output_files

    def download_and_split_files(self, data_path: str, file_urls: List[str]) -> List:
        local_dir = data_path.split("/")[-1]

        def download_to_local(remote_path: str) -> str:
            ensure_directory_exists(local_dir)
            local_path = "/".join([local_dir, remote_path.split("/")[-1]])
            self.client.get(remote_path, local_path)
            return local_path

        all_output_files = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_url = {
                executor.submit(download_to_local, url): url for url in file_urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    output_files = self.split_file(data)
                    os.remove(data)
                    all_output_files.extend(output_files)
                    log_debug(f"{url} downloaded to {output_files}")
                except Exception as exc:
                    log_error(f"{url} generated an exception: {exc}")
        return all_output_files

    def _process_local_batch(
        self, local_file_batch: List[str], target_dir: str
    ) -> None:
        self.client.mkdir([target_dir])
        self.client.put(local_file_batch, target_dir, is_remote_dir=True)

    def _batch_upload_local_file(
        self, data_path: str, split_local_files: List[str]
    ) -> List[str]:
        grouped_files = [
            split_local_files[i : i + 1] for i in range(0, len(split_local_files), 1)
        ]
        split_files_dirs = [
            "/".join([data_path, "size_split", str(i)])
            for i in range(len(grouped_files))
        ]
        # 使用多线程处理每个批次，并为每个批次分配组编号
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._process_local_batch, group, split_files_dirs[i])
                for i, group in enumerate(grouped_files)
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()
        return split_files_dirs

    def _process_remote_batch(
        self, remote_file_batch: List[str], target_dir: str
    ) -> None:
        self.client.mkdir([target_dir])
        self.client.cp(remote_file_batch, target_dir, is_remote_dir=True)

    def _batch_group_remote_files(
        self, data_path: str, remote_files: List[Dict]
    ) -> List:
        grouped_files: List[List[Dict]] = []
        remote_files.sort(key=lambda x: x["size"], reverse=True)

        # 将文件分配到group中
        for file in remote_files:
            placed = False
            for group in grouped_files:
                # 检查是否可以将文件放入当前group
                if (
                    sum([item["size"] for item in group]) + file["size"]
                    <= self.max_single_file_size
                    and len(group) < MAX_SUPPORTED_FILE_COUNT
                ):
                    group.append(file)
                    placed = True
                    break
            if not placed:
                # 如果没有可放置的group，创建一个新的group
                grouped_files.append([file])

        split_files_dirs = [
            "/".join([data_path, "count_split", str(i)])
            for i in range(len(grouped_files))
        ]
        # 使用多线程处理每个批次，并为每个批次分配组编号
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self._process_remote_batch,
                    [item["path"] for item in group],
                    split_files_dirs[i],
                )
                for i, group in enumerate(grouped_files)
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()
        return split_files_dirs

    def _prepare_ds(self, bf_id: str, input_uri: str) -> List[str]:
        if isinstance(self.client, BosClient):
            prefix = f"bos:/{self.client.bucket}"
            if input_uri.startswith(prefix):
                input_uri = input_uri[len(prefix) :]

        ds_id = bf_id
        data_path = "/".join([input_uri.rstrip("/"), ds_id])
        res = self.client.du([input_uri])
        jsonl_files = self.filter_jsonl_files(res)
        if not jsonl_files:
            raise ValueError("no jsonl files found in the {input_uri}")

        log_debug(f"scanned input jsonl file:{jsonl_files}")
        small_files = []
        exceed_files = []
        for f in jsonl_files:
            if int(f["size"]) > self.max_single_file_size:
                exceed_files.append(f)
            else:
                small_files.append(f)

        res_ds_input_dirs: List[str] = []
        if exceed_files:
            # 拆分成小文件
            split_local_files = self.download_and_split_files(
                data_path, [f["path"] for f in exceed_files]
            )
            # 上传成一组文件
            res_ds_input_dirs.extend(
                self._batch_upload_local_file(data_path, split_local_files)
            )
            for f in split_local_files:
                os.remove(f)

        if small_files:
            res_ds_input_dirs.extend(
                self._batch_group_remote_files(
                    data_path, [f_meta for f_meta in small_files]
                )
            )

        if isinstance(self.client, BosClient):
            prefix = f"bos:/{self.client.bucket}"
            for i in range(len(res_ds_input_dirs)):
                res_ds_input_dirs[i] = res_ds_input_dirs[i].lstrip("/")
                res_ds_input_dirs[i] = f"{prefix}/{res_ds_input_dirs[i]}"

        return res_ds_input_dirs

    def wait_for_tasks(
        self, wait_finished: bool = True, **kwargs: Any
    ) -> List["InferTask"]:
        final_tasks: List[InferTask] = []
        while True:
            tasks = self._monitor_task_pool
            if len(tasks) == 0:
                break
            done_list = []
            for k, task in tasks.items():
                if task.infer_id and task.status in ["Running", "", None]:
                    try:
                        task.update_status()
                    except Exception as e:
                        log_error(f"failed to get task status:{e}")
                        time.sleep(5)
                        continue
                    time.sleep(5)
                elif task.infer_id:
                    if k in self._monitor_task_pool:
                        done_list.append(k)
                    final_tasks.append(task)
            with self._monitor_task_pool_lock:
                for k in done_list:
                    if k in self._monitor_task_pool:
                        del self._monitor_task_pool[k]
            if not wait_finished:
                break
            time.sleep(10)
        return final_tasks

    def _submit_tasks(self, tasks: List["InferTask"]) -> None:
        if len(tasks) == 0:
            return
        with self._monitor_task_pool_lock:
            for task in tasks:
                self.queue.put(task)
                self._monitor_task_pool[task.id] = task
        with open(
            f"{tasks[0].bf_id}/bf_task_infos.json", "w", encoding=encoding()
        ) as f:
            json.dump([r.id for r in self._monitor_task_pool.values()], f)

    def batch_inference(
        self,
        input_uri: str,
        output_uri: str,
        wait_finished: bool = True,
        done_file_uri: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        batch inference
        Args:
            input_uri: input uri
            output_uri: output uri
            wait_finished: whether to wait for the task to finish
            del_after_finished: whether to delete the input files after
                the task is finished
            **kwargs: other arguments
        """
        del_after_finished = kwargs.get("del_after_finished", False)
        bf_id = uuid()
        log_info(f"bf_id: {bf_id} batch inference inst created")
        ensure_directory_exists(bf_id)
        if kwargs.get("use_raw_input"):
            input_group_uris = [input_uri]
            kwargs.pop("use_raw_input")
        else:
            input_group_uris = self._prepare_ds(bf_id, input_uri)

        log_info(f"input uris:{input_group_uris}")

        if isinstance(self.client, AFSClient):
            user_name, password = self.client.ugi.split(",")
            bf_tasks = [
                InferTask(
                    bf_id=bf_id,
                    id=i,
                    request_input={
                        "afs_config": {
                            "userName": user_name,
                            "password": password,
                            "inputAfsUri": input_group_uri,
                            "outputAfsUri": output_uri,
                        },
                        **kwargs,
                    },
                )
                for i, input_group_uri in enumerate(input_group_uris)
            ]
        else:
            bf_tasks = [
                InferTask(
                    bf_id=bf_id,
                    id=i,
                    request_input={
                        "bos_config": {
                            "input_bos_uri": input_group_uri,
                            "output_bos_uri": output_uri,
                        },
                        **kwargs,
                    },
                )
                for i, input_group_uri in enumerate(input_group_uris)
            ]

        self._submit_tasks(bf_tasks)
        log_info(f"bf_id: {bf_id} with local queueing tasks num: {self.queue.qsize()}")
        res = self.wait_for_tasks(wait_finished=wait_finished)

        is_bos = isinstance(self.client, BosClient)

        for r in res:
            if r.output is None:
                log_error(f"failed to get result from server, task res: {r}")
                continue
            output_sub_uri: str = cast(
                str,
                (
                    r.output.get("outputAfsUri", "")
                    if not is_bos
                    else r.output.get("outputBosUri", "")
                ),
            )
            output_sub_dir: str = cast(str, r.output.get("outputDir", ""))
            log_info(
                f"bf: {bf_id}, task_id: {r.id}, infer_id: {r.infer_id} status:"
                f" {r.status}, output_dir:"
                f" { str(os.path.join(output_sub_uri, output_sub_dir))}"
            )
        if del_after_finished:
            if is_bos:
                assert isinstance(self.client, BosClient)
                prefix = f"bos:/{self.client.bucket}"
                input_group_uris = [
                    uri[len(prefix) :] if uri.startswith(prefix) else uri
                    for uri in input_group_uris
                ]

            self.client.rmr(input_group_uris)
        if done_file_uri:
            open(f"{bf_id}/DONE", "w", encoding=encoding())
            self.client.put([f"{bf_id}/DONE"], done_file_uri)

        return {"bf_id": bf_id, "results": res}

    def status(self, bf_id: str, pooling: bool = False) -> List:
        """
        status of a batch inference
        Args:
            bf_id: batch inference id
            pooling: whether to poll the status of tasks until they are
                all finished
        """
        with self._monitor_task_pool_lock:
            if not self._monitor_task_pool:
                with open(f"{bf_id}/bf_task_infos.json", "r", encoding=encoding()) as f:
                    task_id_list = json.load(f)
                    for id in task_id_list:
                        task = InferTask.load(bf_id, id)
                        self._monitor_task_pool[id] = task
                        if task.status in ["", None]:
                            self._submit_tasks([task])
            res = self.wait_for_tasks(wait_finished=pooling)
            for r in res:
                if r.output is None:
                    log_error(f"failed to get result from server, task res: {r}")
                    continue
                # TODO 需要抽象出通用的接口以适配bos等
                output_sub_uri: str = cast(str, r.output.get("outputAfsUri", ""))
                output_sub_dir: str = cast(str, r.output.get("outputDir", ""))
                log_info(
                    f"bf: {bf_id}, task_id: {r.id}, infer_id: {r.infer_id} status:"
                    f" {r.status}, output_dir:"
                    f" { str(os.path.join(output_sub_uri, output_sub_dir))}"
                )
        return res


@dataclass
class InferTask:
    bf_id: str = field(default="")
    id: Any = field(default=None)
    infer_id: Any = field(default=None)
    request_input: Dict = field(default_factory=dict)
    status: str = field(default="")
    output: Optional[Dict] = field(default=None)

    def __init__(self, bf_id: str, id: Any, request_input: Dict, **kwargs: Any) -> None:
        self.bf_id = bf_id
        self.id = id
        self.infer_id = kwargs.get("infer_id")
        self.request_input = request_input
        self.status = kwargs.get("status") or ""
        self.output: Optional[Dict] = None
        self.persist()

    def persist(self) -> None:
        with open(f"{self.bf_id}/{self.id}.json", "w", encoding=encoding()) as f:
            data = self.__dict__
            json.dump(
                data,
                f,
            )

    @classmethod
    def load(cls, bf_id: str, id: Any) -> "InferTask":
        with open(f"{bf_id}/{id}.json", "r", encoding=encoding()) as f:
            data = json.load(f)
            return cls(
                bf_id=bf_id,
                id=id,
                request_input=data.get("request_input"),
                status=data.get("status"),
                infer_id=data.get("infer_id"),
                output=data.get("output"),
            )

    def update_status(self, with_persist: bool = True) -> None:
        resp_body = infer_task_status(self.infer_id).body
        self.status = resp_body.get("result", {}).get("runStatus")
        self.output = resp_body.get("result")
        log_info(f"updating task status{self}")
        if with_persist:
            self.persist()


def ensure_directory_exists(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)
