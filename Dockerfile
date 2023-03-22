FROM --platform=linux/amd64 amazonlinux:2 AS base

WORKDIR /app

RUN yum install -y python3 git

RUN yum install java

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "./response-ml/agent.py", "run", "--host=0.0.0.0"]



