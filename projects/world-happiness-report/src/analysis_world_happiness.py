#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 兼容入口，实际流程见项目根目录 run_all.py

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from run_all import main  # noqa: E402


if __name__ == "__main__":
    main()
