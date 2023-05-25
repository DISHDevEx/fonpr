'''
Class defining the Gymnasium type environment for FONPR agents.
'''

import gymnasium as gym
import pandas as pd
import numpy as np
import logging
import datetime
from gymnasium import spaces, Env
from time import sleep

from advisors import PromClient
from utilities import prom_query_rl_upf_experiment1, ec2_cost_calculator
from action_handler import ActionHandler, get_token


class FONPR_Env(Env):
    metadata = {"render_modes": []}

    def __init__(self, render_mode=None, window=15, sample_rate=4, obs_period=5):
        # An observation in this case is generated by Prometheus logs covering the past 15 minutes
        self.window = window # How far back in time does the observation look, in minutes
        self.sample_rate = sample_rate # How many observation samples are collected per minute
        self.samples = window * sample_rate
        self.obs_period = obs_period # How frequently does a new observation occur, in minutes
        
        # Temporary use until instance presence can be tracked; allows approximate reward calculation in the absense of real time data.
        self.instance_size = "Large"
        
        # States we are observing consist of "Large instance On", "Small instance On", "Throughput"
        # TODO: incorporate instance presence tracking for observation and reward function
        low=np.tile(np.array([0.]), (self.samples,1))
        high=np.tile(np.array([np.inf]), (self.samples,1))
        
        self.observation_space = spaces.Box(
            low=low, 
            high=high, 
            shape=(self.samples, low.shape[1])
            )

        # We have 3 actions, corresponding to "NOOP", Transition to Large", "Transition to Small"
        self.action_space = spaces.Discrete(3)

        # assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        self.step_counter = 0

    def _get_obs(self):
        # Request query from Prometheus
        prom_client_advisor = PromClient("http://10.0.104.52:9090")
        prom_client_advisor.set_queries_by_function(prom_query_rl_upf_experiment1())
        prom_response = prom_client_advisor.run_queries()
        
        df = pd.DataFrame(columns=['DateTime', 'Throughput', 'm4.large', 't3.medium'])
        data_df = pd.DataFrame(prom_response[0][0]['values'])
        df[['DateTime', 'Throughput']] = data_df
        df = df.set_index('DateTime') # Use timestamps for index
        df.index = pd.to_datetime(df.index, unit='s')
        df = df.astype('float32')
        
        df['Throughput'] = df['Throughput'] - df.iloc[0,0] # Normalize all throughput to value at first timestamp
        df = df.interpolate() # Linear interpolation for any missing values
        df = df.resample(f'{int(60/self.sample_rate)}s').mean() # Keep input size consistent
        df = df.interpolate() # Linear interp again for any NaNs created by resample
        
        # Process pod info
        # pods = {} # Can be used for debugging
        for i, pod in enumerate(prom_response[1]):
            
            # isolate host_ip and timestamps
            host_ip = pod['metric']['host_ip']
            values = pod['values']
            
            # map host_ip to instance-type
            node_name = 'ip-' + host_ip.replace('.', '-') + '.ec2.internal'
            prom_client_advisor.set_queries_by_list(['kube_node_labels{node=\'' + node_name + '\'}'])
            node_labels = prom_client_advisor.run_queries()
            instance_type = node_labels[0][0]['metric']['label_node_kubernetes_io_instance_type']
            
            # pods[f'pod{i}'] = {'host_ip': host_ip, 'values': values, 'instance_type': instance_type} # Can be used for debugging
            
            # create on-flags for instance type
            df_pod = pd.DataFrame(values, columns=['DateTime', instance_type])
            df_pod = df_pod.set_index('DateTime')
            df_pod.index = pd.to_datetime(df_pod.index, unit='s')
            df_pod = df_pod.astype('float32')
            print(df.head(), '\n', df_pod.head())
            df.update(df_pod)
            print(df.head())
            df = df.interpolate()
        
        # Ensure input shape is met
        while len(df) != self.samples:
            df.loc[df.index[0]-datetime.timedelta(seconds=60/self.sample_rate)] = df.loc[df.index[0]] # create new timestamp index and copy first row values
            df = df.sort_index()
        
        df = df.fillna(0) # If instance types have NaNs after interp, assumed off
        
        return df.values

    def _get_info(self):
        # Provide information on state, action, and reward?
        return {}
        
    def reset(self, *, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action):
        gh_url="https://github.com/DISHDevEx/napp/blob/matt/test_update/napp/open5gs_values/5gSA_no_ues_values_with_nodegroups.yaml"
        dir_name="napp"
        
        if action == 0: # No-Op; do nothing
            logging.info('No action taken for this cycle.')
            pass
        elif action == 1: # Transition to Large instance
            hndl = ActionHandler(get_token(), gh_url, dir_name, {"target_pod": "upf", "values": "Large"})
            hndl.fetch_update_push_upf_sizing()
        elif action == 2: # Transition to Small instance
            hndl = ActionHandler(get_token(), gh_url, dir_name, {"target_pod": "upf", "values": "Small"})
            hndl.fetch_update_push_upf_sizing()
            
        # sleep(self.obs_period * 60) # Sleep for observation period before retrieving next observation
        sleep(10) # For testing
        
        rxtx_value = 3.33e-9 # Rough estimate of dollars per byte over the network
        li_cost = ec2_cost_calculator("m4.large") # Cost of large instance in dollars per hour
        si_cost = ec2_cost_calculator("t3.medium") # Cost of small instance in dollars per hour
        
        observation = self._get_obs()
        # reward over window: revenue generated by rx/tx on network ($) - cost of running large instance ($) - cost of running small instance ($)
        reward = rxtx_value * np.sum(observation) #\
            # -(li_cost / 60 * np.sum(self.obs_space[1]) / len(self.obs_space) * self.window) \
            # -(si_cost / 60 * np.sum(self.obs_space[2]) / len(self.obs_space) * self.window)
        info = self._get_info()
        
        terminated = False # No terminal state for our environment; continuous
        self.step_counter += 1
        truncated = True if self.step_counter % 6 == 0 else False

        # return observation, reward, terminated, truncated, info
        return observation, reward, terminated, truncated, info

    def render(self):
        ...

    def close(self):
        ...
