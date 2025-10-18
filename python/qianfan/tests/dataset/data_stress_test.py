import os
import unittest

from qianfan.dataset.dataset import Dataset


class StressTestCase(unittest.TestCase):
    def setUp(self):
        self.path = "text"
        with open(self.path, "w+") as f:
            f.write("""人体最重要的有机物质是什么？
化学中PH值用来表示什么？
如何看待第一次世界大战？
如何看待第二次世界大战？
第一个登上月球的人是谁？""")

        os.environ["QIANFAN_ENABLE_STRESS_TEST"] = "true"

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        os.environ.pop("QIANFAN_ENABLE_STRESS_TEST", None)

    def test_stress(self):
        ds = Dataset.load(data_file=self.path)

        ds.stress_test(
            workers=60,
            users=60,
            model="ERNIE-4.0-8K-Latest",
        )

    def test_multi_stress(self):
        ds = Dataset.load(data_file=self.path)
        ds.multi_stress_test(
            origin_users=2,
            workers=2,
            spawn_rate=2,
            model="ERNIE-4.0-8K-Latest",
            runtime="10s",
            rounds=2,
            interval=2,
            first_latency_threshold=2,
            round_latency_threshold=30,
            success_rate_threshold=0.8,
        )


if __name__ == "__main__":
    unittest.main()
