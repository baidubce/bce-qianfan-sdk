"""
QianfanLocustRunner
"""


import logging
import os
import time
import traceback
from multiprocessing import Value
from typing import Any, Dict, List, Optional, Union

from qianfan import resources
from qianfan.dataset import Dataset
from qianfan.dataset.stress_test.load_statistics import gen_brief, generate_html_table
from qianfan.dataset.stress_test.yame import GlobalData
from qianfan.dataset.stress_test.yame.runner import LocustRunner

logger = logging.getLogger("yame.stats")
logger.setLevel(logging.INFO)
GlobalData.data["threshold_first"] = Value("i", 0)
GlobalData.data["first_latency_threshold"] = 0
GlobalData.data["log"] = 0


def model_details(endpoint: str) -> Optional[Dict[str, Any]]:
    try:
        info = resources.Service.V2.service_list()
        for inf in info.body["result"]["serviceList"]:
            temp = inf["url"].split("/")
            if temp[-1] == endpoint:
                return inf
        return None
    except Exception:
        return None


def determine_dataset_format(
    dataset: List[Union[Dict[str, str], List[Dict[str, str]], str]]
) -> Optional[str]:
    try:
        # 检查类型1：列表，包含字典，字典有 'prompt' 和 'response' 键
        if isinstance(dataset, list) and all(
            isinstance(item, dict) and "prompt" in item and "response" in item
            for item in dataset
        ):
            return "json"

        # 检查类型2：列表，包含列表，这些列表中包含字典，字典有 'prompt' 键
        if isinstance(dataset, list) and all(
            isinstance(item, list)
            and all(
                isinstance(sub_item, dict) and "prompt" in sub_item for sub_item in item
            )
            for item in dataset
        ):
            return "jsonl"

        # 检查类型3：列表，包含字符串
        if isinstance(dataset, list) and all(isinstance(item, str) for item in dataset):
            return "txt"

        # 如果不匹配任何类型
        return None
    except Exception:
        logger.error("无法识别该数据集格式!")
        return None


class QianfanLocustRunner(LocustRunner):
    """
    QianfanLocustRunner
    """

    locust_file = os.path.abspath(os.path.dirname(__file__)) + "/qianfan_llm_load.py"

    def __init__(
        self,
        dataset: Dataset,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        model_type: str = "ChatCompletion",
        user_num: int = 1,
        worker_num: int = 1,
        runtime: str = "1m",
        spawn_rate: int = 1,
        recording: bool = True,
        record_dir: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        rounds: int = 1,
        interval: Optional[int] = 0,
        first_latency_threshold: Optional[float] = 100,
        round_latency_threshold: Optional[float] = 1000,
        success_rate_threshold: Optional[float] = 0,
        model_info: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        if model is not None:
            host = model
            is_endpoint = False
        elif endpoint is not None:
            host = endpoint
            is_endpoint = True
        super(QianfanLocustRunner, self).__init__(
            locustfile=self.locust_file,
            user_num=user_num,
            worker_num=worker_num,
            runtime=runtime,
            spawn_rate=spawn_rate,
            host=host,
            recording=recording,
            record_dir=record_dir,
            dataset=dataset,
            model_type=model_type,
            hyperparameters=hyperparameters,
            is_endpoint=is_endpoint,
            rounds=rounds,
            interval=interval,
            first_latency_threshold=first_latency_threshold,
            round_latency_threshold=round_latency_threshold,
            success_rate_threshold=success_rate_threshold,
            model_info=model_info,
            **kwargs,
        )

        log = kwargs.get("log", False)
        if log:
            GlobalData.data["log"] = 1
        self.first_latency_threshold = first_latency_threshold or 100
        GlobalData.data["first_latency_threshold"] = self.first_latency_threshold * 1000
        self.round_latency_threshold = round_latency_threshold or 1000
        self.success_rate_threshold = success_rate_threshold or 0

        self.dataset = dataset
        self.model_type = model_type
        self.hyperparameters = hyperparameters
        self.user_num = user_num
        self.worker_num = worker_num
        self.spawn_rate = spawn_rate
        self.rounds = rounds
        self.interval = interval
        # 初始化基础 model_info 字典
        self.model_info = {
            "modelname": None,
            "modelVersionId": None,
            "serviceId": None,
            "serviceUrl": None,
            "computer": None,
            "replicasCount": None,
            "origin_user_num": self.user_num,
            "worker": self.worker_num,
            "rounds": self.rounds,
            "spawn_rate": self.spawn_rate,
            "hyperparameters": self.hyperparameters,
            "interval": self.interval,
            "log_info": "",
        }
        # 如果是端点且端点不为空，尝试获取模型信息
        if is_endpoint and endpoint is not None:
            model_info = model_details(endpoint)
            if model_info:
                # 更新 model_info 字典
                self.model_info.update(
                    {
                        "modelname": model_info["name"],
                        "modelVersionId": model_info["modelId"],
                        "serviceId": model_info["serviceId"],
                        "serviceUrl": model_info["url"],
                        "computer": model_info["resourceConfig"]["type"],
                        "replicasCount": model_info["resourceConfig"]["replicasCount"],
                    }
                )

    def run(self, user_num: Optional[int] = None) -> Dict[str, Any]:
        """
        run
        """
        ret: Dict[str, List[str]] = {"logfile": [], "record_dir": []}
        current_user_num = self.user_num
        html = []
        for round in range(self.rounds):
            start_time = time.time()
            round_result = super(QianfanLocustRunner, self).run(
                user_num=current_user_num
            )  # 启动本轮并发
            end_time = time.time()
            t = end_time - start_time
            ret["logfile"].append(round_result["logfile"])
            ret["record_dir"].append(round_result["record_dir"])
            html_path = round_result["performance_dir"] + "/performance_table.html"
            try:
                round_html = gen_brief(
                    round_result["record_dir"],
                    t,
                    len(self.dataset),
                    current_user_num,
                    self.worker_num,
                    self.spawn_rate,
                    self.model_type,
                    self.hyperparameters,
                )
                html.append(round_html)
            except Exception:
                traceback.print_exc()
                logger.error("在生成统计报告时发生错误.")
            if GlobalData.data["threshold_first"].value == 1:
                dataset = self.dataset.list()
                prompt = ""
                format = determine_dataset_format(dataset)
                if format == "jsonl":
                    prompt = dataset[0][0]["prompt"]
                elif format == "json":
                    prompt = dataset[0]["prompt"]
                elif format == "txt":
                    prompt = dataset[0]
                log_info = f"首token超时, 超时token: {prompt}"
                self.model_info["log_info"] = log_info
                logger.info(f"首token超时, 超时token: {prompt}")
                html_table = generate_html_table(html, self.model_info)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_table)
                return ret
            if t > self.round_latency_threshold:
                html_table = generate_html_table(html, self.model_info)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_table)
                logger.info("整句时延超时")
                return ret
            if round_html["SuccessRate"] < self.success_rate_threshold:
                html_table = generate_html_table(html, self.model_info)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_table)
                logger.info("成功率低于阈值")
                return ret
            current_user_num += self.interval if self.interval is not None else 0
        html_table = generate_html_table(html, self.model_info)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_table)
        end_time = time.time()
        logger.info(f"Log path: {ret['logfile']}")
        return ret
