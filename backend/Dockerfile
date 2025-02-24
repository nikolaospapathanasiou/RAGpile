FROM python:3.12

RUN pip install pipenv

WORKDIR /app

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --system

COPY . .

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]