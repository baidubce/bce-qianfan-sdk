#!/usr/bin/env python
# coding=utf-8
"""
build parser
"""

from locust.argument_parser import LocustArgumentParser
from yame.runner import LocustRunner


def build_root_parser():
    """
    build cli root parser
    """
    parser = LocustArgumentParser()
    sub_parsers = parser.add_subparsers(dest='action', required=True)

    headless_parser = sub_parsers.add_parser('headless', help="locust禁用web interface，命令行方式启动")
    build_headless_parser(headless_parser)

    return parser


def build_statistics_options(parser):
    """
    build statistics/logging options group
    """
    group = parser.add_argument_group(
        'yame-plugins: 统计/日志设置参数',
        '每个任务默认自动生成"record/<datetime>"目录（可通过--record-dir修改），'
        '自动在该目录下保存--logfile=run.log，--html=report.html，--csv=statistics；可再通过以下参数修改.')
    group.add_argument('--record-dir', help='设置报告目录')
    group.add_argument('-L', '--loglevel', help='日志级别，默认INFO. 支持：DEBUG/INFO/WARNING/ERROR/CRITICAL.')
    group.add_argument('--logfile', help='日志文件路径')
    group.add_argument('--html', metavar='HTML_FILE', help='locust html报告路径')
    group.add_argument('--csv', metavar='CSV_PREFIX',
                       help='Store current request stats to files in CSV format. '
                            'Setting this option will generate three files: [CSV_PREFIX]_stats.csv, '
                            '[CSV_PREFIX]_stats_history.csv and [CSV_PREFIX]_failures.csv')
    group.add_argument('--csv-full-history', action='store_true',
                       help='Store each stats entry in CSV format to _stats_history.csv file. '
                            'You must also specify the "--csv" argument to enable this.')
    group.add_argument('--recording', action='store_true',
                       help='recording参数已废弃，默认打开报告/日志记录；保留此参数仅用于兼容旧版命令.')
    group.add_argument('--json', action='store_true', help='Prints the final stats in JSON format to stdout.')
    group.add_argument('--only-summary', action='store_true',
                       help='Disable periodic printing of request stats during --headless run')


def build_headless_parser(parser):
    """
    build headless parser
    """
    group = parser.add_argument_group(title='headless模式参数')
    group.add_argument('-W', '--workers', help='worker数量(提升发压能力)(default=1)', default=1, type=int)
    group.add_argument('-U', '--users', help='user数量(并发数)(default=1)', default=1, type=int)
    group.add_argument('-t', '--runtime', help='压测时长(default=1m)', default='1m')
    group.add_argument('-S', '--spawn-rate', help='user增长速率', type=int)
    group.add_argument('-H', '--host', help='访问的host地址')
    group.add_argument('-f', '--locustfile', help='locustfile文件路径', required=True)

    build_statistics_options(parser)
    parser.set_defaults(func=run_locust_job_with_headless)


def run_locust_job_with_headless(args):
    """
    run locust with headless argument
    """
    runner = LocustRunner(locustfile=args.locustfile,
                          user_num=args.users, worker_num=args.workers, runtime=args.runtime,
                          spawn_rate=args.spawn_rate, host=args.host, enable_web=False,
                          recording=True, record_dir=args.record_dir,
                          loglevel=args.loglevel, logfile=args.logfile, report=args.html,
                          csv_prefix=args.csv, csv_full_history=args.csv_full_history,
                          json=args.json, only_summary=args.only_summary)
    runner.run()
