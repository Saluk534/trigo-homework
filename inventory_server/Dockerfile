FROM python:3.13-slim

RUN python3 -m pip install flask
WORKDIR /code

COPY main.py main.py

ENTRYPOINT [ "python3", "main.py" ]