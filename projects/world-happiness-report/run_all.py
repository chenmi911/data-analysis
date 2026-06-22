#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 项目主入口

from pathlib import Path
import runpy


PROJECT_DIR = Path(__file__).resolve().parent

runpy.run_path(str(PROJECT_DIR / "etl.py"), run_name="__main__")
runpy.run_path(str(PROJECT_DIR / "analyse.py"), run_name="__main__")
runpy.run_path(str(PROJECT_DIR / "visualize.py"), run_name="__main__")
