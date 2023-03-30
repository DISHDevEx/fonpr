FROM python:3.9.1

#install wget
RUN apt-get install curl wget

# VERSIONS
ENV SPARK_VERSION=3.3.1 \
HADOOP_VERSION=3 \
JAVA_VERSION=11

# SET JAVA ENV VARIABLES
ENV JAVA_HOME="/home/jdk-${JAVA_VERSION}.0.2"
ENV PATH="${JAVA_HOME}/bin/:${PATH}"

# Download and Install java
RUN apt-get update\
    && apt-get install -y openjdk-${JAVA_VERSION}-jre\
    && mkdir --parents ${JAVA_HOME}/bin/\
    && mv usr/bin/java ${JAVA_HOME}/bin/\
    && apt-get clean\
    && rm -rf /var/lib/apt/lists/*

# DOWNLOAD SPARK AND INSTALL
RUN DOWNLOAD_URL_SPARK="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
    && wget --no-verbose -O apache-spark.tgz  "${DOWNLOAD_URL_SPARK}"\
    && mkdir -p /home/spark \
    && tar -xf apache-spark.tgz -C /home/spark --strip-components=1 \
    && rm apache-spark.tgz
    

# SET SPARK ENV VARIABLES
ENV SPARK_HOME="/home/spark"
ENV PATH="${SPARK_HOME}/bin/:${PATH}"

# SET PYSPARK VARIABLES
ENV PYTHONPATH="${SPARK_HOME}/python/:$PYTHONPATH"
ENV PYTHONPATH="${SPARK_HOME}/python/lib/py4j-0.10.9.5-src.zip:$PYTHONPATH"

# Let's change to  "$NB_USER" command so the image runs as a non root user by default
USER $NB_UID

# ENTRYPOINT ["python" ]
WORKDIR /app

## Copy requirements over into working dir
COPY requirements.txt .

# Install pip and install requireiments
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy all files into working dir
COPY . .

#expose port 8888 for tcp spark streaming
EXPOSE 8888

#using python3 run our agent
CMD [ "python3", "response_ml/spark_agent.py"]