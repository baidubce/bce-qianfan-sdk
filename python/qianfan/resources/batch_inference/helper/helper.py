import concurrent.futures
import json
import os
import re
import subprocess
import time
from typing import Any, Dict, List

from qianfan import QfResponse, resources
from qianfan.config import encoding
from qianfan.utils.logging import log_debug, log_error, log_info
from qianfan.utils.utils import generate_letter_num_random_id, uuid

# 最大支持300mb
MAX_SUPPORTED_FILE_SIZE = 300 * 1024 * 1024
MAX_SUPPORTED_FILE_COUNT = 100
SLEEP_INTERVAL = 15


class AFSClient(object):
    def __init__(self, **kwargs: Any):
        self.host = kwargs.get("host", None)
        self.ugi = kwargs.get("ugi", None)

    def put(self, *params: Any) -> str:
        return self._exec("put", *params)

    def du(self, *params: Any) -> str:
        res = self._exec("du", *params)
        return res

    def get(self, remote_path: str, local_path: str) -> str:
        res = self._exec("get", remote_path, local_path)
        return res

    def rmr(self, *params: Any) -> str:
        return self._exec("rmr", *params)

    def _get_exec_cmd(self, cmd: str, *params: Any) -> str:
        log_debug(f"run cmd {cmd} {params}")
        exec_cmd = (
            "hadoop fs"
            f" -Dfs.default.name={self.host} "
            f"-Dhadoop.job.ugi={self.ugi} -{cmd} {' '.join(params)} "
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

    def mv(self, *params: Any) -> str:
        return self._exec("mv", *params)

    def mkdir(self, *params: Any) -> str:
        try:
            return self._exec("mkdir", *params)
        except ValueError as e:
            if "File exists" in str(e):
                pass
            else:
                raise e
        return ""

    def cp(self, *params: Any) -> str:
        return self._exec("cp", *params)


def call_bf(afs_config: dict, **kwargs: Any) -> QfResponse:
    create_bf_resp = resources.Data.create_offline_batch_inference_task(
        name=kwargs.get("name") or f"bf_{generate_letter_num_random_id(8)}",
        afs_config=afs_config,
        **kwargs,
    )
    return create_bf_resp


def wait_bf_task(task_id: str, wait_finished: bool = True) -> Any:
    while True:
        resp = resources.Data.get_offline_batch_inference_task(task_id=task_id)
        result = resp.get("result", {})
        if not wait_finished:
            break
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
        time.sleep(SLEEP_INTERVAL)
    return result


class BatchInferenceHelper:
    # 使用正则表达式来匹配文件名和大小
    jsonl_files_pattern = re.compile(r"(\d+)\s+(\S+jsonl)")

    def __init__(self, host: str, ugi: str, **kwargs: Any) -> None:
        # TODO 抽象一个统一的client or DataSource，实现put，get, du, mkdir等操作
        self.afs_client = AFSClient(host=host, ugi=ugi, **kwargs)

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
                if current_size >= MAX_SUPPORTED_FILE_SIZE:
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
            self.afs_client.get(remote_path, local_path)
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
        self.afs_client.mkdir(target_dir)
        self.afs_client.put(*[*local_file_batch, target_dir])

    def _batch_upload_local_file(
        self, data_path: str, split_local_files: List[str]
    ) -> List:
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
        self.afs_client.mkdir(target_dir)
        self.afs_client.cp(*[*remote_file_batch, target_dir])

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
                    <= MAX_SUPPORTED_FILE_SIZE
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

    def _prepare_ds(self, bf_id: str, input_uri: str) -> List:
        ds_id = bf_id
        data_path = "/".join([input_uri, ds_id])
        res = self.afs_client.du(input_uri)
        jsonl_files = self.filter_jsonl_files(res)
        if not jsonl_files:
            raise ValueError("no jsonl files found in the {input_uri}")

        log_debug(f"scanned input jsonl file:{jsonl_files}")
        small_files = []
        exceed_files = []
        for f in jsonl_files:
            if int(f["size"]) > MAX_SUPPORTED_FILE_SIZE:
                exceed_files.append(f)
            else:
                small_files.append(f)

        res_ds_input_dirs = []
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

        return res_ds_input_dirs

    def wait_for_tasks(self, tasks: List[str], wait_finished: bool = True) -> List:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(wait_bf_task, task_id, wait_finished)
                for i, task_id in enumerate(tasks)
            ]
            res = []
            for future in concurrent.futures.as_completed(futures):
                res.append(future.result())
            return res

    def batch_inference(
        self, input_uri: str, output_uri: str, wait_finished: bool = True, **kwargs: Any
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
        input_group_uris = self._prepare_ds(bf_id, input_uri)
        log_info(f"input uris:{input_group_uris}")
        task_list = []
        user_name, password = self.afs_client.ugi.split(",")
        for input_group_uri in input_group_uris:
            resp = call_bf(
                afs_config={
                    "userName": user_name,
                    "password": password,
                    "inputAfsUri": input_group_uri,
                    "outputAfsUri": output_uri,
                },
                **kwargs,
            )
            task_list.append(resp["result"]["taskId"])

        log_info(f"batch inference id [{bf_id}] with api tasks: {task_list}")
        with open(f"{bf_id}/bf_task_ids.json", "w+", encoding=encoding()) as f:
            json.dump(task_list, f, ensure_ascii=False)
        res = self.wait_for_tasks(task_list, wait_finished)
        for r in res:
            log_info(
                f'task_id: {r["taskId"]} status: {r["runStatus"]}, output_dir:'
                f' {"/".join([r["outputAfsUri"], r["outputDir"]])}'
            )
        if del_after_finished:
            self.afs_client.rmr(*input_group_uris)

        return {"bf_id": bf_id, "results": res}

    def status(self, bf_id: str, pooling: bool = False) -> List:
        """
        status of a batch inference
        Args:
            bf_id: batch inference id
            pooling: whether to poll the status of tasks until they are
                all finished
        """
        with open(f"{bf_id}/bf_task_ids.json", "r", encoding=encoding()) as f:
            task_list = json.load(f)
            res = self.wait_for_tasks(task_list, pooling)
            for r in res:
                log_info(
                    f'task_id: {r["taskId"]} status: {r["runStatus"]},'
                    f' done_query_count: {r["progress"]}, output_dir:'
                    f' {"/".join([r["outputAfsUri"], r["outputDir"]])}'
                )
        return res


def ensure_directory_exists(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)
