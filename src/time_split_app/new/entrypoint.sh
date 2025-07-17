#!/usr/bin/env bash
set -eux

exec streamlit run app.py --server.address=0.0.0.0
