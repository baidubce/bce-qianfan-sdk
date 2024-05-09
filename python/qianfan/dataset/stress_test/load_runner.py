"""
QianfanLocustRunner
"""
import logging
import os
from typing import Any, Dict, Optional

from qianfan.dataset import Dataset
from qianfan.dataset.stress_test.load_statistics import gen_brief
from qianfan.dataset.stress_test.yame.runner import LocustRunner

logger = logging.getLogger("yame.stats")
logger.setLevel(logging.INFO)


class QianfanLocustRunner(LocustRunner):
    """
    QianfanLocustRunner
    """

    locust_file = os.path.abspath(os.path.dirname(__file__)) + "/qianfan_llm_load.py"

    def __init__(
        self,
        model: str,
        dataset: Dataset,
        model_type: str = "ChatCompletion",
        user_num: int = 1,
        worker_num: int = 1,
        runtime: str = "1m",
        spawn_rate: int = 1,
        recording: bool = True,
        record_dir: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ):
        super(QianfanLocustRunner, self).__init__(
            locustfile=self.locust_file,
            user_num=user_num,
            worker_num=worker_num,
            runtime=runtime,
            spawn_rate=spawn_rate,
            host=model,
            recording=recording,
            record_dir=record_dir,
            dataset=dataset,
            model_type=model_type,
            hyperparameters=hyperparameters,
        )

    def run(self) -> Dict[str, Any]:
        """
        run
        """
        ret = super(QianfanLocustRunner, self).run()
        if ret["exitcode"] == 0:
            gen_brief(ret["record_dir"])
        else:
            logger.error("Task error! Please check the log.")
        return ret
