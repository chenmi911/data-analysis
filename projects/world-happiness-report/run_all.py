#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 项目主入口

from etl import main as run_etl
from analyse import main as run_analyse
from visualize import main as run_visualize


def main() -> None:
    run_etl()
    run_analyse()
    run_visualize()


if __name__ == "__main__":
    main()
