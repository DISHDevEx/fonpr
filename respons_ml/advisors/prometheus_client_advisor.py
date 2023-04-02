from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import pprint
    
class PromClient():
 
 def __init__(self, prom_endpoint = 'http://10.0.101.214:9090'):
  self.prom_endpoint = prom_endpoint
  self.prom = PrometheusConnect(url=prom_endpoint)
  self.queries = []
  self.query_results = []
  
 def set_queries(self, query_building_function):
  self.queries = query_building_function()
  
 def get_queries(self):
  return self.queries 
 
 def run_queries(self):
  ## Aggregate all data:
  for query in self.queries:
   self.query_results.append(self.prom.custom_query(query=query))
  return self.query_results

 
 
