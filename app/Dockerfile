FROM python:3.8

WORKDIR /user

RUN apt-get update && apt-get install sqlite3

COPY init.sql .

RUN sqlite3 -init init.sql doogs.db

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.py .

EXPOSE 8000
