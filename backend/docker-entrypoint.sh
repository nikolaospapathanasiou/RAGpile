#!/bin/bash

alembic upgrade head

python src/debug.py
