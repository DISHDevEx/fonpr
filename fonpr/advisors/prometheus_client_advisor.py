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
        prom_endpoint: String
            "ip:port" for the prometheus server endpoint.
    """
    def __init__(self, prom_endpoint="http://10.0.101.214:9090"):
        """
        Initalize the instance based on prometheus server endpoint.
           

        Parameters
        ---------
            prom_endpoint: string (formatted typically as http://ip:port)
                Ip address or host name from where the data originates. 
                
        Returns
        ---------
            None
        """
        self.prom_endpoint = prom_endpoint
        self.prom = PrometheusConnect(url=prom_endpoint)
        self.queries = []
        self.query_results = []

    def get_endpoint(self):
        """
        Return prometheus endpoint.
        
        Parameters
        ----------
            None
            
        Returns
        ---------
            prom_endpoint: String 
                (formatted typically as http://ip:port)
                Ip address or host name from where the data originates. 
            
        """
        return self.prom_endpoint

    def set_endpoint(self, new_prom_endpoint):
        """
        Set prometheus endpoint.
        
        Parameters
        ---------
            prom_endpoint: string 
                (formatted typically as http://ip:port)
                Ip address or host name from where the data originates. 
        """
        self.prom_endpoint = new_prom_endpoint
        self.prom = PrometheusConnect(url=self.prom_endpoint)

    def set_queries_by_function(self, query_building_function):
        """
        Set queries from a function.  
        
        Parameters
        ---------
            query_building_function: function that returns a list of strings
                Function that returns a list of queries, where each query is a string. 
        """
        self.queries = query_building_function()
        
    def set_query_by_list(self, list_of_queries):
        """
        Set queries from a list.
        
        Parameters
        ---------
            list_of_queries: List of strings
                List of queries, where each query is a string. 
        """
        self.queries = list_of_queries
        
    def get_queries(self):
        """
        Return queries that the class has instantiated.
        
        Parameters
        ---------
            None
            
        Returns
        ---------
            queries: List of strings
                List of queries, where each query is a string. 
        """
        return self.queries

    def run_queries(self):
        """
        Send queries to prometheus server, and aggregate all results in a list.
        
        Parameters
        ---------
            None
            
        Returns
        ---------
            query_results: List of results
                Results from prometheus server each result is a dictionary. 
        """
        # Aggregate all data:
        if(len(self.queries)<1):
            return None
        else:
            for query in self.queries:
                self.query_results.append(self.prom.custom_query(query=query))
            return self.query_results
