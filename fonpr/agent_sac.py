"""
Script for running a Soft Actor Critic based agent using the FONPR_Env Interface.
"""

from ray_infrastructure import FONPR_Env
from ray.tune.logger import pretty_print
from ray.rllib.algorithms import sac
import logging
import subprocess
import argparse

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    logging.info("Launching FONPR SAC Agent")

    parser = argparse.ArgumentParser(
        prog="FONPR_Agent",
        description="Executes policy implementation for closed loop 5G network control.",
    )

    parser.add_argument(
        "--window",
        type=int,
        default=15,
        required=False,
        help="How far back in time to look for an observation, in minutes.",
    )
    parser.add_argument(
        "--sample_rate",
        type=int,
        default=4,
        required=False,
        help="Samples per minute.",
    )
    parser.add_argument(
        "--obs_period",
        type=int,
        default=1,
        required=False,
        help="Time in minutes between executions of the policy logic.",
    )
    parser.add_argument(
        "--prom_endpoint",
        type=str,
        default="http://10.0.114.131:9090",
        required=False,
        help="Override default Prometheus server IP address / port.",
    )
    parser.add_argument(
        "--s3_checkpoint_uri",
        type=str,
        default="s3://respons-agent-checkpoints/sac_v0.0.0/",
        required=False,
        help="Specify path to target S3 bucket for model checkpointing.",
    )
    parser.add_argument(
        "--gh_url",
        type=str,
        default="https://github.com/DISHDevEx/napp/blob/agent-sac/napp/open5gs_values/5gSA_no_ues_values_with_nodegroups.yaml",
        required=False,
        help="Specify path to target value.yaml file on GitHub.",
    )
    parser.add_argument(
        "--dir_name",
        type=str,
        default="napp",
        required=False,
        help="Specify root directory of value.yaml path in repo.",
    )
    
    args = parser.parse_args()
    
    env_config={
        'render_mode': None,
        'window': args.window,
        'sample_rate': args.sample_rate,
        'obs_period': args.obs_period,
        'prom_endpoint': args.prom_endpoint,
        'gh_url': args.gh_url,
        'dir_name': args.dir_name
    }

    # Updating default configs for initial training and evaluation
    config = (
        sac.SACConfig()
        .environment(env=FONPR_Env, env_config=env_config)
        .rollouts(num_rollout_workers=0) # Not parallelizable in Open5GS; using just the local worker
        .framework('tf2')
        .reporting(min_sample_timesteps_per_iteration=10)
        .training(train_batch_size=8, num_steps_sampled_before_learning_starts=8, gamma=.9)
        )
    config.replay_buffer_config.update(capacity=128)
    agent = config.build()
    
    counter = 0
    while True:
        counter += 1
        logging.info(f'---- Training cycle {counter} started ----')
        agent.train()
        logging.info(f'---- Training cycle {counter} complete ----')
        if (counter - 1) % 6 == 0:
            path_to_checkpoint = agent.save()
            logging.info(
                'An Algorithm checkpoint has been created inside directory:'
                f'"{path_to_checkpoint}"'
                )
            # Copy checkpoints over to s3
            subprocess.run(['aws', 's3', 'sync', '/root/ray_results/', args.s3_checkpoint_uri])