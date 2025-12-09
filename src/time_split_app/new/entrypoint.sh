#!/bin/bash
set -eux

source extensions.env
exec streamlit run app.py --server.address=0.0.0.0
