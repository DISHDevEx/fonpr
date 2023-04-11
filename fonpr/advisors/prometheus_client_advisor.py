"""
Module to contain prometheus client to connect and query the Prometheus server
"""

from prometheus_api_client import PrometheusConnect

class PromClient:
    """PromClient utilizes prometheus_api_client to query Prometheus server.

        The SparkAdvisor is meant to send prebuilt queries to the Prometheus server.
        
        The Prometheus server will send back results to the queries, 
            which PromClient will expose to respons agent. 
    

    Attributes:
        prom_endpoint: str
            "ip:port" for the prometheus server endpoint
    """
    def __init__(self, prom_endpoint="http://10.0.101.214:9090"):
        """
        Initalizes the instance based on prometheus server endpoint.
           

        Parameters
        ----------
            host: string
                Ip address or host name from where the data originates. 
            port: int
                The port from which the host will be exposing data. 
        """
        
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

    def set_endpoint(self, new_prom_endpoint):
        """
        Set prometheus endpoint
        Input: prometheus endpoint
        Output: none
        """
        self.prom_endpoint = new_prom_endpoint
        self.prom = PrometheusConnect(url=self.prom_endpoint)

    def set_queries_by_function(self, query_building_function):
        """
        Set queries
        Input: queries
        Output: none
        """
        self.queries = query_building_function()
        
    def set_query_by_str(self, str_query):
        """
        Set queries
        Input: queries
        Output: none
        """
        self.queries = [str_query]
        
    def set_query_by_list(self, list_of_queries):
        """
        Set queries
        Input: queries
        Output: none
        """
        self.queries = list_of_queries
        
    def add_query_from_string(self, str_query):
        """
        Set queries
        Input: queries
        Output: none
        """
        self.queries = self.queries.append(str_query)

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
