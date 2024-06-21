# -- encoding: utf-8 --
"""
brief.py
"""
import logging
import sys
from typing import List

logger = logging.getLogger("yame.runner")


def get_qps_and_rate(path: str) -> List[float]:
    """
    get_duration
    """
    with open(path) as fd:
        for line in fd:
            if line.startswith("Type"):
                continue
            line_splits = line.split(",")
            qps = float(line_splits[-13])
            total_count = int(line_splits[2])
            error_count = int(line_splits[3])
            break
        if total_count != 0:
            rate = (total_count - error_count) / total_count * 100
        else:
            rate = 0
        return [qps, rate]


def get_statistics(path: str) -> List[float]:
    """
    get_statistics
    """
    with open(path) as fd:
        for line in fd:
            if line.startswith("Type"):
                continue
            line_splits = line.split(",")
            lat_avg = float(line_splits[5])
            lat_min = float(line_splits[6])
            lat_max = float(line_splits[7])
            lat_50p = float(line_splits[4])
            lat_80p = float(line_splits[-8])
            break
    return [lat_avg, lat_min, lat_max, lat_50p, lat_80p]


def gen_brief(report_dir: str) -> None:
    """
    gen_brief
    """
    qps, rate = get_qps_and_rate(report_dir + "/statistics_stats.csv")
    lat_tuple = get_statistics(report_dir + "/statistics_stats.csv")
    first_lat_tuple = get_statistics(
        report_dir + "/statistics_first_token_latency_stats.csv"
    )
    input_tk_tuple = get_statistics(report_dir + "/statistics_input_tokens_stats.csv")
    output_tk_tuple = get_statistics(report_dir + "/statistics_output_tokens_stats.csv")

    text = (
        "Load Test Statistics\n"
        + "QPS: %s\n" % round(qps, 2)
        + "Latency Avg: %s\n" % round(lat_tuple[0] / 1000, 2)
        + "Latency Min: %s\n" % round(lat_tuple[1] / 1000, 2)
        + "Latency Max: %s\n" % round(lat_tuple[2] / 1000, 2)
        + "Latency 50%%: %s\n" % round(lat_tuple[3] / 1000, 2)
        + "Latency 80%%: %s\n" % round(lat_tuple[4] / 1000, 2)
        + "FirstTokenLatency Avg: %s\n" % round(first_lat_tuple[0] / 1000, 2)
        + "FirstTokenLatency Min: %s\n" % round(first_lat_tuple[1] / 1000, 2)
        + "FirstTokenLatency Max: %s\n" % round(first_lat_tuple[2] / 1000, 2)
        + "FirstTokenLatency 50%%: %s\n" % round(first_lat_tuple[3] / 1000, 2)
        + "FirstTokenLatency 80%%: %s\n" % round(first_lat_tuple[4] / 1000, 2)
        + "InputTokens Avg: %s\n" % round(input_tk_tuple[0], 2)
        + "OutputTokens Avg: %s\n" % round(output_tk_tuple[0], 2)
        + "SuccessRate: %s%%" % round(rate, 2)
    )
    logger.info(text)


if __name__ == "__main__":
    report_dir = sys.argv[1]
    gen_brief(report_dir)
