#!/bin/bash

alembic upgrade head

fastapi dev app.py --host 0.0.0.0 --port 8000
