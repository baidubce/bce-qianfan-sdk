# -- encoding: utf-8 --


"""
brief.py
"""
import html
import logging
from typing import Any, Dict, List

logger = logging.getLogger("yame.runner")


def get_qps(path: str) -> float:
    """
    get_duration
    """
    with open(path) as fd:
        for line in fd:
            if line.startswith("Type"):
                continue
            line_splits = line.split(",")
            qps = float(line_splits[-13]) - float(line_splits[-12])
            break
        return qps


def get_statistics(path: str) -> List[float]:
    """
    get_statistics
    """
    with open(path) as fd:
        for line in fd:
            if line.startswith("Type"):
                continue
            line_splits = line.split(",")
            lat_avg = -1.0 if line_splits[5] == "N/A" else float(line_splits[5])
            lat_min = -1.0 if line_splits[6] == "N/A" else float(line_splits[6])
            lat_max = -1.0 if line_splits[7] == "N/A" else float(line_splits[7])
            lat_50p = -1.0 if line_splits[11] == "N/A" else float(line_splits[11])
            lat_80p = -1.0 if line_splits[14] == "N/A" else float(line_splits[14])
            lat_90p = -1.0 if line_splits[14] == "N/A" else float(line_splits[15])
            lat_95p = -1.0 if line_splits[14] == "N/A" else float(line_splits[16])
            lat_99p = -1.0 if line_splits[14] == "N/A" else float(line_splits[17])
            total_count = int(line_splits[2])
            failure_count = int(line_splits[3])
            total_time = float(line_splits[2]) * float(line_splits[5])
            break
    return [
        lat_avg,
        lat_min,
        lat_max,
        lat_50p,
        lat_80p,
        lat_90p,
        lat_95p,
        lat_99p,
        total_count,
        failure_count,
        total_time,
    ]


