"""
Create a replay buffer on a per agent basis. The replay buffer uses the agent 
specifications 
"""
from tf_agents.specs import tensor_spec
from tf_agents.replay_buffers import reverb_replay_buffer
from tf_agents.replay_buffers import reverb_utils
import reverb

class ReplayBuffer:
    
    def __init__(self,agent,replay_buffer_max_length = 100000,table_name = 'uniform_table'):
        
        self.agent = agent
        self.replay_buffer_max_length=replay_buffer_max_length
        self.table_name = table_name
        
        self.replay_buffer_signature, self.table, self.reverb_server,self.replay_buffer,self.rb_observer = self.create_replay_buffer()
        
        
    def create_replay_buffer(self):
    

        replay_buffer_signature = tensor_spec.from_spec(
          self.agent.collect_data_spec)
        replay_buffer_signature = tensor_spec.add_outer_dim(
        replay_buffer_signature)
        
        
        table = reverb.Table(
        self.table_name,
        max_size=self.replay_buffer_max_length,
        sampler=reverb.selectors.Uniform(),
        remover=reverb.selectors.Fifo(),
        rate_limiter=reverb.rate_limiters.MinSize(1),
        signature=replay_buffer_signature)
        
        reverb_server = reverb.Server([table])
        
        replay_buffer = reverb_replay_buffer.ReverbReplayBuffer(
        self.agent.collect_data_spec,
        table_name=self.table_name,
        sequence_length=2,
        local_server=reverb_server)
        
        rb_observer = reverb_utils.ReverbAddTrajectoryObserver(
        replay_buffer.py_client,
        self.table_name,
        sequence_length=2)
        
        return replay_buffer_signature, table, reverb_server, rb_observer