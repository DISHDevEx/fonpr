"""
Module to contain the driver for tensorflow agents to interact with napp. 
The driver utilizes the policy of an agent to interact with the environment.
"""
import time
import logging
from fonpr.action_handler.action_handler import ActionHandler, get_token
from fonpr.utilities.prom_queries import prom_network_upf_interfaces_query
from fonpr.utilities.cost_function import ec2_cost_calculator
from fonpr.advisors.prometheus_client_advisor import PromClient
import tensorflow as tf
import numpy as np
import tf_agents
from tf_agents.trajectories import trajectory
from collections import defaultdict
from typing import List, Tuple

TimeStep = tf_agents.trajectories.TimeStep


class Driver:
    """
    Driver interacts with the NAPP environment using a tf agent policy.
    The drivers main responsibilities are to catalogue action, current state, next state, reward.
    Driver has all the functions needed to make changes in napp as suggested by agent, and to calculate the observations, rewards.

    Attributes
    ----------
        prom_endpoint: str
            "ip:port" for the prometheus server endpoint.

        wait_period = int
            The time interval driver should wait for in seconds to retrive the observations after taking an action.

    Methods
    -------
        reward_function(throughput, infra_cost) -> float:
            Calculates and returns the reward(maximizing profit).
            Uses throughput and infra_cost to calculate reward.

        get_observations() -> List[float]:
            Queries the prometheus server (ip:port) to receive observations.

        get_infra_cost(size) -> float:
            Uses ec2_cost_calculator to get the hourly pricing of the EC2 sizes specified (as a list).

        update_yml(size,gh_url,dir_name)-> None:
            Updates the yml file to modify NAPP upf sizing.

        take_action_get_next_timestep(action_step):
            Takes an action, waits some time, and finds the next state + reward pair.

        drive(max_steps, policy, observer):
            Uses the tf agents policy specified to interact with environment. The interactions,
            or experience, is the placed inside the observer (typically replay buffer for DQN).

    """

    def __init__(self, prom_endpoint="http://10.0.104.52:9090", wait_period=2):
        self.prom_endpoint = prom_endpoint
        self.wait_period = wait_period

    def reward_function(self, throughput, infra_cost) -> float:
        """
        Calculates the reward for the agent to receive based off of throughput and infrastructure cost.

        Parameters
        ----------
            throughput : Float
                The average network transmitted for the last hour from UPF pod.
            infra_cost : float
                The cost of running the ec2 sizing for the UPF pod.

        Returns
        -------
            avg_upf_network: Float
                The average network transmitted for the last hour from UPF pod.

        Notes
        -------
        How the math works:
        (1) Throughput is in bytes/second
        (2) Cost conversion  translates dollars to bytes
        (3) Multiplying 1 and 2: Bytes/Second * Dollars/Bytes --> Dollars/Second
        (4) Now we have to convert the Dollers/Second to Dollars/Hour by using a seconds_to_hours_conversion variable.
        (5) Subtract the result of (4) (which is revenue) by the infra cost (Dollars/Hour) to yield profit.
        """

        # All cost is calculated on an hourly basis
        # Throughput must be in bytes per second.
        # The cost conversion converts 1 gigabyte to 3.33$(https://newsdirect.com/news/mobile-phone-data-costs-7x-more-in-the-us-than-the-uk-158885004?category=Communications).
       
        cost_conversion_coefficient = 3.33 / (10**9)  # 3.33 dollars per 10^9 bytes
        seconds_to_hours_conversion = 3600 / 1  # 3600 seconds per hour
        reward = (throughput) * (
            cost_conversion_coefficient
        ) * seconds_to_hours_conversion - infra_cost
        return reward

    def get_observations(self) -> List[float]:
        """
        Calculates the average rx and tx for eth0 and ogstun interfaces summed across all pod_idxs. Also calculates the hourly cost for all nodes running UPF's.

        Returns
        -------
            observations: List
                [Rx_eth0,Rx_ogstun,Tx_eth0,Tx_ogstun,cost]
        """

        prom_client_advisor = PromClient(self.prom_endpoint)
        prom_client_advisor.set_queries_by_function(prom_network_upf_interfaces_query)
        (
            avg_upf_network_tx,
            avg_upf_network_rx,
            node_sizing,
        ) = prom_client_advisor.run_queries()

        dict_interface_network_tx = defaultdict(list)
        dict_interface_network_rx = defaultdict(list)
        nodes_used_list = []
        dict_node_sizing = {}

        for pod_idx in range(len(avg_upf_network_tx)):
            dict_interface_network_tx[
                avg_upf_network_tx[pod_idx]["metric"]["interface"]
            ].append(float(avg_upf_network_tx[pod_idx]["value"][1]))
            if avg_upf_network_tx[pod_idx]["metric"]["node"] not in nodes_used_list:
                nodes_used_list.append(avg_upf_network_tx[pod_idx]["metric"]["node"])

            dict_interface_network_rx[
                avg_upf_network_rx[pod_idx]["metric"]["interface"]
            ].append(float(avg_upf_network_rx[pod_idx]["value"][1]))
            if avg_upf_network_rx[pod_idx]["metric"]["node"] not in nodes_used_list:
                nodes_used_list.append(avg_upf_network_rx[pod_idx]["metric"]["node"])

        for node in range(len(node_sizing)):
            if node_sizing[node]["metric"]["node"] in nodes_used_list:
                dict_node_sizing[node_sizing[node]["metric"]["node"]] = node_sizing[
                    node
                ]["metric"]["label_beta_kubernetes_io_instance_type"]

        # Sum all the metrics on a per rx interface basis
        dict_interface_network_rx_sum = dict(
            map(lambda x: (x[0], sum(x[1])), dict_interface_network_rx.items())
        )
        # Sum all the metrics on a per tx interface basis
        dict_interface_network_tx_sum = dict(
            map(lambda x: (x[0], sum(x[1])), dict_interface_network_tx.items())
        )

        # Observations to build: rx per interface, tx per interface, total cost

        observations = list(dict_interface_network_rx_sum.values()) + list(
            dict_interface_network_tx_sum.values()
        )

        cost = self.get_infra_cost(list(dict_node_sizing.values()))

        observations = observations + [cost]

        return observations

    def get_infra_cost(self, list_of_sizes) -> float:
        """
        Calculates the hourly cost of the infrastructure based off the categorical value of size.

        Assumes all nodes that existed within window were charged for the entire window duration.

        Parameters
        ----------
            list_of_sizes : list[String]
                Specify the node sizings for upf.
        Returns
        -------
            cost: float
                The hourly cost of running the ec2 sizing for the UPF pod.
        """
        running_cost = 0
        for iterate in range(len(list_of_sizes)):
            running_cost += ec2_cost_calculator(list_of_sizes[iterate])
        return running_cost

    def update_yml(
        self,
        size,
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

    def take_action_get_next_timestep(self, action_step) -> TimeStep:
        """
        Allows drive method to take an action and build the trajectory object for the next (discount, observation, reward, step_type).
        This is the method that allows driver to interact with the environment after time 0.

        Parameters
        ----------
            action_step :  PolicyStep(action, state, info) named tuple
                This is the action suggested by the policy utilizing the driver.
        Returns
        ---------
            next_time_step: tf_agents.trajectories.TimeStep(discount, observation, reward, step_type)
                The timestep trajectory that is created from taking an action.
        """
        if action_step.action == 0:
            self.update_yml(size="Small")

        if action_step.action == 1:
            self.update_yml(size="Large")

        time.sleep(self.wait_period)

        observations = self.get_observations()
        throughput = sum(observations[:-1])
        infra_cost = observations[-1]
        reward = self.reward_function(throughput, infra_cost)

        discount = tf.convert_to_tensor(np.array(1, np.float32))
        observation = tf.convert_to_tensor(np.array(observations, np.float64))
        reward = tf.convert_to_tensor(np.array(reward, np.float32))
        # Step type can be of 0:First, 1:MID, or 2:Final
        step_type = tf.convert_to_tensor(np.array(1, np.int64))

        next_time_step = tf_agents.trajectories.TimeStep(
            discount=discount,
            observation=observation,
            reward=reward,
            step_type=step_type,
        )
        return next_time_step

    def drive(self, max_steps=10, policy=-1, observer=-1) -> TimeStep:
        """
        Allows drive method to take an action and build the trajectory object for the next (discount, observation, reward, step_type).
        This is the method that allows driver to interact with the environment after time 0.

        Parameters
        ----------
            max_steps :  int
                Number of steps to take per episode.

            policy: tf_agents.policies.TFPolicy
                This is the policy that the sits in the driver seat for this driver.

            observer: reverb_utils.ReverbAddTrajectoryObserver
                Replay Buffer to fill up.

        Returns
        ---------
            current_timestep: tf_agents.trajectories.TimeStep(discount, observation, reward, step_type)
                This is the last timestep seen by driver. It returns it at the end of all episodes.

            policy_state: policy.action.state object.
                This is the stat of the policy at the end of all episodes.
        """

        observations = self.get_observations()
        throughput = sum(observations[:-1])
        infra_cost = observations[-1]
        reward = self.reward_function(throughput, infra_cost)

        discount = tf.convert_to_tensor(np.array(1, np.float32))
        observation = tf.convert_to_tensor(np.array(observations, np.float64))
        reward = tf.convert_to_tensor(np.array(reward, np.float32))
        # Step type can be of 0:First, 1:MID, or 2:Final
        step_type = tf.convert_to_tensor(np.array(0, np.int64))

        current_timestep = tf_agents.trajectories.TimeStep(
            discount=discount,
            observation=observation,
            reward=reward,
            step_type=step_type,
        )

        for step in range(max_steps):
            if step == 0:
                policy_state = policy.get_initial_state(1)

            # Action_step is a PolicyStep(action, state, info) object.
            action_step = policy.action(current_timestep, policy_state)

            next_time_step = self.take_action_get_next_timestep(action_step)
            action_step_with_previous_state = action_step._replace(state=policy_state)
            traj = trajectory.from_transition(
                current_timestep, action_step_with_previous_state, next_time_step
            )
            observer(traj)
            current_timestep = next_time_step
            policy_state = action_step.state

        return current_timestep
