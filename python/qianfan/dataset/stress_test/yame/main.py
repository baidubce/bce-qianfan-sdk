#!/usr/bin/env python
# coding=utf-8
"""
Load Runner Main
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from yame.parser import build_root_parser


def main():
    """
    Main Func
    """
    parser = build_root_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
