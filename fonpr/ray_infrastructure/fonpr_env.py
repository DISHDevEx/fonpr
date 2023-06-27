"""
Class defining the Gymnasium type environment for FONPR agents.
"""

import gymnasium as gym
import pandas as pd
import numpy as np
import logging
import datetime
from gymnasium import spaces, Env
from time import sleep
from typing import Tuple, Any, Optional

from advisors import PromClient
from utilities import prom_query_rl_upf_throughput_pods, ec2_cost_calculator
from action_handler import ActionHandler, get_token


class FONPR_Env(Env):
    """
    ### Description
    
    Environment defining the interface between reinforcement learning algorithms
    and the respons-nuances 5G ecosystem, based off of Gymnasium environments.
    
    Provides a means for generating observations of a respons-nuances cluster,
    calculating a reward function, and implementing updates to the controlling
    values.yaml file on the remote repository.
    
    ### Action Space
    
    The actions available in this interface are discrete, and control the EC2
    instance size to be utilized by the User Plane Function (UPF).
    
    | Num | Action                                |
    |-----|---------------------------------------|
    | 0   | NOOP - Take no action                 |
    | 1   | Transition to the Large instance type |
    | 2   | Transition to the Small instance type |
    
    ### Observation Space
    
    The observation is a `ndarray` with shape `(self.samples, 3)` that provides
    timeseries data about user plane network throughput, and which EC2 instance
    types were being utilized over the window:
    
    | Num | Observation                  | Min                 | Max               |
    |-----|------------------------------|---------------------|-------------------|
    | 0   | User Plane Throughput        | 0                   | np.inf            |
    | 1   | Large instance == "On"       | 0                   | 1                 |
    | 2   | Small instance == "On"       | 0                   | 1                 |
    
    ### Rewards
    
    The goal is to maximize profit in dollars by optimizing revenue, generated 
    by throughput, against the infrastructure cost necessary for generating that
    revenue. 
    
    TODO: incorporate Service Level Agreements (SLAs) and Quality of Service (QoS) 
    metrics into the formula, as well.
    
    ### Starting State
    
    The starting state is simply an observation of an already existing Respons-Nuances
    cluster. The agent runs continuously, taking steps at periodic intervals and
    learning from the user plane load patterns and its actions as they arrive.
    This environment assumes no control over the load seen by the network.
    
    ### Episode Termination
    
    This is a continuous environment and has no terminal state.
    
    ### Arguments
    
    An env_config dictionary can be passed to update render mode, window size, 
    sample rate, and the observation period at agent initialization.

    Attributes
    ----------
        window: int
            How far back in time does the observation look, in minutes.
        sample_rate: int
            How many observation samples are collected per minute.
        samples: int
            Total number of samples to be collected at each observation.
        obs_period: int
            How frequently does a new observation occur, in minutes.
        observation_space: gymnasium.spaces.Box
            Defines the shape and acceptable range of values for state observations.
        action_space: gymnasium.spaces.Discrete
            Defines the shape and acceptable range of values for agent actions.
        render_mode: Any
            Selector for training and performance visualization types.
        step_counter: int
            Counter for how many steps have been taken using the current interface.
        large_instance_type: str
            The AWS EC2 instance type in the Large instance Node Group.
        small_instance_type: str
            The AWS EC2 instance type in the Small instance Node Group.
        prom_endpoint: str
            The target endpoint for the on cluster prometheus server.

    Methods
    -------
        _get_obs() -> np.array:
            Internal class method that queries the Prometheus server for state
            information, returning a processed array of state values.
            
        _get_info() -> dict:
            Return a dictionary of agent / environment information (currently empty)
            
        reset(*, seed: Optional[int], options: Optional[dict]) -> Tuple[np.array, dict]:
            If running a simulator, this method resets the state of the environment
            according to desired behavior (deterministic or stochastic), and then
            returns an initial observation of the new environment and the info dictionary.
            
            Respons-Nuances clusters are not designed to be reset in this sense.
            As such, reset provides an initial observation for beginning the training
            process.
            
        step(action: int) -> Tuple[np.array, float, bool, bool, dict]:
            Implement action, dwell for a specified period of time, then collect
            next time step observation.
            
            Returns the new observation, new reward, if the new observed state is
            considered terminated, if the new observed state is truncated, and info.
            
        render():
            Not currently implemented.
            
            Used for visualizing training.
            
        close():
            Not currently implemented.
            
            Used to close the environment and terminate external software that
            may have been invoked during environment use.
    """
    logging.basicConfig(level=logging.INFO)
    metadata = {"render_modes": []}
    
    # Custom environments must take a single 'env_config' parameter in their constructor.
    # See the ray documentation here for more detail: https://docs.ray.io/en/master/rllib/rllib-env.html
    def __init__(
        self, 
        env_config={
            'render_mode': None, 
            'window': 15, 
            'sample_rate': 4, 
            'obs_period': 5, 
            'prom_endpoint': 'http://10.0.114.131:9090',
            'gh_url': 'https://github.com/DISHDevEx/napp/blob/agent-sac/napp/open5gs_values/5gSA_no_ues_values_with_nodegroups.yaml',
            'dir_name': 'napp'
            }
        ) -> None:

        self.prom_endpoint = env_config['prom_endpoint'] # Endpoint for the Prometheus server on the cluster
        self.window = env_config['window'] # How far back in time does the observation look, in minutes
        self.sample_rate = env_config['sample_rate'] # How many observation samples are collected per minute
        self.samples = self.window * self.sample_rate
        self.obs_period = env_config['obs_period'] # How frequently does a new observation occur, in minutes
        self.gh_url = env_config['gh_url'] # Path to remote controlling value.yaml file
        self.dir_name = env_config['dir_name'] # Repo name that hosts the value.yaml file
        
        # States we are observing consist of "Throughput", "Large instance On", "Small instance On".
        low=np.tile(np.array([0., 0., 0.]), (self.samples,1))
        high=np.tile(np.array([np.inf, 1., 1.]), (self.samples,1))
        
        self.observation_space = spaces.Box(
            low=low, 
            high=high, 
            shape=(self.samples, low.shape[1])
            )

        # We have 3 actions, corresponding to "NOOP", Transition to Large", "Transition to Small".
        self.action_space = spaces.Discrete(3)

        # assert render_mode is None or render_mode in self.metadata["render_modes"].
        self.render_mode = env_config['render_mode']
        
        self.step_counter = 0
        self.large_instance_type = 'm4.xlarge' # Hardcoded to begin
        self.small_instance_type = 't3.medium' # Hardcoded to begin

    def _get_obs(self) -> np.array:
        # Request query from Prometheus.
        prom_client_advisor = PromClient(self.prom_endpoint)
        prom_client_advisor.set_queries_by_list(prom_query_rl_upf_throughput_pods(self.window))
        prom_response = prom_client_advisor.run_queries()
        
        # Create dataframe for processing of query data.
        # The dataframe is constructed in a way to allow for flexibility in 
        # sample parameters (window and sample rate).
        df = pd.DataFrame(columns=['DateTime', 'Throughput', self.large_instance_type, self.small_instance_type])
        data_df = pd.DataFrame(prom_response[0][0]['values'])
        df[['DateTime', 'Throughput']] = data_df
        df = df.set_index('DateTime') # Use timestamps for index
        df.index = pd.to_datetime(df.index, unit='s')
        df = df.astype('float32')
        
        # With the Prometheus sample rate outside of our control, we can request
        # a certain resolution, but we are not guaranteed to have data at our
        # requested interval. As such, we will need to resize our data and address
        # any NaNs that are created in the process. Simple linear interpolation
        # is used to handle missing values in this case. If the sampling rate of
        # Prometheus changes, the number of NaNs may change, but the observation
        # shape will remain the same.
        df['Throughput'] = df['Throughput'] - df.iloc[0,0] # Normalize all throughput to value at first timestamp
        df = df.interpolate() # Linear interpolation for any missing values
        df = df.resample(f'{int(60/self.sample_rate)}s').mean() # Keep input size consistent
        df = df.interpolate() # Linear interp again for any NaNs created by resample
        
        # Process pod info.
        for i, pod in enumerate(prom_response[1]):
            
            # isolate node label and timestamps.
            node = pod['metric']['node']
            values = pod['values']
            
            # map node to instance-type.
            prom_client_advisor.set_queries_by_list(['kube_node_labels{node=\'' + node + '\'}'])
            node_labels = prom_client_advisor.run_queries()
            instance_type = node_labels[0][0]['metric']['label_node_kubernetes_io_instance_type']
            
            # create on-flags for instance type.
            df_pod = pd.DataFrame(values, columns=['DateTime', instance_type])
            df_pod = df_pod.set_index('DateTime')
            df_pod.index = pd.to_datetime(df_pod.index, unit='s')
            df_pod = df_pod.astype('float32')
            df.update(df_pod)
            df = df.interpolate()
        
        # Ensure input shape is met.
        while len(df) != self.samples:
            df.loc[df.index[0]-datetime.timedelta(seconds=60/self.sample_rate)] = df.loc[df.index[0]] # create new timestamp index and copy first row values
            df = df.sort_index()
        
        df = df.fillna(0) # If instance types have NaNs after interp, assumed off
        
        return df.values

    def _get_info(self) -> dict:
        # Provide information on state, action, and reward?
        return {}
        
    def reset(self, *, seed=None, options=None) -> Tuple[np.array, dict]:
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action) -> Tuple[np.array, float, bool, bool, dict]:
        
        if action == 0: # No-Op; do nothing
            logging.info('No action taken for this cycle.')
            pass
        elif action == 1: # Transition to Large instance
            logging.info('Transitioning to Large instance type.')
            hndl = ActionHandler(get_token(), self.gh_url, self.dir_name, {"target_pod": "upf", "values": "Large"})
            hndl.fetch_update_push_upf_sizing()
        elif action == 2: # Transition to Small instance
            logging.info('Transitioning to Small instance type.')
            hndl = ActionHandler(get_token(), self.gh_url, self.dir_name, {"target_pod": "upf", "values": "Small"})
            hndl.fetch_update_push_upf_sizing()
            
        sleep(self.obs_period * 60) # Sleep for observation period before retrieving next observation
        
        rxtx_value = 3.33e-9 # Rough estimate of dollars per byte over the network
        large_cost = ec2_cost_calculator(self.large_instance_type) # Cost of large instance in dollars per hour
        small_cost = ec2_cost_calculator(self.small_instance_type) # Cost of small instance in dollars per hour
        
        observation = self._get_obs()
        # reward over window: revenue generated by rx/tx on network ($) - cost of running large instance ($) - cost of running small instance ($)
        reward = rxtx_value * observation[-1, 0] \
            -((large_cost / 60) * (np.sum(observation[:, 1]) / self.samples) * self.window) \
            -((small_cost / 60) * (np.sum(observation[:, 2]) / self.samples) * self.window)
        info = self._get_info()
        
        terminated = False # No terminal state for our environment; continuous
        self.step_counter += 1
        truncated = False # Infinite time horizon; no condition where environment gets reset

        return observation, reward, terminated, truncated, info

    def render(self):
        ...

    def close(self):
        ...
