"""
QianfanLocustRunner
"""
import logging
import os
import sys

logger = logging.getLogger("yame.stats")
logger.setLevel(logging.INFO)

from qianfan.dataset.stress_test.load_statistics import gen_brief
from qianfan.dataset.stress_test.yame.runner import LocustRunner


class QianfanLocustRunner(LocustRunner):
    """
    QianfanLocustRunner
    """

    locust_file = os.path.abspath(os.path.dirname(__file__)) + "/qianfan_llm_load.py"

    def __init__(
        self,
        user_num=1,
        worker_num=1,
        runtime="1m",
        spawn_rate=1,
        model=None,
        recording=True,
        record_dir=None,
        dataset=None,
        data_column="prompt",
        hyperparameters=None,
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
            data_column=data_column,
            hyperparameters=hyperparameters,
        )

    def run(self):
        """
        run
        """
        ret = super(QianfanLocustRunner, self).run()
        if ret["exitcode"] == 0:
            gen_brief(ret["record_dir"])
        else:
            logger.error("Task error! Please check the log.")
        return ret
