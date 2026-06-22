#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 兼容入口，实际流程见项目根目录 run_all.py

from pathlib import Path
import runpy


PROJECT_DIR = Path(__file__).resolve().parents[1]
runpy.run_path(str(PROJECT_DIR / "run_all.py"), run_name="__main__")
