import reverb

"""
Create a replay buffer on a per agent basis. The replay buffer uses the agent 
specifications 
"""


class ReplayBuffer:
    
    def __init__(self,agent):
        self.agent = agent
        
    def create_replay_buffer(self):
        
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