"""
Script for running a Soft Actor Critic based agent in using the FONPR_Env Interface.
"""

from interfaces import FONPR_Env
from ray.tune.logger import pretty_print
from ray.rllib.algorithms import sac

if __name__ == "__main__":
    
    config = (
        sac.SACConfig()
        .environment(env = FONPR_Env, env_config={'obs_period':1})
        .rollouts(num_rollout_workers=0)
        .framework('tf2')
        .reporting(min_sample_timesteps_per_iteration=30)
        .training(train_batch_size=8, num_steps_sampled_before_learning_starts=16)
        )
    config.replay_buffer_config.update(capacity=32)
    agent = config.build()
    
    counter = 0
    while True:
        counter += 1
        print(f'---- Training cycle {counter} started ----')
        agent.train()
        print(f'---- Training cycle {counter} complete ----')