FROM python:3.12

RUN pip install pipenv

WORKDIR /app

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --dev --system

COPY . .

ENV PYTHONPATH="/app/src:${PYTHONPATH}"
ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
