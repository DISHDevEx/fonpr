"""
Module to contain respons agent. It is also the module that runs as a container in eks.
"""
import logging

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

if __name__ == "__main__":
    """
    DQN main module. Build DQN, Random Policy, Replay Buffer, and Driver. Then allow the random policy and DQN to use Driver to fill up 
    replay buffer. 
    """
    
    # Instantiate some logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Launching FONPR DQN Agent")
    
    #################Define Hyperperameters#################
    
    num_iterations = 20000 # @param {type:"integer"}
    
    initial_collect_steps = 100  # @param {type:"integer"}
    collect_steps_per_iteration = 1# @param {type:"integer"}
    replay_buffer_max_length = 100000  # @param {type:"integer"}
    
    batch_size = 64  # @param {type:"integer"}
    learning_rate = 1e-3  # @param {type:"number"}
    log_interval = 200  # @param {type:"integer"}
    
    num_eval_episodes = 10  # @param {type:"integer"}
    eval_interval = 1000  # @param {type:"integer"}
    
    fc_layer_params = (100,50)
    
    logging.info("Hyperperamters Established Successfully")
    
    #################CREATE AGENT SPECIFICATIONS#################
    
    discount = tf_agents.specs.BoundedTensorSpec((),np.float32,name='discount',minimum=0,maximum = 1)
    observation = tf_agents.specs.BoundedTensorSpec((1,),np.float32,name='observation',minimum=[0],maximum = [1000000000])
    reward = tf_agents.specs.TensorSpec((),np.float32,name='reward')
    step_type = tf_agents.specs.TensorSpec((),np.float32,name='step_type')
    time_step_spec = tf_agents.trajectories.TimeStep(discount = discount,observation = observation, reward=reward, step_type = step_type )
    action_spec = tf_agents.specs.BoundedArraySpec((), np.int64, name='action', minimum=0, maximum=2)
    
    logging.info("Agent Specifications Established Successfully")
    
    #################CREATE DQN AGENT#################
  
    agent_creator = FonprDqn(time_step_spec,action_spec,learning_rate,fc_layer_params)
    agent = agent_creator.get_agent()
    agent.initialize()
    
    logging.info("DQN Agent Established Successfully")
    
    #################CREATE RANDOM POLICY#################
    
    random_policy = random_tf_policy.RandomTFPolicy(time_step_spec,
                                                action_spec)
                                                
    logging.info("Random Agent Established Successfully") 
    
    #################CREATE REPLAY BUFFER#################
    
    replay_buffer = ReplayBuffer(agent=agent,replay_buffer_max_length=replay_buffer_max_length)
    iterator = replay_buffer.get_replay_buffer_as_iterator()
    
    logging.info("Replay Buffer Established Successfully")
    
    #################CREATE DRIVER#################
    
    driver = Driver()
    
    logging.info("Driver Established Successfully")
    
    #################RUN DRIVERS#################

    logging.info("Running Random Policy")
  
    ##run random policy to fill up replay buffer
    driver.drive(max_steps=10,policy = py_tf_eager_policy.PyTFEagerPolicy(
      random_policy, use_tf_function=True),observer=replay_buffer.rb_observer)
      
    logging.info("Random Policy Finished Running")
    

    ##DQN
    ##training the agent
    agent.train = common.function(agent.train)
    agent.train_step_counter.assign(0)
    
    #Run Episodes, each with Steps. 
    #Agent trains once per episode after a predefined number of steps. 
    logging.info("Running DQN Actions and training sequence")
    for episode in range(10):
        #create a driver to collect experience
        ts = driver.drive(max_steps=10, policy = py_tf_eager_policy.PyTFEagerPolicy(
          agent.collect_policy, use_tf_function=True),observer=replay_buffer.rb_observer)
          
        experience, unused_info = next(iterator)
        print("length of training set",len(experience))
        train_loss = agent.train(experience).loss
        
        step = agent.train_step_counter.numpy()
    
        print("Times agent has trained", step)
        print("Replay buffer size:", replay_buffer.replay_buffer.num_frames())
        
    
    