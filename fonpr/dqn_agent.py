"""
Module to contain respons agent. It is also the module that runs as a container in eks.
"""
from __future__ import absolute_import, division, print_function
import time
import logging
from collections import defaultdict
from advisors import PromClient
from utilities import prom_network_upf_query, ec2_cost_calculator
from action_handler import ActionHandler, get_token
import argparse
import logging
from vizier.service import clients
from vizier.service import pyvizier as vz

import numpy as np
import reverb

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


def reward_function(throughput, infra_cost):
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


def get_throughput():
    """
    Calculates the average network bytes transmitted from the UPF pod for the last hour.

    Returns
    -------
        avg_upf_network: float
            The average network transmitted for the last hour from UPF pod.
    """

    # Set the prometheus client endpoint for the prometheus server in Respons-Nuances.
    prom_client_advisor = PromClient("http://10.0.104.52:9090")
    prom_client_advisor.set_queries_by_function(prom_network_upf_query)
    avg_upf_network = prom_client_advisor.run_queries()
    avg_upf_network = float(avg_upf_network[0][0]["value"][1])
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
            The hourly cost of running the ec2 sizing for the UPF pod.
    """

    if size == "Small":
        return ec2_cost_calculator("t3.medium")
    if size == "Large":
        return ec2_cost_calculator("m4.large")


def update_yml(
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
    
    
    
def create_dqn(time_step_spec, action_spec):
    fc_layer_params = (100, 50)
    action_tensor_spec = tensor_spec.from_spec(action_spec)
    num_actions = action_tensor_spec.maximum - action_tensor_spec.minimum + 1
    
    # Define a helper function to create Dense layers configured with the right
    # activation and kernel initializer.
    def dense_layer(num_units):
      return tf.keras.layers.Dense(
          num_units,
          activation=tf.keras.activations.relu,
          kernel_initializer=tf.keras.initializers.VarianceScaling(
              scale=2.0, mode='fan_in', distribution='truncated_normal'))
    
    # QNetwork consists of a sequence of Dense layers followed by a dense layer
    # with `num_actions` units to generate one q_value per available action as
    # its output.
    dense_layers = [dense_layer(num_units) for num_units in fc_layer_params]
    q_values_layer = tf.keras.layers.Dense(
        num_actions,
        activation=None,
        kernel_initializer=tf.keras.initializers.RandomUniform(
            minval=-0.03, maxval=0.03),
        bias_initializer=tf.keras.initializers.Constant(-0.2))
    q_net = sequential.Sequential(dense_layers + [q_values_layer])
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    
    train_step_counter = tf.Variable(0)
    
    agent = dqn_agent.DqnAgent(
        time_step_spec,
        action_spec,
        q_network=q_net,
        optimizer=optimizer,
        td_errors_loss_fn=common.element_wise_squared_loss,
        train_step_counter=train_step_counter)
    return agent
    

def take_action_get_next_timestep(action):
    

   
    
def driver(max_steps = 10, max_episodes=10, policy, observer):
    
    throughput = get_throughput()
    infra_cost = get_infra_cost()
    reward = reward_function(throughput,infra_cost)
    
    discount  = np.array(1,np.float32)
    observation = np.array([throughput],np.float32)
    reward = np.array(reward,np.float32)
    step_type = np.array(0,np.float32)
    
    current_timestep = tf_agents.trajectories.TimeStep(discount = discount,observation = observation, reward=reward, step_type = step_type )
    
    for episode in range(max_episodes):
        for step in range(max_steps):
            
            if(step == 0):
                policy_state = policy.get_initial_state(1)
                
            action_step = policy.action(current_timestep,policy_state)
            next_time_step = 
            
            

    


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
    action_spec = action_spec = tf_agents.specs.BoundedArraySpec((), np.int64, name='action', minimum=0, maximum=2)
    
    agent = create_dqn(time_step_spec,action_spec)
    agent.initialize()
    
    #################CREATE POLICY#########################
    eval_policy = agent.policy
    collect_policy = agent.collect_policy
    random_policy = random_tf_policy.RandomTFPolicy(time_step_spec,
                                                action_spec)
                                                
    #################CREATE REPLAY BUFFER#########################
    table_name = 'uniform_table'
    replay_buffer_signature = tensor_spec.from_spec(
      agent.collect_data_spec)
    replay_buffer_signature = tensor_spec.add_outer_dim(
    replay_buffer_signature)
    
    table = reverb.Table(
    table_name,
    max_size=replay_buffer_max_length,
    sampler=reverb.selectors.Uniform(),
    remover=reverb.selectors.Fifo(),
    rate_limiter=reverb.rate_limiters.MinSize(1),
    signature=replay_buffer_signature)
    
    reverb_server = reverb.Server([table])
    
    replay_buffer = reverb_replay_buffer.ReverbReplayBuffer(
    agent.collect_data_spec,
    table_name=table_name,
    sequence_length=2,
    local_server=reverb_server)
    
    rb_observer = reverb_utils.ReverbAddTrajectoryObserver(
    replay_buffer.py_client,
    table_name,
    sequence_length=2)
    ############ RUN DRIVER #######################

    print("COLLECT POLICY",collect_policy)

    # ##Run DQN
    # for i in range(15):
    #     logging.info("Executing update cycle.")

        