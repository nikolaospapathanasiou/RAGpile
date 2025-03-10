#!/bin/bash

alembic upgrade head

fastapi dev src/app.py --host 0.0.0.0 --port 8000
