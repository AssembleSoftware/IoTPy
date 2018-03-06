import sys
import logging
"""
Code for Paxos using IoTPy

The proposers propose values to be accepted by the acceptors. They will 
continue to propose values until a value is accepted by the majority of 
acceptors. The time step behavior moves forward the time which is also the
proposer's value that they can propose. There is a daemon for the messages
from the proposers to the acceptors and another for the messages from the
acceptors to the proposers. It can either duplicate, delete, or leave a 
message alone each with set probabilities as a form of fault injection.

We don't have learners because once the acceptors are in a stable state,
learning the stable state is very straightforward.

You can modify the number of proposers and acceptors to test different cases.
"""
import os
import random
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

from stream import Stream, _no_value, _multivalue
from merge import blend
from op import map_element

# num_proposers: Number of proposers
# num_acceptors: Number of acceptors
# proposer_out_streams: Array of streams from proposers
# acceptor_out_streams: Array of streams from acceptors
# proposer_in_streams: Array of streams to proposers
# acceptor_in_streams: Array of streams to acceptors
num_proposers = 2
num_acceptors = 3
majority = 1 + num_acceptors/2
proposer_out_streams = [
    Stream('proposer_out_'+str(i)) for i in range(num_proposers)]
acceptor_out_streams = [
    Stream('acceptor_out_'+str(i)) for i in range(num_acceptors)]
time_step_stream = Stream('time_step')
in_streams_for_each_proposer = acceptor_out_streams
in_streams_for_each_proposer.append(time_step_stream)
in_streams_for_time_step = in_streams_for_each_proposer
daemons_acceptors_out_streams = [
    Stream('daemons_acceptor_out_'+str(i)) for i in range(num_acceptors)]
daemons_proposers_out_streams = [
    Stream('daemons_proposer_out_'+str(i)) for i in range(num_proposers)]

logging.basicConfig(filename='agent.log', filemode='w', level=logging.DEBUG)

def random_number():
    """
    Returns an integer random number which is used to drive time steps.

    """
    return random.randint(1, 10)

def delete(v, deletion_probability=0.1, duplication_probability=0.1):
    random_number = random.random()
    # Delete message
    if random_number < deletion_probability:
        return _no_value
    # Duplicate message
    elif (
            random_number <
            deletion_probability + duplication_probability
            ):
        return _multivalue([v, v])
    # Leave message as is
    else:
        return v


def proposer_behavior(input_msg, state):
    logging.info('proposer input_msg is ' + str(input_msg))
    my_id, my_prepare_timestamp, time_to_next_prepare_msg, dict_of_acceptors = state
    logging.info('proposer id is ' + str(my_id))
    logging.info('prepare timestamp is ' + str(my_prepare_timestamp))
    logging.info('time remaining to next prepare message is ' + str(time_to_next_prepare_msg))
    # my_id is the id of this proposer
    # my_prepare_timestamp is the time of last prepare message
    # sent by this proposer.
    # time_to_next_prepare_msg is the time remaining before
    # this proposer sends another prepare message.
    # dict_of_acceptors is a dict in which a key is an acceptor id and
    # the value is the granted message from that acceptor.
    msg_name = input_msg[0]
    # The first value in every message is the name of the message
    if msg_name == 'time_step':
        current_time = input_msg[1]
        time_to_next_prepare_msg -= 1
        if time_to_next_prepare_msg == 0:
            # Send prepare message
            my_prepare_timestamp = current_time
            output_msg = ('prepare', my_prepare_timestamp, my_id)
            time_to_next_prepare_msg = current_time + random_number()
            # Clear dict of acceptors because granted messages for earlier
            # prepare timestamps no longer apply
            dict_of_acceptors = {}
            next_state = \
              my_id, my_prepare_timestamp, time_to_next_prepare_msg, dict_of_acceptors
            return output_msg, next_state
        else:
            next_state = \
              my_id, my_prepare_timestamp, time_to_next_prepare_msg, dict_of_acceptors
            return _no_value, next_state
    elif msg_name == 'granted':
        # If a majority of acceptors have sent granted messages with the same
        # timestamp as this proposer's prepare timestamp then send accept messages
        acceptor_id, prepare_timestamp, prepare_proposer, \
          accept_timestamp, accept_proposer = input_msg[1:]
        if (prepare_timestamp, prepare_proposer) == (my_prepare_timestamp, my_id):
            # Since timestamps are equal, include the acceptor that sent this 
            # granted message in the dict of acceptors,
            dict_of_acceptors[acceptor_id] = (accept_timestamp, accept_proposer)
            if len(dict_of_acceptors) >= majority:
                max_accept_timestamp = max(dict_of_acceptors.values()[0])
                # Find the max id of the acceptor who sent a grant with the
                # max accept timestamp.
                max_accept_id = max(
                    acceptor_values[1] for acceptor_values in dict_of_acceptors.values()
                    if acceptor_values[0] == max_accept_timestamp
                    )
                next_state = \
                  my_id, my_prepare_timestamp, time_to_next_prepare_msg, dict_of_acceptors
                if max_accept_timestamp < 0:
                    # If max accept timestamp is negative, then none of the acceptors
                    # in the dict have accepted a message.
                    # So, proposer selects a proposal.
                    # The proposal is identified by the tuple (time, id).
                    output_msg = ('accept', my_prepare_timestamp, my_id)
                else:
                    # At least one acceptor has already accepted a proposal.
                    # So, proposer must select the acceptor's proposal.
                    output_msg = ('accept', max_accept_timestamp, max_accept_id)
                return output_msg, next_state
        return _no_value, state
    else:
        assert msg_name == 'accepted'
        # No action required.
        return _no_value, state

