#!/bin/bash
set -e

echo "---------- run-invocations.sh -----------"
echo "1/5: Clean ------------------------------"
poetry run inv clean
echo "2/5: Format code ------------------------"
poetry run inv format
echo "3/5: Test -------------------------------"
poetry run inv tests
echo "4/5: Lint -------------------------------"
poetry run inv lint
echo "5/5: Typecheck (mypy) -------------------"
poetry run inv mypy
echo "---------------- Finished ---------------"
