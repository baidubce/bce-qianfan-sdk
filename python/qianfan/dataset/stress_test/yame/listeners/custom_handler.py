#!/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义统计指标（stream=True时有效）
默认行为：首Token延迟 Time to First Token
"""
import functools
import json
import os
import time
from typing import Any, Callable, List, Optional

import gevent
import locust.stats
from locust import events
from locust.env import Environment
from locust.log import greenlet_exception_logger
from locust.runners import (
    STATE_CLEANUP,
    STATE_STOPPED,
    STATE_STOPPING,
    LocalRunner,
    MasterRunner,
    WorkerRunner,
)
from locust.stats import (
    CONSOLE_STATS_INTERVAL_SEC,
    PERCENTILES_TO_REPORT,
    STATS_NAME_WIDTH,
    RequestStats,
    StatsEntry,
    StatsError,
)

from qianfan.dataset.stress_test.yame.logger import console_logger, logger


class CustomStatsCSVFileWriter(locust.stats.StatsCSVFileWriter):
    """Custom StatsCSVFileWriter using custom stats"""

    def __init__(
        self,
        stats: RequestStats,
        environment: Environment,
        percentiles_to_report: List,
        base_filepath: str,
        full_history: bool = False,
    ):
        super(CustomStatsCSVFileWriter, self).__init__(
            environment, percentiles_to_report, base_filepath, full_history
        )
        self.stats = stats

    def _requests_data_rows(self, csv_writer: locust.stats.CSVWriter) -> None:
        """Write requests csv data row, excluding header."""
        for stats_entry in locust.stats.chain(
            locust.stats.sort_stats(self.stats.entries), [self.stats.total]
        ):
            csv_writer.writerow(
                locust.stats.chain(
                    [
                        stats_entry.method,
                        stats_entry.name,
                        stats_entry.num_requests,
                        stats_entry.num_failures,
                        stats_entry.median_response_time,
                        stats_entry.avg_response_time,
                        stats_entry.min_response_time or 0,
                        stats_entry.max_response_time,
                        stats_entry.avg_content_length,
                        stats_entry.total_rps,
                        stats_entry.total_fail_per_sec,
                    ],
                    self._percentile_fields(stats_entry),
                )
            )

    def _failures_data_rows(self, csv_writer: locust.stats.CSVWriter) -> None:
        """Write failures csv data row."""
        for stats_error in locust.stats.sort_stats(self.stats.errors):
            csv_writer.writerow(
                [
                    stats_error.method,
                    stats_error.name,
                    StatsError.parse_error(stats_error.error),
                    stats_error.occurrences,
                ]
            )

    def _stats_history_data_rows(
        self, csv_writer: locust.stats.CSVWriter, now: float
    ) -> None:
        """Write CSV rows with the custom stats."""
        timestamp = int(now)
        stats_entries: List[StatsEntry] = []
        if self.full_history:
            stats_entries = locust.stats.sort_stats(self.stats.entries)

        for stats_entry in locust.stats.chain(stats_entries, [self.stats.total]):
            csv_writer.writerow(
                locust.stats.chain(
                    (
                        timestamp,
                        (
                            self.environment.runner.user_count
                            if self.environment.runner is not None
                            else 0
                        ),
                        stats_entry.method or "",
                        stats_entry.name,
                        f"{stats_entry.current_rps:2f}",
                        f"{stats_entry.current_fail_per_sec:2f}",
                    ),
                    self._percentile_fields(stats_entry, use_current=self.full_history),
                    (
                        stats_entry.num_requests,
                        stats_entry.num_failures,
                        stats_entry.median_response_time,
                        stats_entry.avg_response_time,
                        stats_entry.min_response_time or 0,
                        stats_entry.max_response_time,
                        stats_entry.avg_content_length,
                    ),
                )
            )


class CustomHandler:
    """
    stream response handler class
    """

    index = 1

    def __init__(
        self,
        name: Optional[str] = None,
        request_handler: Optional[Callable] = None,
        csv_suffix: Optional[str] = None,
    ):
        self.stats = RequestStats()
        self.id = CustomHandler.index
        CustomHandler.index += 1
        self.name = name or f"自定义统计{self.id}"
        self.listener_index = 1
        self.csv_suffix = csv_suffix or f"custom{self.id}"

        # init listeners
        if not request_handler:
            request_handler = CustomHandler.request_handler
        events.request.add_listener(functools.partial(request_handler, self.stats))
        events.report_to_master.add_listener(self.on_report_to_master)
        events.worker_report.add_listener(self.on_worker_report)
        # events.quitting.add_listener(self.test_stop_listener)
        events.test_stop.add_listener(self.test_stop_listener)
        events.test_start.add_listener(self.test_start_handler)

    def add_listener(
        self,
        name: Optional[str] = None,
        condition_handler: Optional[Callable] = None,
        thresholds: Optional[float] = None,
    ) -> Any:
        """
        添加阈值监听器
        :param name: 监听器名称
        :param condition_handler: 状态判断方法
        :param thresholds: 阈值

        handler方法说明：
            handler(stats, thresholds)
            参数：
                stats       locust.stats.RequestStats
                thresholds  阈值
            返回：bool，当返回True时，停止压测任务
        """
        listener_name = name or f"自定义监听器{self.listener_index}"

        def default_handler(stats: RequestStats, thresholds: Optional[float]) -> bool:
            """默认handler"""
            return stats.total.avg_response_time > thresholds

        if not condition_handler:
            condition_handler = default_handler

        def thresholds_listener(environment: Environment, **kwargs: Any) -> None:
            """
            启动异步greenlet，以检查阈值
            """
            # don't run this on workers, we only care about the aggregated numbers
            if isinstance(environment.runner, MasterRunner) or isinstance(
                environment.runner, LocalRunner
            ):
                gevent.spawn(thresholds_checker, environment).link_exception(
                    greenlet_exception_logger(logger)
                )

        def thresholds_checker(environment: Environment) -> None:
            """
            检查指标，超过阈值退出
            """
            logger.info(
                f"{self.name} {listener_name} listener starts: thresholds={thresholds}"
            )
            time.sleep(0.1)
            assert environment.runner is not None
            while environment.runner.state not in [
                STATE_STOPPING,
                STATE_STOPPED,
                STATE_CLEANUP,
            ]:
                time.sleep(1)
                if condition_handler(self.stats, thresholds):
                    if environment.web_ui:
                        logger.warning(
                            f"{self.name} {listener_name} "
                            "满足阈值条件(thresholds={thresholds}),"
                            " stopping."
                        )
                        environment.runner.stop()
                    else:
                        logger.warning(
                            f"{self.name} {listener_name} "
                            "满足阈值条件(thresholds={thresholds}),"
                            " quitting."
                        )
                        environment.runner.quit()
                    return

        events.test_start.add_listener(thresholds_listener)
        self.listener_index += 1
        return self

    def on_report_to_master(self, client_id: str, data: dict) -> None:
        """
        当为worker runner时，需要将收集到的自定义数据上报给master runner做汇总
        master runner接受到data时，再从其中解出自定义数据做汇总
        注意：自定义数据的key 不能使用stats、status_total、errors，
        这是locust原生数据占用的结构.
        """
        data[f"custom_stats_{self.id}"] = self.stats.serialize_stats()
        data[f"custom_stats_total_{self.id}"] = self.stats.total.get_stripped_report()
        data[f"custom_errors_{self.id}"] = self.stats.serialize_errors()
        self.stats.errors = {}

    def on_worker_report(self, client_id: str, data: dict) -> None:
        """
        worker runner通过data上传stats数据，
        data包含自定义数据（通过on_report_to_master传入）
        master runner接受到data后将其中的自定义数据与自己本地数据做merge
        """
        for stats_data in data[f"custom_stats_{self.id}"]:
            entry = StatsEntry.unserialize(stats_data)
            request_key = (entry.name, entry.method)
            if request_key not in self.stats.entries:
                self.stats.entries[request_key] = StatsEntry(
                    self.stats, entry.name, entry.method, use_response_times_cache=True
                )
            self.stats.entries[request_key].extend(entry)

        for error_key, error in data[f"custom_errors_{self.id}"].items():
            if error_key not in self.stats.errors:
                self.stats.errors[error_key] = StatsError.unserialize(error)
            else:
                self.stats.errors[error_key].occurrences += error["occurrences"]

        self.stats.total.extend(
            StatsEntry.unserialize(data[f"custom_stats_total_{self.id}"])
        )

    def test_start_handler(self, environment: Environment, **kwargs: Any) -> None:
        """
        启动异步greenlet，定时打印stats
        """
        # reset statistics
        self.stats.reset_all()
        # don't run this on workers, we only care about the aggregated numbers
        if isinstance(environment.runner, MasterRunner) or isinstance(
            environment.runner, LocalRunner
        ):
            # init csv writer
            options = environment.parsed_options
            if options and options.csv_prefix:
                base_csv_file = os.path.basename(options.csv_prefix)
                base_csv_dir = options.csv_prefix[: -len(base_csv_file)]
                if not os.path.exists(base_csv_dir) and len(base_csv_dir) != 0:
                    os.makedirs(base_csv_dir)
                stats_csv_writer = CustomStatsCSVFileWriter(
                    self.stats,
                    environment,
                    PERCENTILES_TO_REPORT,
                    options.csv_prefix + f"_{self.csv_suffix}",
                    options.stats_history_enabled,
                )
                # start csv writer gevent
                gevent.spawn(stats_csv_writer.stats_writer).link_exception(
                    greenlet_exception_logger(logger)
                )
            # start stats printer
            if (
                options
                and not options.only_summary
                and (options.print_stats or (options.headless and not options.worker))
            ):
                gevent.spawn(self.stats_printer, environment).link_exception(
                    greenlet_exception_logger(logger)
                )

    def print_stats_json(self) -> str:
        """
        print self.stats.serialize_stats()
        reference: locust.stats.print_stats_json
        """
        content = (
            f"Summary: {self.name} [stats (json)]\n"
            + json.dumps(self.stats.serialize_stats(), indent=4)
            + "\n"
        )
        console_logger.debug(content)
        return content

    def print_stats(self, current: bool = True) -> str:
        """print self.stats summary"""
        content = (
            ("" if current else "Summary: ")
            + self.name
            + " [stats]\n"
            + "\n".join(locust.stats.get_stats_summary(self.stats, current=current))
            + "\n"
        )
        console_logger.debug(content)
        return content

    def print_percentile_stats(self) -> str:
        """print self.stats percentile"""
        percentile_stats = locust.stats.get_percentile_stats_summary(self.stats)
        percentile_stats[0] = f"Summary: {self.name} [percentiles (approximated)]"
        content = "\n".join(percentile_stats) + "\n"
        console_logger.debug(content)
        return content

    def get_error_report_summary(self) -> list:
        """get custom error report"""
        summary = [
            f'Summary: {self.name} [report (from "fails")]',
            "%-18s|%-18s %-18s %-80s"
            % ("count", "count/fails", "count/total", "catalog"),
        ]
        separator = (
            f'{"-" * 18}|{"-" * 18}|{"-" * 18}|{"-" * ((80 + STATS_NAME_WIDTH) - 50)}'
        )
        summary.append(separator)
        for error in self.stats.errors.values():
            summary.append(
                "%-18i %-18s %-18s %-100s"
                % (
                    error.occurrences,
                    "%-.2f%%"
                    % (float(error.occurrences) / self.stats.total.num_failures * 100),
                    "%-.2f%%"
                    % (
                        float(error.occurrences)
                        / (
                            self.stats.total.num_requests
                            + self.stats.total.num_failures
                        )
                        * 100
                    ),
                    error.to_name(),
                )
            )
        summary.append(separator)
        summary.append("")
        return summary

    def print_error_report(self) -> str:
        """print self.status error report"""
        if self.stats.errors:
            content = "\n".join(self.get_error_report_summary()) + "\n"
            console_logger.debug(content)
        else:
            content = ""
        return content

    def start_stats_printer_gevent(
        self, environment: Environment, **kwargs: Any
    ) -> None:
        """
        启动异步greenlet，定时打印stats
        """
        # don't run this on workers, we only care about the aggregated numbers
        if isinstance(environment.runner, MasterRunner) or isinstance(
            environment.runner, LocalRunner
        ):
            gevent.spawn(self.stats_printer, environment).link_exception(
                greenlet_exception_logger(logger)
            )

    def stats_printer(self, environment: Environment) -> None:
        """
        定时打印stats
        """
        assert environment.runner is not None
        while environment.runner.state not in [
            STATE_STOPPING,
            STATE_STOPPED,
            STATE_CLEANUP,
        ]:
            self.print_stats()
            gevent.sleep(CONSOLE_STATS_INTERVAL_SEC)

    @staticmethod
    def request_handler(
        stats: RequestStats,
        request_type: Any,
        name: str,
        response_time: float,
        response_length: int,
        exception: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """
        每个请求均会调用，用于向统计表注册数据
        (1) 注册1个记录：stats.log_request(type, name, time, length)
        (2) 标记为失败或某种分类：stats.log_error(type, name, exc)
            其中exc为错误或分类message，最终会按type+name+exc分类统计
        """
        if "ttft" in kwargs:
            stats.log_request(request_type, name, kwargs["ttft"], response_length)
        else:
            stats.log_request(request_type, name, 0, response_length)
            stats.log_error(request_type, name, "未找到ttft首token延迟")

    def test_stop_listener(self, environment: Environment) -> None:
        """
        测试结束时，通过这个event将存储在global data中的first response stats打印到终端
        """
        if isinstance(environment.runner, WorkerRunner):
            return

        # print final statistics of self.stats
        if (
            hasattr(environment.parsed_options, "json")
            and environment.parsed_options
            and environment.parsed_options.json
        ):
            log_content = self.print_stats_json()
        else:
            log_content = self.print_stats(current=False)
            log_content += self.print_percentile_stats()
            log_content += self.print_error_report()

        # output final statistics of self.stats to logfile
        if (
            environment.parsed_options
            and environment.parsed_options.logfile
            and log_content
        ):
            output_folder = os.path.dirname(environment.parsed_options.logfile)
            with open(
                os.path.join(output_folder, f"{self.csv_suffix}_statistics.log"), "w"
            ) as fs:
                fs.write(log_content)
