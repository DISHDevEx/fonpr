from rl_infrastructure import FonprDqn
from rl_infrastructure import ReplayBuffer
from rl_infrastructure import Driver

import numpy as np
import tensorflow as tf
import tf_agents
from tf_agents.policies import random_tf_policy
from tf_agents.policies import py_tf_eager_policy
from tf_agents.utils import common
import reverb
from collections import defaultdict
import pandas as pd

from advisors import PromClient
from utilities import prom_network_upf_query, ec2_cost_calculator,prom_network_upf_interfaces_query
from action_handler import ActionHandler, get_token

import toolz



if __name__ == "__main__":
        prom_client_advisor = PromClient("http://10.0.104.52:9090")
        prom_client_advisor.set_queries_by_function(prom_network_upf_interfaces_query)
        avg_upf_network_tx,avg_upf_network_rx, node_sizing = prom_client_advisor.run_queries()
        
        dict_interface_network_tx = defaultdict(list)
        dict_interface_network_rx = defaultdict(list)
        nodes_used_list = []
        dict_node_sizing = {}
        
        

        for pod in range(len(avg_upf_network_tx)):
            dict_interface_network_tx[avg_upf_network_tx[pod]["metric"]["interface"]].append(float(avg_upf_network_tx[pod]["value"][1]))
            if(avg_upf_network_tx[pod]["metric"]["node"] not in nodes_used_list ): nodes_used_list.append(avg_upf_network_tx[pod]["metric"]["node"])
            
            dict_interface_network_rx[avg_upf_network_rx[pod]["metric"]["interface"]].append(float(avg_upf_network_rx[pod]["value"][1]))
            if(avg_upf_network_rx[pod]["metric"]["node"] not in nodes_used_list ): nodes_used_list.append(avg_upf_network_rx[pod]["metric"]["node"])
        
        for node in range(len(node_sizing)):
            if(node_sizing[node]["metric"]['node'] in nodes_used_list):
                dict_node_sizing[node_sizing[node]["metric"]['node']] = node_sizing[node]["metric"]['label_beta_kubernetes_io_instance_type']
            
        
        
        dict_interface_network_rx_sum = dict(map(lambda x: (x[0], sum(x[1])), dict_interface_network_rx.items()))
        
        dict_interface_network_tx_sum = dict(map(lambda x: (x[0], sum(x[1])), dict_interface_network_tx.items()))
         
        obs = list(dict_interface_network_rx_sum.values())+list(dict_interface_network_tx_sum.values())
        cost = list(dict_node_sizing.values())
    
        print(obs[:-1])
        
        #observations: 
        #rxtx per interface 
        
        
