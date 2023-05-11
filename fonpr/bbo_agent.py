"""
Module to contain respons agent. it is also the module that runs as a container in eks.
"""
import time
import logging
from collections import defaultdict
from advisors import PromClient
from utilities import prom_cpu_mem_queries,ec2_cost_calculator
from action_handler import ActionHandler, get_token
import argparse
import logging
from vizier.service import clients
from vizier.service import pyvizier as vz


def reward_function(throughput,infra_cost):
    ## throughput must be in bytes 
    ## the cost conversion coefficient converts 1 gigabit to 3.33$(https://newsdirect.com/news/mobile-phone-data-costs-7x-more-in-the-us-than-the-uk-158885004?category=Communications)

    cost_conversion_coefficient = 3.33/1000000000
    reward = (throughput)*(cost_conversion_coefficient) - infra_cost
    

def get_throughput():
    
    throughput = 1000000000
    
    return throughput

def get_infra_cost(size="Large"):
    if(size == "Small"):
        return ec2_cost_calculator()
    


def update_yml(size ='Large', gh_url ='https://github.com/DISHDevEx/napp/blob/vinny/test-updating-yml/napp/open5gs_values/5gSA_no_ues_values_with_nodegroups.yaml', dir_name='napp') -> None:
    """
    Executes data ingestion via an advisor, executes logic to output a dictionary
    of requested actions based on the advisor outputs, and updates the controlling 
    document in its remote repo using the action handler.
    
    Parameters
    ----------
        size : str
            specify the nodegroup sizing for upf
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
    
    # Update remote repository with requested values
    hndl = ActionHandler(get_token(), gh_url, dir_name, requested_actions)
    hndl.fetch_update_push()
    logging.info('Agent update complete!')



if __name__ == "__main__":
    """
    Test cycle: running execute_agent_cycle repeatedly to demonstrate base
    functionality in the kubernetes environment.
    """
    
    ##set a sizing variable for reward function to intake
    current_sizing_selected = 'Large'
    
    ##instantiate some logging
    logging.basicConfig(level=logging.INFO)
    logging.info('Launching FONPR Agent')
    
    #setup google vizier for BBO 
    study_config = vz.StudyConfig(algorithm='GAUSSIAN_PROCESS_BANDIT')
    study_config.search_space.root.add_categorical_param('size', ['Small', 'Large'])
    study_config.metric_information.append(vz.MetricInformation('metric_name', goal=vz.ObjectiveMetricGoal.MAXIMIZE))
    study = clients.Study.from_study_config(study_config, owner='vinayak', study_id='example1')
    
    ##Run BBO
    for i in range(1):
        # logging.info('Executing update cycle.')
        
        suggestions = study.suggest(count=1)

        for suggestion in suggestions:
            params = suggestion.parameters
            update_yml(size = params['size'] )
            ##sleep for 60 seconds, to see the impact of changing sizing
            time.sleep(60)
            observed_throughput = get_throughput()
            
            reward = reward_function(observed_throughput,)
            
        

