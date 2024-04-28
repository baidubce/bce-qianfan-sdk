"""
QianfanLocustRunner
"""
import os
import logging

from yame.runner import LocustRunner
from qianfan_brief import gen_brief


logging.getLogger("yame.stats").setLevel(logging.INFO)


class QianfanLocustRunner(LocustRunner):
    """
    QianfanLocustRunner
    """
    locust_file = os.path.abspath(os.path.dirname(__file__)) + "/qianfan_llm_load.py"

    def __init__(self, user_num=1, worker_num=1, runtime='1m', spawn_rate=1, model=None,
                 recording=True, record_dir=None, data_file=None):
        super(QianfanLocustRunner, self).__init__(locustfile=self.locust_file,
                    user_num=user_num, worker_num=worker_num, runtime=runtime,
                    spawn_rate=spawn_rate, host=model,
                    recording=recording, record_dir=record_dir, data_file=data_file)
         
    def run(self):
        """
        run
        """
        ret = super(QianfanLocustRunner, self).run()
        gen_brief(ret["record_dir"])
        return ret


if __name__ == "__main__":
    # 开放出来的参数
    users = 1
    workers = 1
    runtime = "600s"
    spawn_rate = 128
    model = "Ernie-Bot"
    data_file = "./data/lxtest.jsonl"
    runner = QianfanLocustRunner(user_num=users, worker_num=workers, runtime=runtime,
                         spawn_rate=spawn_rate, model=model, data_file=data_file)
    runner.run()