def gen_brief(
    report_dir: str,
    time: float,
    count: int,
    user_num: int,
    worker_num: int,
    spawn_rate: int,
    model_type: str,
    hyperparameters: Any,
) -> Dict[str, Any]:
    """
    gen_brief
    """
    qps = get_qps(report_dir + "/statistics_stats.csv")
    lat_tuple = get_statistics(report_dir + "/statistics_total_latency_stats.csv")
    first_lat_tuple = get_statistics(
        report_dir + "/statistics_first_token_latency_stats.csv"
    )
    interval_lat_tuple = get_statistics(
        report_dir + "/statistics_interval_latency_stats.csv"
    )
    input_tk_tuple = get_statistics(report_dir + "/statistics_input_tokens_stats.csv")
    output_tk_tuple = get_statistics(report_dir + "/statistics_output_tokens_stats.csv")
    input_str_length_tuple = get_statistics(
        report_dir + "/statistics_input_str_length_stats.csv"
    )
    output_str_length_tuple = get_statistics(
        report_dir + "/statistics_output_str_length_stats.csv"
    )
    total_count = get_statistics(report_dir + "/statistics_stats.csv")[8]
    failure_count = get_statistics(report_dir + "/statistics_stats.csv")[9]
    success_count = total_count - failure_count
    success_rate = (
        0 if total_count == 0 else round(success_count / total_count * 100, 2)
    )
    text = (
        "Load Test Statistics\n"
        + "user_num: %s\n" % user_num
        + "worker_num: %s\n" % worker_num
        + "spawn_rate: %s\n" % spawn_rate
        + "model_type: %s\n" % model_type
        + "hyperparameters: %s\n" % hyperparameters
        + "QPS: %s\n" % round(qps, 2)
        + "Latency Avg: %s\n" % round(lat_tuple[0] / 1000, 6)
        + "Latency Min: %s\n" % round(lat_tuple[1] / 1000, 6)
        + "Latency Max: %s\n" % round(lat_tuple[2] / 1000, 6)
        + "Latency 50%%: %s\n" % round(lat_tuple[3] / 1000, 6)
        + "Latency 80%%: %s\n" % round(lat_tuple[4] / 1000, 6)
        + "Latency 90%%: %s\n" % round(lat_tuple[5] / 1000, 6)
        + "Latency 95%%: %s\n" % round(lat_tuple[6] / 1000, 6)
        + "Latency 99%%: %s\n" % round(lat_tuple[7] / 1000, 6)
        + "FirstTokenLatency Avg: %s\n" % round(first_lat_tuple[0] / 1000, 6)
        + "FirstTokenLatency Min: %s\n" % round(first_lat_tuple[1] / 1000, 6)
        + "FirstTokenLatency Max: %s\n" % round(first_lat_tuple[2] / 1000, 6)
        + "FirstTokenLatency 50%%: %s\n" % round(first_lat_tuple[3] / 1000, 6)
        + "FirstTokenLatency 80%%: %s\n" % round(first_lat_tuple[4] / 1000, 6)
        + "FirstTokenLatency 90%%: %s\n" % round(first_lat_tuple[5] / 1000, 6)
        + "FirstTokenLatency 95%%: %s\n" % round(first_lat_tuple[6] / 1000, 6)
        + "FirstTokenLatency 99%%: %s\n" % round(first_lat_tuple[7] / 1000, 6)
        + "IntervalLatency Avg: %s\n" % round(interval_lat_tuple[0] / 1000, 6)
        + "IntervalLatency Min: %s\n" % round(interval_lat_tuple[1] / 1000, 6)
        + "IntervalLatency Max: %s\n" % round(interval_lat_tuple[2] / 1000, 6)
        + "IntervalLatency 50%%: %s\n" % round(interval_lat_tuple[3] / 1000, 6)
        + "IntervalLatency 80%%: %s\n" % round(interval_lat_tuple[4] / 1000, 6)
        + "IntervalLatency 90%%: %s\n" % round(interval_lat_tuple[5] / 1000, 6)
        + "IntervalLatency 95%%: %s\n" % round(interval_lat_tuple[6] / 1000, 6)
        + "IntervalLatency 99%%: %s\n" % round(interval_lat_tuple[7] / 1000, 6)
        + "InputTokens Avg: %s\n" % round(input_tk_tuple[0], 2)
        + "OutputTokens Avg: %s\n" % round(output_tk_tuple[0], 2)
        + "TotalInputTokens: %s\n" % round(input_tk_tuple[0] * success_count, 2)
        + "TotalOutputTokens: %s\n" % round(output_tk_tuple[0] * success_count, 2)
        + "InputStringLength Avg :%s\n" % round(input_str_length_tuple[0], 2)
        + "OutputStringLength Avg :%s\n" % round(output_str_length_tuple[0], 2)
        + "TotalInputStringLength: %s\n"
        % round(input_str_length_tuple[0] * success_count, 2)
        + "TotalOutputStringLength: %s\n"
        % round(output_str_length_tuple[0] * success_count, 2)
        + "OutputTokensPerSecond: %s\n"
        % (
            round(output_tk_tuple[0] / (lat_tuple[0] / 1000), 2)
            if lat_tuple[0] != 0
            else 0
        )
        + "OutputStringLengthPerSecond: %s\n"
        % (
            round(output_str_length_tuple[0] / (lat_tuple[0] / 1000), 2)
            if lat_tuple[0] != 0
            else 0
        )
        + "SendQuery: %s\n" % round(total_count, 2)
        + "SuccessQuery: %s\n" % round(success_count, 2)
        + "FailureQuery: %s\n" % round(failure_count, 2)
        + "TotalQuery: %s\n" % round(count, 2)
        + "TotalTime: %s\n" % round(time, 2)
        + "SuccessRate: %s%%" % success_rate
    )
    statistics = {
        "QPS": round(qps, 2),
        "latency_avg": round(lat_tuple[0] / 1000, 6),
        "latency_min": round(lat_tuple[1] / 1000, 6),
        "latency_max": round(lat_tuple[2] / 1000, 6),
        "latency_50%": round(lat_tuple[3] / 1000, 6),
        "latency_80%": round(lat_tuple[4] / 1000, 6),
        "latency_90%": round(lat_tuple[5] / 1000, 6),
        "latency_95%": round(lat_tuple[6] / 1000, 6),
        "latency_99%": round(lat_tuple[7] / 1000, 6),
        "FirstTokenLatency_avg": round(first_lat_tuple[0] / 1000, 6),
        "FirstTokenLatency_min": round(first_lat_tuple[1] / 1000, 6),
        "FirstTokenLatency_max": round(first_lat_tuple[2] / 1000, 6),
        "FirstTokenLatency_50%": round(first_lat_tuple[3] / 1000, 6),
        "FirstTokenLatency_80%": round(first_lat_tuple[4] / 1000, 6),
        "FirstTokenLatency_90%": round(first_lat_tuple[5] / 1000, 6),
        "FirstTokenLatency_95%": round(first_lat_tuple[6] / 1000, 6),
        "FirstTokenLatency_99%": round(first_lat_tuple[7] / 1000, 6),
        "IntervalLatency_avg": round(interval_lat_tuple[0] / 1000, 6),
        "IntervalLatency_min": round(interval_lat_tuple[1] / 1000, 6),
        "IntervalLatency_max": round(interval_lat_tuple[2] / 1000, 6),
        "IntervalLatency_50%": round(interval_lat_tuple[3] / 1000, 6),
        "IntervalLatency_80%": round(interval_lat_tuple[4] / 1000, 6),
        "IntervalLatency_90%": round(interval_lat_tuple[5] / 1000, 6),
        "IntervalLatency_95%": round(interval_lat_tuple[6] / 1000, 6),
        "IntervalLatency_99%": round(interval_lat_tuple[7] / 1000, 6),
        "InputTokens_avg": round(input_tk_tuple[0], 2),
        "OutputTokens_avg": round(output_tk_tuple[0], 2),
        "InputStringLength_avg": round(input_str_length_tuple[0], 2),
        "OutputStringLength_avg": round(output_str_length_tuple[0], 2),
        "OutputTokensPerSecond": (
            round(output_tk_tuple[0] / (lat_tuple[0] / 1000), 2)
            if lat_tuple[0] != 0
            else 0
        ),
        "OutputStringLengthPerSecond": (
            round(output_str_length_tuple[0] / (lat_tuple[0] / 1000), 2)
            if lat_tuple[0] != 0
            else 0
        ),
        "TotalTime": round(time, 2),
        "SuccessRate": success_rate,
        "concurrency": user_num,
    }

    logger.info(text)
    return statistics


