"""
Create a replay buffer on a per agent basis. The replay buffer uses the agent 
specifications.
"""
from tf_agents.specs import tensor_spec
from tf_agents.replay_buffers import reverb_replay_buffer
from tf_agents.replay_buffers import reverb_utils
import reverb


class ReplayBuffer:
    """
    ReplayBuffer helps to a reverb server to provide replay buffer to agent. This helps the agent train on random samples
    Independantly and Identically Distributed (IID) from the replay buffer. 
    
    Attributes
    ----------
        agent: dqn_agent.DqnAgent()
            The TensorFlow dqn agent. 
            
        replay_buffer_max_length: Int
            The length of the replay buffer,before a fifo popping mechanism gets implemented.
            
        table_name: String
            Name of the reverb server table to be implemented. 
                
        sequence_length = Int
            Number of consecutive samples to bind together into a single sample for training.
        
        replay_buffer_signature: agent.collect_data_spec
            Defines the structure or signature of the replay buffer.  
            
        table: reverb.Table
            This is the underlying table that the replay buffer will interact with. 
            
        reverb_server: reverb.Server([table])
            Turns the table into a server(allows api interactions)

        replay_buffer: reverb_replay_buffer.ReverbReplayBuffer(reverb_server)
            Turns the server into a replay buffer. 
            
        rb_observer: reverb_utils.ReverbAddTrajectoryObserver
            Allows driver to use the replay buffer as an observer. rb_observer has the ability 
            to collect experience. 

    Methods
    -------
        _create_replay_buffer():
            Private function autocalled during constructor __init__. 
            Creates replay_buffer_signature,table,reverb_server,replay_buffer,rb_observer.

        get_replay_buffer_as_dataset():
            Returns replay buffer as dataset. 
        
        get_replay_buffer_as_iterator():
            Returns a replay buffer as dataset, with an iterator wrapper. 
    """
    def __init__(
        self,
        agent,
        replay_buffer_max_length=100000,
        table_name="uniform_table",
        sequence_length=2,
    ):
        self.agent = agent
        self.replay_buffer_max_length = replay_buffer_max_length
        self.table_name = table_name
        self.sequence_length = sequence_length
        (
            self.replay_buffer_signature,
            self.table,
            self.reverb_server,
            self.replay_buffer,
            self.rb_observer,
        ) = self._create_replay_buffer()

    def _create_replay_buffer(self):
        """
        This function is called as part of the constructor. 
        Creates all of the components of the replay buffer. 
        Returns
        ---------
        replay_buffer_signature: agent.collect_data_spec
            Defines the structure or signature of the replay buffer.  
            
        table: reverb.Table
            This is the underlying table that the replay buffer will interact with. 
            
        reverb_server: reverb.Server([table])
            Turns the table into a server(allows api interactions)

        replay_buffer: reverb_replay_buffer.ReverbReplayBuffer(reverb_server)
            Turns the server into a replay buffer. 
            
        rb_observer: reverb_utils.ReverbAddTrajectoryObserver
            Allows driver to use the replay buffer as an observer. rb_observer has the ability 
            to collect experience. 
        """
        replay_buffer_signature = tensor_spec.from_spec(self.agent.collect_data_spec)
        replay_buffer_signature = tensor_spec.add_outer_dim(replay_buffer_signature)

        table = reverb.Table(
            self.table_name,
            max_size=self.replay_buffer_max_length,
            sampler=reverb.selectors.Uniform(),
            remover=reverb.selectors.Fifo(),
            rate_limiter=reverb.rate_limiters.MinSize(1),
            signature=replay_buffer_signature,
        )

        reverb_server = reverb.Server([table])

        replay_buffer = reverb_replay_buffer.ReverbReplayBuffer(
            self.agent.collect_data_spec,
            table_name=self.table_name,
            sequence_length=self.sequence_length,
            local_server=reverb_server,
        )

        rb_observer = reverb_utils.ReverbAddTrajectoryObserver(
            replay_buffer.py_client,
            self.table_name,
            sequence_length=self.sequence_length,
        )

        return replay_buffer_signature, table, reverb_server, replay_buffer, rb_observer

    def get_replay_buffer_as_dataset(self, num_parallel_calls=3, batch_size=10):
        """
        Returns replay buffer as dataset. 
        
        Returns
        ---------
        dataset: replay_buffer.as_dataset()
        """
        dataset = self.replay_buffer.as_dataset(
            num_parallel_calls=num_parallel_calls,
            sample_batch_size=batch_size,
            num_steps=self.sequence_length,
        ).prefetch(3)

        return dataset

    def get_replay_buffer_as_iterator(self, num_parallel_calls=3, batch_size=10):
        """
        Returns replay buffer as dataset with an iterator wrapper. 
        
        Returns
        ---------
        iterator: iter(replay_buffer.as_dataset())
        """
        dataset = self.get_replay_buffer_as_dataset(num_parallel_calls, batch_size)
        iterator = iter(dataset)
        return iterator
