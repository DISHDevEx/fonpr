"""
Module to contain respons agent. it is also the module that runs as a container in eks.
"""
import time
import logging
from collections import defaultdict
from advisors import PromClient
from utilities import prom_network_upf_query,ec2_cost_calculator
from action_handler import ActionHandler, get_token
import argparse
import logging
from vizier.service import clients
from vizier.service import pyvizier as vz


def reward_function(throughput,infra_cost):
    """
    Calculates the reward for the agent to recieve based off of throughput and infrastructure cost. 
    
    Parameters
    ----------
        throughput : float
            The average network transmitted for the last hour from UPF pod. 
        infra_cost : float
            The cost of running the ec2 sizing for the UPF pod.
            
    Returns
    -------
        avg_upf_network: float
            The average network transmitted for the last hour from UPF pod. 
    """
    
    #All cost is calculated on an hourly basis
    # Throughput must be in bytes.
    # The cost conversion coefficient converts 1 gigabit to 3.33$(https://newsdirect.com/news/mobile-phone-data-costs-7x-more-in-the-us-than-the-uk-158885004?category=Communications).
    cost_conversion_coefficient = 3.33/1000000000
    reward = (throughput)*(cost_conversion_coefficient) - infra_cost
    return reward

def get_throughput():
    """
    Calculates the average network bytes transmitted from the UPF pod for the last hour. 
    
    Returns
    -------
        avg_upf_network: float
            The average network transmitted for the last hour from UPF pod. 
    """
    
    #Set the prometheus client endpoint for the prometheus server in Respons-Nuances.
    prom_client_advisor = PromClient('http://10.0.104.52:9090')
    prom_client_advisor.set_queries_by_function(prom_network_upf_query)
    avg_upf_network = prom_client_advisor.run_queries()
    avg_upf_network = float(avg_upf_network[0][0]['value'][1])
    return avg_upf_network

def get_infra_cost(size="Large"):
    """
    Calculates the hourly cost of the infrastructure based off the categorical value of size. 
    
    Parameters
    ----------
        size : str
            Specify the nodegroup sizing for upf.
    Returns
    -------
        cost: int
            The cost of running the ec2 sizing for the UPF pod.
    """
    
    if(size == "Small"):
        return ec2_cost_calculator("t3.medium")
    if(size == "Large"):
        return ec2_cost_calculator("m4.large")

def update_yml(size ='Large', gh_url ='https://github.com/DISHDevEx/napp/blob/aakash/hpa-nodegroups/napp/open5gs_values/5gSA_no_ues_values_with_nodegroups.yaml', dir_name='napp') -> None:
    """
    Updates the controlling document in its remote repo using the action handler.
    
    Parameters
    ----------
        size : str
            Specify the nodegroup sizing for upf.
        gh_url : str
            URL pointing to the target value.yaml file in GitHub (e.g. 'https://github.com/DISHDevEx/openverso-charts/blob/matt/gh_api_test/charts/respons/test.yaml')
        dir_name : str
            Name of first directory in path to the yaml file (empty string if the file is at the root of the repo)
    """
    
    #Requested actions is a dictionary specifying the pod to modify, and the sizing for that pod. 
    requested_actions = {
        'target_pod' : 'upf',
        'values' : size
    }
    
    # Update remote repository with requested values.
    hndl = ActionHandler(get_token(), gh_url, dir_name, requested_actions)
    hndl.fetch_update_push()
    logging.info('Agent update complete!')



if __name__ == "__main__":
    """
    BBO agent logic: recieve throughput, cost to make a reward. Based off reward specify sizing of the upf pod. 
    """

    #Instantiate some logging
    logging.basicConfig(level=logging.INFO)
    logging.info('Launching FONPR BBO Agent')
    
    #Setup google vizier for BBO 
    study_config = vz.StudyConfig(algorithm='GAUSSIAN_PROCESS_BANDIT')
    study_config.search_space.root.add_categorical_param('size', ['Small', 'Large'])
    study_config.metric_information.append(vz.MetricInformation('reward', goal=vz.ObjectiveMetricGoal.MAXIMIZE))
    study = clients.Study.from_study_config(study_config, owner='vinayak', study_id='smallProblemUPFSizing')
    
    ##Run BBO
    for i in range(15):
        
        logging.info('Executing update cycle.')
        
        suggestions = study.suggest(count=1)
        for suggestion in suggestions:
            params = suggestion.parameters
            update_yml(size = params['size'] )
            
            logging.info(f"Agent changing upf size to: {params['size']}")
            
            
            ##Sleep for 600 seconds, to see the impact of changing sizing. (Update hourly)
            time.sleep(600)
            
            #Get the observations for the system to build out reward function.
            #Build observed throughput.
            observed_throughput = get_throughput()
            logging.info(f"Observed throughput {observed_throughput}")
            
            #Build cost.
            observed_cost = get_infra_cost(params['size'] )
            logging.info(f"Observed cost {observed_cost}")
            
            #Build reward.
            reward = reward_function(observed_throughput,observed_cost)
            logging.info(f"Observed reward {reward}")
            
            #Complete the interaction. 
            suggestion.complete(vz.Measurement({'reward': reward}))
            
            
            
        

