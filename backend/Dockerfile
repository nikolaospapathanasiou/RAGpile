FROM python:3.13

RUN pip install pipenv

WORKDIR /app

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --dev --system

COPY . .

ENV PYTHONPATH="/app/src:${PYTHONPATH}"
CMD [ "/app/docker-entrypoint.sh" ]

