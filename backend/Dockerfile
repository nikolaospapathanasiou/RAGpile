FROM python:3.13

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY . .

ENV PYTHONPATH="/app/src:${PYTHONPATH}"
CMD [ "/app/docker-entrypoint.sh" ]

