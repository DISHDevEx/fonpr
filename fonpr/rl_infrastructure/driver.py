import time
import logging
from advisors import PromClient
from utilities import prom_network_upf_query, ec2_cost_calculator
from action_handler import ActionHandler, get_token
import tensorflow as tf
import numpy as np
import tf_agents
from tf_agents.trajectories import trajectory

class Driver:
    
    def __init__(self,prom_endpoint = "http://10.0.104.52:9090",wait_period = 2 ):
        self.prom_endpoint = prom_endpoint
        self.wait_period = wait_period
    
    def reward_function(self, throughput, infra_cost):
        """
        Calculates the reward for the agent to receive based off of throughput and infrastructure cost.
    
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
    
        # All cost is calculated on an hourly basis
        # Throughput must be in bytes.
        # The cost conversion coefficient converts 1 gigabyte to 3.33$(https://newsdirect.com/news/mobile-phone-data-costs-7x-more-in-the-us-than-the-uk-158885004?category=Communications).
        cost_conversion_coefficient = 3.33 / (10**9)
        reward = (throughput) * (cost_conversion_coefficient) - infra_cost
        return reward
    
    
    def get_throughput(self):
        """
        Calculates the average network bytes transmitted from the UPF pod for the last hour.
    
        Returns
        -------
            avg_upf_network: float
                The average network transmitted for the last hour from UPF pod.
        """
    
        # Set the prometheus client endpoint for the prometheus server in Respons-Nuances.
        prom_client_advisor = PromClient(self.prom_endpoint)
        prom_client_advisor.set_queries_by_function(prom_network_upf_query)
        avg_upf_network = prom_client_advisor.run_queries()
        avg_upf_network = float(avg_upf_network[0][0]["value"][1])
        return avg_upf_network
    
    
    def get_infra_cost(self,size="Large"):
        """
        Calculates the hourly cost of the infrastructure based off the categorical value of size.
    
        Parameters
        ----------
            size : str
                Specify the nodegroup sizing for upf.
        Returns
        -------
            cost: int
                The hourly cost of running the ec2 sizing for the UPF pod.
        """
    
        if size == "Small":
            return ec2_cost_calculator("t3.medium")
        if size == "Large":
            return ec2_cost_calculator("m4.large")
    
    
    def update_yml(self,
        size="Large",
        gh_url="https://github.com/DISHDevEx/napp/blob/aakash/hpa-nodegroups/napp/open5gs_values/5gSA_no_ues_values_with_nodegroups.yaml",
        dir_name="napp",
    ) -> None:
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
    
        # Requested actions is a dictionary specifying the pod to modify, and the sizing for that pod.
        requested_actions = {"target_pod": "upf", "values": size}
    
        # Update remote repository with requested values.
        hndl = ActionHandler(get_token(), gh_url, dir_name, requested_actions)
        hndl.fetch_update_push_upf_sizing()
        logging.info("Agent update complete!")
        
        
        
    def take_action_get_next_timestep(self,action_step):
        
        if(action_step.action ==0):
            self.update_yml(size="Small")
        
        if(action_step.action ==1):
            self.update_yml(size="Large")
            
        time.sleep(self.wait_period)
        
        throughput = self.get_throughput()
        infra_cost = self.get_infra_cost()
        reward = self.reward_function(throughput,infra_cost)
    
        discount  = tf.convert_to_tensor(np.array(1,np.float32))
        observation = tf.convert_to_tensor(np.array([throughput],np.float32))
        reward = tf.convert_to_tensor(np.array(reward,np.float32))
        step_type = tf.convert_to_tensor(np.array(1,np.float32))
        
        next_time_step = tf_agents.trajectories.TimeStep(discount = discount,observation = observation, reward=reward, step_type = step_type )
        return next_time_step
     
     
     
        
    def drive(self,max_steps=10,policy=-1, observer=-1):
        
        throughput = self.get_throughput()
        infra_cost = self.get_infra_cost()
        reward = self.reward_function(throughput,infra_cost)
        
        discount  = tf.convert_to_tensor(np.array(1,np.float32))
        observation = tf.convert_to_tensor(np.array([throughput],np.float32))
        reward = tf.convert_to_tensor(np.array(reward,np.float32))
        step_type = tf.convert_to_tensor(np.array(0,np.float32))
        
        current_timestep = tf_agents.trajectories.TimeStep(discount = discount,observation = observation, reward=reward, step_type = step_type )
        
    
        for step in range(max_steps):
            
            if(step == 0):
                policy_state = policy.get_initial_state(1)
                
            action_step = policy.action(current_timestep,policy_state)
            next_time_step = self.take_action_get_next_timestep(action_step)
            action_step_with_previous_state = action_step._replace(state=policy_state)
            traj = trajectory.from_transition(current_timestep, action_step_with_previous_state, next_time_step)
            observer(traj)
            current_timestep = next_time_step
            policy_state = action_step.state
        
        return current_timestep, policy_state
            
