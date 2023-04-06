"""
Module to contain spark advisor to connect to target and stream logs in.
"""
import time
from pyspark.sql import SparkSession



class SparkAdvisor:
    """SparkAdvisor utilizes spark streaming to ingest data for respons agents.

        The SparkAdvisor is meant to ingest real time data stream.
        Once real time data is ingested, the advisor will expose the data in a palatable format for respons agents. 
    

    Attributes:
        host: string 
            Defining ip or host name from where the data originates.
        port: int 
            Defining the port from which the host will be exposing data. 
    """
    def __init__(self, host='"10.0.101.214"', port=9090):
        """
        Initalizes the instance based on host name and port.
           

        Parameters
        ----------
            host: string
                Ip address or host name from where the data originates. 
            port: int
                The port from which the host will be exposing data. 
        """
        self.host = host
        self.port = port
        self.spark = SparkSession.builder.appName("LogStreamProcessor").getOrCreate()

    def get_host(self):
        """
        Return string host value. 
        
        Host is where data is originating.
        """
        return self.host

    def set_host(self, host):
        """
        Modify the string value for host. 
        
        Host is where data is originating.
        
        Parameters
        ----------
            host: string
                Ip address or host name from where the data originates. 
        """
        
        self.host = host

    def get_port(self):
        """
        Return integer port value. 
        
        Port is where data is published on the host.
        """
        return self.port

    def set_port(self, port):
        """
        Modify the integer value for port.
        
        Port is where data is published on the host.
        
        Parameters
        ----------
            port: int
                The port from which the host will be exposing data. 
        """
        self.port = port

    def read_stream(self):
        """
        Connect to specified server address:port. 
        
        From established connection, stream data that is published at that location.
        
        Returns
        ----------
            lines: spark.readStream
                The stream that is published by host:port.  
        """
        lines = (
            self.spark.readStream.format("socket")
            .option("host", self.host)
            .option("port", self.port)
            .load()
        )
        query = lines.writeStream.format("console").start()
        time.sleep(10)  # sleep 10 seconds
        query.stop()
        return lines
