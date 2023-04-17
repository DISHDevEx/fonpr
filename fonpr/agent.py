"""
Module to contain respons agent. it is also the module that runs as a container in eks. 
"""
import time
import logging
from collections import defaultdict
import pandas as pd
from advisors import PromClient
from utilities import prom_cpu_mem_queries


def print_lim_reqs():
    """
    Create a prometheus client, connect to server, make queries, and print limits and requests for all pods.
    V0 logic for the respons agent.
    For V0 the agent will use the max/avg of CPU and Memory as the limits/requests.

    Returns
    -------
        None. (logging and printing data for v0)
    """

    # Init promclient, and pass it the queries (list).
    prom_client_advisor = PromClient()
    prom_client_advisor.set_queries_by_function(prom_cpu_mem_queries)
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

    # Transcribe the dictionary to dataframe.
    df_lim_req = pd.DataFrame.from_dict(
        dict_lim_req,
        orient="index",
        columns=[
            "lim_cpu_cores",
            "req_cpu_cores",
            "lim_memory_bytes",
            "req_memory_bytes",
        ],
    )

    logging.info("\t" + df_lim_req.to_string().replace("\n", "\n\t"))
    print(df_lim_req.head(100))


if __name__ == "__main__":
    """
    Call the print_lim_reqs() function for a predefined set of iterations, with a waiting period.
    10000 iterations, and wait period of 5 seconds.
    """

    num_iterations = 10000
    time_interval = 5

    for iterate in range(num_iterations):
        print_lim_reqs()
        logging.info(
            "iteration: ", iterate, "! next update in ", time_interval, " seconds"
        )
        print("iteration: ", iterate, "! next update in ", time_interval, " seconds")
        time.sleep(time_interval)
