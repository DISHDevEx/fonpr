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

from advisors import PromClient
from utilities import prom_network_upf_query, ec2_cost_calculator,prom_network_upf_interfaces_query
from action_handler import ActionHandler, get_token

if __name__ == "__main__":
        prom_client_advisor = PromClient("http://10.0.104.52:9090")
        prom_client_advisor.set_queries_by_function(prom_network_upf_interfaces_query)
        avg_upf_network_interfaces = prom_client_advisor.run_queries()
        
        print(avg_upf_network_interfaces)
        