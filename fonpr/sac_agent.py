"""
Script for running a Soft Actor Critic based agent using the FONPR_Env Interface.
"""

from interfaces import FONPR_Env
from ray.tune.logger import pretty_print
from ray.rllib.algorithms import sac
import logging

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    
    # Setting observation period to 1 for initial training and evaluation
    env_config={'render_mode':None, 'window':15, 'sample_rate':4, 'obs_period':1}
    
    # Updating default configs for initial training and evaluation
    config = (
        sac.SACConfig()
        .environment(env=FONPR_Env, env_config=env_config)
        .rollouts(num_rollout_workers=0) # Not parallelizable in Open5GS; using just the local worker
        .framework('tf2')
        .reporting(min_sample_timesteps_per_iteration=30)
        .training(train_batch_size=8, num_steps_sampled_before_learning_starts=16)
        )
    config.replay_buffer_config.update(capacity=32) # Keeping small for initial experiments
    agent = config.build()
    
    counter = 0
    while True:
        counter += 1
        logging.info(f'---- Training cycle {counter} started ----')
        agent.train()
        logging.info(f'---- Training cycle {counter} complete ----')