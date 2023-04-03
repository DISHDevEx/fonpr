"""
Module to contain spark advisor to connect to target and stream logs in
"""

import logging
from pyspark.sql import SparkSession
import argparse
import time
 
class SparkAdvisor():
    
    def __init__(self,host = '"10.0.101.214"',port = 9090):
        """
        Constructor to the advisor. 
        Inputs: host address, port address for socket server/client desired connection
        outputs: None
        """
        self.host = host
        self.port = port
        self.spark = SparkSession.builder.appName("LogStreamProcessor").getOrCreate()
 
    def get_host(self):
        """
        Return host
        Input: None
        Output: host
        """
        return self.host 
        
    def set_host(self,host):
        """
        Set host
        Input: host
        Output: none
        """
        self.host = host
        
    def get_port(self):
        """
        Return port
        Input: None
        Output: port
        """
        return self.port
        
    def set_port(self, port):
        """
        Set port
        Input: port
        Output: none
        """
        self.port = port

    
    def read_stream(self):
        """
        Connect to specified server address:port, and stream data that is published at that location. 
        Input: None
        Output: Data that was published at the location the spark stream is connected to 
        """
        lines = (
             self.spark.readStream.format("socket")
            .option("host",self.host )
            .option("port", self.port)
            .load()
        )
        query = lines.writeStream.format("console").start()
        time.sleep(10)  # sleep 10 seconds
        query.stop()
        return lines
