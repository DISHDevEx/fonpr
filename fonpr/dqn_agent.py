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
    replay buffer. Use replay buffer to train in between episodes.
    """

    # Instantiate some logging.
    logging.basicConfig(level=logging.INFO)
    logging.info("Launching FONPR DQN Agent")

    #################DEFINE HYPERPERAMETERS#################

    ##TRAINING HYPERPERAMETERS

    # Random policy steps to take in order to fill up the replay buffer.
    initial_collect_steps = 100

    # Num_episodes for the DQN to run.
    num_episodes = 200

    # Number_of_interactions the DQN makes per episode.
    number_of_interactions = 10

    # The length of the replay buffer,before a fifo popping mechanism gets implemented.
    replay_buffer_max_length = 100000

    # Number of samples to ingest per training episode.
    batch_size = 20

    # Number of consecutive samples to bind together into a single sample for training.
    sequence_length = 2

    # Time in seconds to wait in between interactions to allow action to effect env.
    wait_period_between_interactions = 900

    ##DQN ARCHITECTURE

    # Shape of the tuple defines number of layers. Contents define nuerons.
    fc_layer_params = (20, 20)

    # Determines the step size for stochastic gradient descent.
    learning_rate = 1e-3

    logging.info("Hyperperamters Established Successfully")

    #################CREATE AGENT SPECIFICATIONS#################

    discount = tf_agents.specs.BoundedTensorSpec(
        (), np.float32, name="discount", minimum=0, maximum=1
    )

    # Observation: [Rx_eth0[1hr:],Rx_ogstun[1hr:],Tx_eth0[1hr:],Tx_ogstun[1hr:],cost]
    observation = tf_agents.specs.BoundedTensorSpec(
        (5,),
        np.float64,
        name="observation",
        minimum=[0, 0, 0, 0, 0],
        maximum=[10000000000, 10000000000, 10000000000, 10000000000, 35],
    )

    reward = tf_agents.specs.TensorSpec((), np.float32, name="reward")

    step_type = tf_agents.specs.TensorSpec((), np.int64, name="step_type")

    time_step_spec = tf_agents.trajectories.TimeStep(
        discount=discount, observation=observation, reward=reward, step_type=step_type
    )

    action_spec = tf_agents.specs.BoundedArraySpec(
        (), dtype=np.int64, name="action", minimum=0, maximum=1
    )

    logging.info("Agent Specifications Established Successfully")

    #################CREATE DQN AGENT#################

    agent_creator = FonprDqn(
        time_step_spec, action_spec, learning_rate, fc_layer_params
    )

    agent = agent_creator.get_agent()

    agent.initialize()

    logging.info("DQN Agent Established Successfully")

    #################CREATE RANDOM POLICY#################

    random_policy = random_tf_policy.RandomTFPolicy(time_step_spec, action_spec)

    logging.info("Random Agent Established Successfully")

    #################CREATE REPLAY BUFFER#################

    replay_buffer = ReplayBuffer(
        agent=agent,
        replay_buffer_max_length=replay_buffer_max_length,
        sequence_length=sequence_length,
    )

    iterator = replay_buffer.get_replay_buffer_as_iterator()

    logging.info("Replay Buffer Established Successfully")

    #################CREATE DRIVER#################

    driver = Driver(wait_period=wait_period_between_interactions)

    logging.info("Driver Established Successfully")

    #################RUN DRIVERS#################

    logging.info("Running Random Policy")

    # Run random policy to fill up replay buffer.
    driver.drive(
        max_steps=initial_collect_steps,
        policy=py_tf_eager_policy.PyTFEagerPolicy(random_policy, use_tf_function=True),
        observer=replay_buffer.rb_observer,
    )

    logging.info("Random Policy Finished Running")

    # DQN -- Training the agent.
    agent.train = common.function(agent.train)
    agent.train_step_counter.assign(0)

    # Run Episodes, each with Steps.
    # Agent trains once per episode after a predefined number of steps.
    logging.info("Running DQN Actions and training sequence")
    for episode in range(num_episodes):
        # Run driver to collect experience.
        ts = driver.drive(
            max_steps=number_of_interactions,
            policy=py_tf_eager_policy.PyTFEagerPolicy(
                agent.collect_policy, use_tf_function=True
            ),
            observer=replay_buffer.rb_observer,
        )

        experience, unused_info = next(iterator)

        train_loss = agent.train(experience).loss

        step = agent.train_step_counter.numpy()

        logging.info(f"Number of episodes complete: {step}")
        logging.info(f"Agent training loss after {step} episodes: {train_loss} ")
