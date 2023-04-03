"""
Module to contain prometheus client to connect and query the prometheus server
"""

from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import pprint

class PromClient:
    def __init__(self, prom_endpoint="http://10.0.101.214:9090"):
        """
        Constructor to the advisor. 
        Inputs: 
            prom_endpoint: STR (formatted typically as http://ip:port)
        outputs: None
        """
        self.prom_endpoint = prom_endpoint
        self.prom = PrometheusConnect(url=prom_endpoint)
        self.queries = []
        self.query_results = []

    def get_endpoint(self):
        """
        Return prometheus endpoint
        Input: None
        Output: prometheus endpoint
        """
        return self.prom_endpoint
        
    def set_endpoint(self,new_prom_endpoint):
        """
        Set prometheus endpoint
        Input: prometheus endpoint
        Output: none
        """
        self.prom_endpoint = new_prom_endpoint
        self.prom = PrometheusConnect(url=self.prom_endpoint)
        
    def set_queries(self, query_building_function):
        """
        Set queries
        Input: queries
        Output: none
        """
        self.queries = query_building_function()

    def get_queries(self):
        """
        Return queries
        Input: None
        Output: queries
        """
        return self.queries

    def run_queries(self):
        """
        Send queries to prometheus server, and aggregate all results in a list
        Input: None
        Output: List of query results
        """
        ## Aggregate all data:
        for query in self.queries:
            self.query_results.append(self.prom.custom_query(query=query))
        return self.query_results