def generate_html_table(data_rows: Any, model_info: Any) -> str:
    """
    generate_html_table
    """
    css_styles = """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
        }
        .info-section {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .info-section h2 {
            margin-top: 0;
            color: #34495e;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #2c3e50;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e9ecef;
        }
    """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Performance Test Report</title>
        <style>
        {css_styles}
        </style>
    </head>
    <body>
        <h1>Performance Test Report</h1>
        
        <div class="info-section">
            <h2>Model Information</h2>
            <p><strong>Service name:</strong> {model_info['modelname']}</p>
            <p><strong>Model Version:</strong> {model_info['modelVersionId']}</p>
            <p><strong>serviceId:</strong> {model_info['serviceId']}</p>
            <p><strong>serviceUrl:</strong> {model_info['serviceUrl']}</p>
            <p><strong>GPU:</strong> {model_info['computer']}</p>
            <p><strong>replicasCount:</strong> {model_info['replicasCount']}</p>
        </div>
        
        <div class="info-section">
            <h2>Stress Test Configuration</h2>
            <p><strong>Origin User Number:</strong> {model_info['origin_user_num']}</p>
            <p><strong>Worker Number:</strong> {model_info['worker']}</p>
            <p><strong>Spawn Rate:</strong> {model_info['spawn_rate']}</p>
            <p><strong>Rounds:</strong> {model_info['rounds']}</p>
            <p><strong>Interval:</strong> {model_info['interval']}</p>
            <p><strong>Hyperparameters:</strong> {model_info['hyperparameters']}</p>
        </div>

        <div class="log-info">
            <h2>Log Information</h2>
            <p><strong>First Token Latency log:</strong> {model_info["log_info"]}</p>
        </div>
        
        <h2>Performance Results</h2>
    """

    columns = [
        "并发",
        "QPS",
        "Latency Avg",
        "Latency Min",
        "Latency Max",
        "Latency 50",
        "Latency 80",
        "Latency 90",
        "Latency 95",
        "Latency 99",
        "FirstTokenLatency Avg",
        "FirstTokenLatency Min",
        "FirstTokenLatency Max",
        "FirstTokenLatency 50",
        "FirstTokenLatency 80",
        "FirstTokenLatency 90",
        "FirstTokenLatency 95",
        "FirstTokenLatency 99",
        "IntervalLatency Avg",
        "IntervalLatency Min",
        "IntervalLatency Max",
        "IntervalLatency 50",
        "IntervalLatency 80",
        "IntervalLatency 90",
        "IntervalLatency 95",
        "IntervalLatency 99",
        "InputTokens avg",
        "OutputTokens avg",
        "InputStringLength avg",
        "OutputStringLength avg",
        "OutputTokensPerSecond",
        "OutputStringLengthPerSecond",
        "SuccessRate",
    ]

    html_content += "<table>\n"

    # Generate table header
    html_content += "  <tr>\n"
    for column in columns:
        html_content += f"    <th>{html.escape(column)}</th>\n"
    html_content += "  </tr>\n"

    # Generate table rows
    for row in data_rows:
        html_content += "  <tr>\n"
        for column in columns:
            if column == "并发":
                value = row.get("concurrency", "")
            elif column == "QPS":
                value = row.get("QPS", "")
            elif column == "Latency Avg":
                value = row.get("latency_avg", "")
            elif column == "Latency Min":
                value = row.get("latency_min", "")
            elif column == "Latency Max":
                value = row.get("latency_max", "")
            elif column == "Latency 50":
                value = row.get("latency_50%", "")
            elif column == "Latency 80":
                value = row.get("latency_80%", "")
            elif column == "Latency 90":
                value = row.get("latency_90%", "")
            elif column == "Latency 95":
                value = row.get("latency_95%", "")
            elif column == "Latency 99":
                value = row.get("latency_99%", "")
            elif column == "FirstTokenLatency Avg":
                value = row.get("FirstTokenLatency_avg", "")
            elif column == "FirstTokenLatency Min":
                value = row.get("FirstTokenLatency_min", "")
            elif column == "FirstTokenLatency Max":
                value = row.get("FirstTokenLatency_max", "")
            elif column == "FirstTokenLatency 50":
                value = row.get("FirstTokenLatency_50%", "")
            elif column == "FirstTokenLatency 80":
                value = row.get("FirstTokenLatency_80%", "")
            elif column == "FirstTokenLatency 90":
                value = row.get("FirstTokenLatency_90%", "")
            elif column == "FirstTokenLatency 95":
                value = row.get("FirstTokenLatency_95%", "")
            elif column == "FirstTokenLatency 99":
                value = row.get("FirstTokenLatency_99%", "")
            elif column == "IntervalLatency Avg":
                value = row.get("IntervalLatency_avg", "")
            elif column == "IntervalLatency Min":
                value = row.get("IntervalLatency_min", "")
            elif column == "IntervalLatency Max":
                value = row.get("IntervalLatency_max", "")
            elif column == "IntervalLatency 50":
                value = row.get("IntervalLatency_50%", "")
            elif column == "IntervalLatency 80":
                value = row.get("IntervalLatency_80%", "")
            elif column == "IntervalLatency 90":
                value = row.get("IntervalLatency_90%", "")
            elif column == "IntervalLatency 95":
                value = row.get("IntervalLatency_95%", "")
            elif column == "IntervalLatency 99":
                value = row.get("IntervalLatency_99%", "")
            elif column == "InputTokens avg":
                value = row.get("InputTokens_avg", "")
            elif column == "OutputTokens avg":
                value = row.get("OutputTokens_avg", "")
            elif column == "InputStringLength avg":
                value = row.get("InputStringLength_avg", "")
            elif column == "OutputStringLength avg":
                value = row.get("OutputStringLength_avg", "")
            elif column == "OutputTokensPerSecond":
                value = row.get("OutputTokensPerSecond", "")
            elif column == "OutputStringLengthPerSecond":
                value = row.get("OutputStringLengthPerSecond", "")
            elif column == "SuccessRate":
                value = row.get("SuccessRate", "")
            else:
                value = ""

            html_content += f"    <td>{html.escape(str(value))}</td>\n"
        html_content += "  </tr>\n"

    html_content += """
        </table>
    </body>
    </html>
    """
    return html_content
