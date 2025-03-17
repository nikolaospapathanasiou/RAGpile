#!/bin/bash

alembic upgrade head

python -m debugpy --listen 0.0.0.0:5678 src/app.py
