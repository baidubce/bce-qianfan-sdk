"""
QianfanLocustRunner
"""
import logging
import os
import traceback
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
        )

    def run(self) -> Dict[str, Any]:
        """
        run
        """
        ret = super(QianfanLocustRunner, self).run()
        logger.info("Log path: %s" % ret["logfile"])
        try:
            gen_brief(ret["record_dir"])
        except Exception:
            traceback.print_exc()
            logger.error("Error happens when statisticizing.")
        return ret
