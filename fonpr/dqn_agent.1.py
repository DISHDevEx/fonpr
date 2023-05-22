"""
Module to contain respons agent. It is also the module that runs as a container in eks.
"""
from __future__ import absolute_import, division, print_function
import time
import logging
from collections import defaultdict
from rl_infrastructure import FonprDqn
from rl_infrastructure import ReplayBuffer
import argparse
from vizier.service import clients
from vizier.service import pyvizier as vz

import numpy as np
import tensorflow as tf

from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import py_driver
from tf_agents.environments import suite_gym
from tf_agents.environments import tf_py_environment
from tf_agents.eval import metric_utils
from tf_agents.metrics import tf_metrics
from tf_agents.networks import sequential
from tf_agents.policies import py_tf_eager_policy
from tf_agents.policies import random_tf_policy
from tf_agents.replay_buffers import reverb_replay_buffer
from tf_agents.replay_buffers import reverb_utils
from tf_agents.trajectories import trajectory
from tf_agents.specs import tensor_spec
from tf_agents.utils import common
import tf_agents.specs
from tf_agents.policies import py_policy
from tf_agents.trajectories import time_step as ts
from tf_agents.trajectories import trajectory
from tf_agents.typing import types
import tf_agents

import numpy as np
import reverb


            

    


if __name__ == "__main__":
    """
    DQN agent logic: receive throughput, cost to make a reward. Based off reward specify sizing of the upf pod.
    """

    # Instantiate some logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Launching FONPR DQN Agent")


    
    #################CREATE DRIVER METRICS#################
    num_iterations = 20000 # @param {type:"integer"}
    
    initial_collect_steps = 100  # @param {type:"integer"}
    collect_steps_per_iteration =   1# @param {type:"integer"}
    replay_buffer_max_length = 100000  # @param {type:"integer"}
    
    batch_size = 64  # @param {type:"integer"}
    learning_rate = 1e-3  # @param {type:"number"}
    log_interval = 200  # @param {type:"integer"}
    
    num_eval_episodes = 10  # @param {type:"integer"}
    eval_interval = 1000  # @param {type:"integer"}
    
    ##############CREATE AGENT#################
    discount = tf_agents.specs.BoundedTensorSpec((),np.float32,name='discount',minimum=0,maximum = 1)
    observation = tf_agents.specs.BoundedTensorSpec((1,),np.float32,name='observation',minimum=[0],maximum = [1000000000])
    reward = tf_agents.specs.TensorSpec((),np.float32,name='reward')
    step_type = tf_agents.specs.TensorSpec((),np.float32,name='step_type')
    time_step_spec = tf_agents.trajectories.TimeStep(discount = discount,observation = observation, reward=reward, step_type = step_type )
    action_spec = tf_agents.specs.BoundedArraySpec((), np.int64, name='action', minimum=0, maximum=2)
    
    agent = create_dqn(time_step_spec,action_spec)
    agent.initialize()
    
    #################CREATE POLICY#########################
    eval_policy = agent.policy
    collect_policy = agent.collect_policy
    random_policy = random_tf_policy.RandomTFPolicy(time_step_spec,
                                                action_spec)
                                                
    #################CREATE REPLAY BUFFER#########################


    ############ RUN DRIVERS #######################

    ##RANDOM POLICY 
    ##run random policy to fill up replay buffer
    driver(max_steps=10,policy = py_tf_eager_policy.PyTFEagerPolicy(
      random_policy, use_tf_function=True),observer=rb_observer)
      
      
    dataset = replay_buffer.as_dataset(
    num_parallel_calls=3,
    sample_batch_size=batch_size,
    num_steps=2).prefetch(3)
    
    iterator = iter(dataset)
    
    ##DQN
    ##training the agent
    agent.train = common.function(agent.train)
    agent.train_step_counter.assign(0)
    
    ##run 10 episodes
    for episode in range(10):
        #create a driver to collect experience
        ts = driver(max_steps=10, policy = py_tf_eager_policy.PyTFEagerPolicy(
          agent.collect_policy, use_tf_function=True),observer=rb_observer)
          
        experience, unused_info = next(iterator)
        
        train_loss = agent.train(experience).loss
        
        step = agent.train_step_counter.numpy()
    
        print(step)
    
    