def acceptor_behavior(input_msg, state):
    my_id, my_prepare_timestamp, prepare_proposer, \
      accept_timestamp, accept_proposer = state
    
    msg_name, msg_timestamp, msg_proposer = input_msg
    # If the timestamp is greater than the formerly accepted timestamp or 
    # if it's equal, then if the current proposer has a higher number than 
    # the formerly accepted proposal, we prepare or accept the message
    if (msg_timestamp > my_prepare_timestamp or
        (msg_timestamp == my_prepare_timestamp) and (msg_proposer >= prepare_proposer)
        ):
        # If the message is prepare, then the acceptor grants it permission 
        # and sends it back to the proposers
        if msg_name == 'prepare':
            my_prepare_timestamp, prepare_proposer = msg_timestamp, msg_proposer
            output_msg = (
                'granted', my_id,
                my_prepare_timestamp, prepare_proposer,
                accept_timestamp, accept_proposer
                )
            state = my_id, my_prepare_timestamp, prepare_proposer, \
              accept_timestamp, accept_proposer 
            return output_msg, state
        # If the message is accept, then the acceptor accepts the message
        # and sets the value and proposer to be the received timestamp
        # and proposer number
        else:
            assert msg_name == 'accept'
            # If the message has been accepted, then update the timestamp
            # to the accepted value
            accept_timestamp, accept_proposer = msg_timestamp, msg_proposer
            state = my_id, my_prepare_timestamp, prepare_proposer, \
              accept_timestamp, accept_proposer
            output_msg = ('accepted', my_id, accept_timestamp, accept_proposer)
            return output_msg, state
    return _no_value, state

def time_step_behavior(input_msg, state):
    msg_name = input_msg[0]
    dict_of_accepted_values, previously_learned_value = state
    # If the message is accepted, we check for majority accepted values
    if msg_name == 'accepted':
        acceptor_id, accept_timestamp, accept_proposer = input_msg[1:]
        dict_of_accepted_values[acceptor_id] = (accept_timestamp, accept_proposer)
        # If the number of accepted values is greater than the majority, we
        # check to see if any one value has been accepted by the majority
        # of acceptors
        if len(dict_of_accepted_values) >= majority:
            list_of_accepted_values = dict_of_accepted_values.values()
            for v in list_of_accepted_values:
                # If the acceptors have reached a majority agreement on the
                # accepted value, set the learned value to the majority 
                # accepted value
                if len([w == v for w in list_of_accepted_values]) >= majority:
                    learned_value = v
                    # Print the newly learned value
                    if previously_learned_value != learned_value:
                        print 'learned_value', learned_value
                        previously_learned_value = learned_value
                        state = dict_of_accepted_values, previously_learned_value
        return _no_value, state
    # If the message is time_step, then we add one to my_prepare_timestep 
    elif msg_name == 'time_step':
        if input_msg[1] < 100 and not previously_learned_value:
            return ('time_step', input_msg[1]+1), state
        else:
            return _no_value, state
    # If the message is granted, then we simply return
    else:
        assert msg_name == 'granted'
        return _no_value, state
        
def run_Paxos():
    proposers = [blend(func=proposer_behavior,
                       in_streams=daemons_proposers_out_streams,
                       out_stream=proposer_out_streams[id],
                       state=(id, 0, random_number(), {}),
                       name='proposer_'+str(id)
                       )
                       for id in range(num_proposers)
                ]
    acceptors = [map_element (func=acceptor_behavior,
                       in_stream=daemons_acceptors_out_streams[id],
                       out_stream=acceptor_out_streams[id],
                       state=(id, -1, -1, -1, -1),
                       name='acceptor_'+str(id)
                       )
                       for id in range(num_acceptors)
                ]
        
    time_step_agent = blend(func=time_step_behavior,
                            in_streams=in_streams_for_time_step,
                            out_stream=time_step_stream,
                            state=({}, None),
                            name='time step agent'
                            )
    
    daemons_acceptors = [blend(
        func=delete,
        in_streams = proposer_out_streams,
        out_stream = daemons_acceptors_out_streams[id],
        name = 'daemons_acceptors_'+str(id)
        )
        for id in range(num_acceptors)
        ]
        
    daemons_proposers = [blend(
        func=delete,
        in_streams = acceptor_out_streams,
        out_stream = daemons_proposers_out_streams[id],
        name = 'daemons_proposers_'+str(id)
        )
        for id in range(num_proposers)
        ]
        
    
    #STEP 4. START COMPUTATION
    # Get the scheduler and execute a step.
    scheduler = Stream.scheduler
    # Start the computation by putting a value into the
    # time step stream
    time_step_stream.append(('time_step', 1))    # Start the scheduler.
    scheduler.step()

if __name__ == '__main__':
    run_Paxos()
    
                
            
