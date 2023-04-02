from advisors import PromClient
from utilities import prom_cpu_mem_queries
from collections import defaultdict
import numpy as np
import pandas as pd
import time
import logging




def print_lim_reqs():
    prom_client_advisor = PromClient()
    prom_client_advisor.set_queries(prom_cpu_mem_queries)
    max_cpu_data,avg_cpu_data,max_memory_data,avg_memory_data =  prom_client_advisor.run_queries()
    dict_lim_req = defaultdict(list)
    logging.info("making prometheus requests!!")
    for i in range(len(max_cpu_data)):
        try:
            dict_lim_req[max_cpu_data[i]['metric']['pod']].append(max_cpu_data[i]['value'][1])
            dict_lim_req[avg_cpu_data[i]['metric']['pod']].append(avg_cpu_data[i]['value'][1])
            dict_lim_req[max_memory_data[i]['metric']['pod']].append(max_memory_data[i]['value'][1])
            dict_lim_req[avg_memory_data[i]['metric']['pod']].append(avg_memory_data[i]['value'][1])
        except KeyError:
            print("empty records found, ignoring")
    
    df_lim_req = pd.DataFrame.from_dict(dict_lim_req,orient='index', columns = ["lim_cpu_cores","req_cpu_cores","lim_memory_bytes","req_memory_bytes"])
    
    logging.info('\t'+ df_lim_req.to_string().replace('\n', '\n\t')) 
    print(df_lim_req.head(100))
    
    
if __name__ == "__main__":
    num_iterations = 10000
    time_interval = 5
    
    for i in range(num_iterations):
        print_lim_reqs()
        logging.info("iteration: ", i, "! next update in ", time_interval, " seconds")
        print("iteration: ", i, "! next update in ", time_interval, " seconds")
        time.sleep(time_interval)
        
    