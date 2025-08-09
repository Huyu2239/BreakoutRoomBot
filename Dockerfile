FROM python:3.12.5-bullseye

RUN apt update; apt -y install tzdata && \
cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN pip install -U pip

WORKDIR /src

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/. .

CMD ["python", "-u", "main.py"]
