"""
Module to contain respons agent. it is also the module that runs as a container in eks.
"""
import time
import logging
from collections import defaultdict
import pandas as pd
from advisors import PromClient
from utilities import prom_cpu_mem_queries
from action_handler import ActionHandler, get_token


    
def collect_lim_reqs() -> dict:
    """
    Create a prometheus client, connect to server, make queries, and print limits and requests for all pods.
    V0 logic for the respons agent. 
    For V0 the agent will use the max/avg of CPU and Memory as the limits/requests. 

    Returns
    -------
        dict_lim_request : dict
            Dictionary containing limits and requests for each pod
    """
    
    #Init promclient, and pass it the queries (list). 
    prom_client_advisor = PromClient(prom_endpoint)
    prom_client_advisor.set_queries(prom_cpu_mem_queries)
    
    (
        max_cpu_data,
        avg_cpu_data,
        max_memory_data,
        avg_memory_data,
    ) = prom_client_advisor.run_queries()

    # Init an empty dict to hold the limits and requests for all pods.
    # Key:Value pairs will look like the following --> dict_lim_req[pod_name] = [max_cpu,avg_cpu_data,max_memory,avg_memory].
    # Max(cpu) and max(memory) serve as the new limits to be set.
    # Avg(cpu) and avg(memory) serve as the new requests to be set.

    dict_lim_req = defaultdict(list)
    logging.info("making prometheus requests!!")

    # The output for a single query from prometheus is a list of nested dictionaries.
    # The following code block processes the query results into a dataframe.
    # Processing query in O(n) time complexity.
    for step in range(len(max_cpu_data)):
        try:
            dict_lim_req[max_cpu_data[step]["metric"]["pod"]].append(
                max_cpu_data[step]["value"][1]
            )
            dict_lim_req[avg_cpu_data[step]["metric"]["pod"]].append(
                avg_cpu_data[step]["value"][1]
            )
            dict_lim_req[max_memory_data[step]["metric"]["pod"]].append(
                max_memory_data[step]["value"][1]
            )
            dict_lim_req[avg_memory_data[step]["metric"]["pod"]].append(
                avg_memory_data[step]["value"][1]
            )
        except KeyError:
            print("empty records found, ignoring")
            
    return dict_lim_req


        
def execute_agent_cycle(prom_endpoint='Default') -> None:
    """
    Executes data ingestion via an advisor, executes logic to output a dictionary
    of requested actions based on the advisor outputs, and updates the controlling 
    document in its remote repo using the action handler.
    """
    
    # Retrieve logs and metrics from the cluster using an advisor
    if prom_endpoint != 'Default':
        lim_reqs = collect_lim_reqs(prom_endpoint)
    else:
        lim_reqs = collect_lim_reqs()
    
    # Process advisor output down to specific value update requests
    targets = [pod_name for pod_name in lim_reqs.keys() if 'amf' in pod_name]
    target_output = list(map(float, lim_reqs[targets[0]]))
    # print(f'{target_output=}')
    
    min_milicores_cpu = 100
    
    req_mem = f'{int(target_output[3] / 1_000_000)}Mi'
    
    if (milicores := int(target_output[0] * 1000) > min_milicores_cpu):
        req_cpu = f'{milicores}m'
    else:
        req_cpu = f'{min_milicores_cpu}m'
    
    # Including 5% 'headroom' for the limit so it doesn't squash over time.
    lim_mem = f'{int((target_output[2] / 1_000_000) * 1.05)}Mi'
    
    if (milicores := int(target_output[0] * 1000) > min_milicores_cpu):
        lim_cpu = f'{int(milicores * 1.05)}m'
    else:
        lim_cpu = f'{min_milicores_cpu}m'
    
    requested_actions = {
        'target_pod' : 'amf',
        'requests' : {'memory' : req_mem, 'cpu' : req_cpu},
        'limits' : {'memory' : lim_mem, 'cpu' : lim_cpu}
    }
    
    # print(requested_actions) 
    
    # Update remote repository with requested values
    gh_url = 'https://github.com/DISHDevEx/openverso-charts/blob/matt/gh_api_test/charts/respons/test.yaml'
    dir_name = 'charts'
    
    hndl = ActionHandler(get_token(), gh_url, dir_name, requested_actions)
    hndl.fetch_update_push()
    logging.info('Agent cycle complete!')

if __name__ == "__main__":
    """
    Test cycle: running execute_agent_cycle repeatedly to demonstrate base
    functionality in the kubernetes environment.
    """
    import argparse
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logging.info('Launching FONPR Agent')
    
    parser = argparse.ArgumentParser(
                        prog="FONPR_Agent",
                        description="Executes policy implementation for closed loop 5G network control.")
    
