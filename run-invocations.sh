#!/bin/bash
set -e

echo "---------- run-invocations.sh -----------"
echo "1/5: Clean ------------------------------"
uv run inv clean
echo "2/5: Format code ------------------------"
uv run inv format
echo "3/5: Test -------------------------------"
uv run inv tests
echo "4/5: Lint -------------------------------"
uv run inv lint
echo "5/5: Typecheck (mypy) -------------------"
uv run inv mypy
echo "---------------- Finished ---------------"
