"""
Module to contain DQN implemented from tensorflow agents.
"""
import numpy as np
import tensorflow as tf

from tf_agents.agents.dqn import dqn_agent
from tf_agents.metrics import tf_metrics
from tf_agents.networks import sequential
from tf_agents.trajectories import trajectory
from tf_agents.specs import tensor_spec
from tf_agents.utils import common
import tf_agents.specs
from tf_agents.trajectories import time_step as ts
from tf_agents.trajectories import trajectory
import tf_agents

class FonprDqn:
    """
    FonprDqn helps to initialize tensorflow Deep-Q-Network agents.

    Attributes
    ----------
        time_step_spec: tf_agents.trajectories.TimeStep(
        discount, observation, reward, step_type)
            Time step specification for agent and NAPP environment.

        action_spec = tf_agents.specs.BoundedArraySpec()
        The number action space for the DQN.

        fc_layer_params: Tuple
            Shape of the tuple defines number of layers. Contents define nuerons.

        learning_rate: int
            Determines the step size for stochastic gradient descent.

        agent: dqn_agent.DqnAgent()
            The TensorFlow dqn agent.
    Methods
    -------
        _create_dqn():
            Private function autocalled during constructor __init__.
            Creates TensorFlow DQN agent using the specifications provided via constructor.

        get_agent():
            Returns dqn_agent.DqnAgent() object built via specifications from constructor.
    """

    def __init__(
        self, time_step_spec, action_spec, learning_rate=1e-3, fc_layer_params=(100, 50)
    ):
        """
        Parameters
        --------- 
            None
        Returns
        ---------
            None
        """
        self.time_step_spec = time_step_spec
        self.action_spec = action_spec
        self.fc_layer_params = fc_layer_params
        self.learning_rate = learning_rate
        self.agent = self._create_dqn()

    def _create_dqn(self):
        """
        This function is called as part of the constructor.
        Returns
        ---------
            dqn_agent.DqnAgent() object built via specifications from constructor.
        """
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
        """
        Public function to allow user of fonpr_dqn class to retrieve agent that has been constructed.
        Returns
        ---------
            dqn_agent.DqnAgent() object built via specifications from constructor.
        """
        return self.agent