"""
Module to contain respons agent. it is also the module that runs as a container in eks.
"""
import time
import logging
from collections import defaultdict
import pandas as pd
from advisors import PromClient
from utilities import prom_cpu_mem_queries
from action_handler import ActionHandler, get_token


    
def collect_lim_reqs() -> dict:
    """
    Create a prometheus client, connect to server, make queries, and print limits and requests for all pods.
    V0 logic for the respons agent. 
    For V0 the agent will use the max/avg of CPU and Memory as the limits/requests. 

    Returns
    -------
        dict_lim_request : dict
            Dictionary containing limits and requests for each pod
    """
    
    #Init promclient, and pass it the queries (list). 
    prom_client_advisor = PromClient(prom_endpoint)
    prom_client_advisor.set_queries(prom_cpu_mem_queries)
    
    (
        max_cpu_data,
        avg_cpu_data,
        max_memory_data,
        avg_memory_data,
    ) = prom_client_advisor.run_queries()

    # Init an empty dict to hold the limits and requests for all pods.
    # Key:Value pairs will look like the following --> dict_lim_req[pod_name] = [max_cpu,avg_cpu_data,max_memory,avg_memory].
    # Max(cpu) and max(memory) serve as the new limits to be set.
    # Avg(cpu) and avg(memory) serve as the new requests to be set.

    dict_lim_req = defaultdict(list)
    logging.info("making prometheus requests!!")

    # The output for a single query from prometheus is a list of nested dictionaries.
    # The following code block processes the query results into a dataframe.
    # Processing query in O(n) time complexity.
    for step in range(len(max_cpu_data)):
        try:
            dict_lim_req[max_cpu_data[step]["metric"]["pod"]].append(
                max_cpu_data[step]["value"][1]
            )
            dict_lim_req[avg_cpu_data[step]["metric"]["pod"]].append(
                avg_cpu_data[step]["value"][1]
            )
            dict_lim_req[max_memory_data[step]["metric"]["pod"]].append(
                max_memory_data[step]["value"][1]
            )
            dict_lim_req[avg_memory_data[step]["metric"]["pod"]].append(
                avg_memory_data[step]["value"][1]
            )
        except KeyError:
            print("empty records found, ignoring")
            
    return dict_lim_req


        
def execute_agent_cycle(prom_endpoint='Default') -> None:
    """
    Executes data ingestion via an advisor, executes logic to output a dictionary
    of requested actions based on the advisor outputs, and updates the controlling 
    document in its remote repo using the action handler.
    """
    
    # Retrieve logs and metrics from the cluster using an advisor
    if prom_endpoint != 'Default':
        lim_reqs = collect_lim_reqs(prom_endpoint)
    else:
        lim_reqs = collect_lim_reqs()
    
    # Process advisor output down to specific value update requests
    targets = [pod_name for pod_name in lim_reqs.keys() if 'amf' in pod_name]
    target_output = list(map(float, lim_reqs[targets[0]]))
    # print(f'{target_output=}')
    
    min_milicores_cpu = 100
    
    req_mem = f'{int(target_output[3] / 1_000_000)}Mi'
    
    if (milicores := int(target_output[0] * 1000) > min_milicores_cpu):
        req_cpu = f'{milicores}m'
    else:
        req_cpu = f'{min_milicores_cpu}m'
    
    # Including 5% 'headroom' for the limit so it doesn't squash over time.
    lim_mem = f'{int((target_output[2] / 1_000_000) * 1.05)}Mi'
    
    if (milicores := int(target_output[0] * 1000) > min_milicores_cpu):
        lim_cpu = f'{int(milicores * 1.05)}m'
    else:
        lim_cpu = f'{min_milicores_cpu}m'
    
    requested_actions = {
        'target_pod' : 'amf',
        'requests' : {'memory' : req_mem, 'cpu' : req_cpu},
        'limits' : {'memory' : lim_mem, 'cpu' : lim_cpu}
    }
    
    # print(requested_actions) 
    
    # Update remote repository with requested values
    gh_url = 'https://github.com/DISHDevEx/openverso-charts/blob/matt/gh_api_test/charts/respons/test.yaml'
    dir_name = 'charts'
    
    hndl = ActionHandler(get_token(), gh_url, dir_name, requested_actions)
    hndl.fetch_update_push()
    logging.info('Agent cycle complete!')

if __name__ == "__main__":
    """
    Test cycle: running execute_agent_cycle repeatedly to demonstrate base
    functionality in the kubernetes environment.
    """
    import argparse
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logging.info('Launching FONPR Agent')
    
    parser = argparse.ArgumentParser(
                        prog="FONPR_Agent",
                        description="Executes policy implementation for closed loop 5G network control.")
    
    parser.add_argument(
            '--interval',
            metavar="-I",
            type=int,
            default=15,
            required=False,
            help='Time in minutes between executions of the policy logic.')
    parser.add_argument(
            '--prom_endpoint',
            metavar="-E",
            type=str,
            default='Default',
            required=False,
            help='Override default Prometheus server IP address / port.')
    
    args = parser.parse_args()
    
    logging.info(f'Update interval set to {args.interval}.')
    logging.info(f'Prometheus server endpoint: {args.prom_endpoint}')
    
    while True:
        logging.info('Executing update cycle.')
        execute_agent_cycle(args.prom_endpoint)
        time.sleep(args.interval * 60)
    
    args = parser.parse_args()
    
    while True:
        execute_agent_cycle()
        time.sleep(args.interval * 60)
