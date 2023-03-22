FROM --platform=linux/amd64 amazonlinux:2 AS base

WORKDIR /app

RUN yum install -y python3
RUN yum install -y java 

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .




