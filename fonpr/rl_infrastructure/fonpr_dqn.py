"""
Module to contain DQN implemented from tensorflow agents.
"""
import numpy as np
import tensorflow as tf

from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import py_driver
from tf_agents.environments import suite_gym
from tf_agents.environments import tf_py_environment
from tf_agents.eval import metric_utils
from tf_agents.metrics import tf_metrics
from tf_agents.networks import sequential
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


class FonprDqn:
    """FONPR DQN will utilize tensorflow agents to construct a deep Q network.


    Attributes:
        ##fill in
    """

    def __init__(
        self, time_step_spec, action_spec, learning_rate=1e-3, fc_layer_params=(100, 50)
    ):
        """
        Parameters
        ---------
        Returns
        ---------
            None
        """
        self.time_step_spec = time_step_spec
        self.action_spec = action_spec
        self.fc_layer_params = fc_layer_params
        self.learning_rate = learning_rate
        self.agent = self.create_dqn()

    def create_dqn(self):
        action_tensor_spec = tensor_spec.from_spec(self.action_spec)
        num_actions = action_tensor_spec.maximum - action_tensor_spec.minimum + 1

        # Define a helper function to create Dense layers configured with the right
        # activation and kernel initializer.
        def dense_layer(num_units):
            return tf.keras.layers.Dense(
                num_units,
                activation=tf.keras.activations.relu,
                kernel_initializer=tf.keras.initializers.VarianceScaling(
                    scale=2.0, mode="fan_in", distribution="truncated_normal"
                ),
            )

        # QNetwork consists of a sequence of Dense layers followed by a dense layer
        # with `num_actions` units to generate one q_value per available action as
        # its output.
        dense_layers = [dense_layer(num_units) for num_units in self.fc_layer_params]
        q_values_layer = tf.keras.layers.Dense(
            num_actions,
            activation=None,
            kernel_initializer=tf.keras.initializers.RandomUniform(
                minval=-0.03, maxval=0.03
            ),
            bias_initializer=tf.keras.initializers.Constant(-0.2),
        )
        q_net = sequential.Sequential(dense_layers + [q_values_layer])

        optimizer = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)

        train_step_counter = tf.Variable(0)

        agent = dqn_agent.DqnAgent(
            self.time_step_spec,
            self.action_spec,
            q_network=q_net,
            optimizer=optimizer,
            td_errors_loss_fn=common.element_wise_squared_loss,
            train_step_counter=train_step_counter,
        )
        return agent

    def get_agent(self):
        return self.agent
