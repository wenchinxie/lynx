#!/bin/bash
# Simple script to run storage tests

cd /home/hanson/lynx
source .venv/bin/activate
python -m pytest tests/unit/test_storage.py -v
