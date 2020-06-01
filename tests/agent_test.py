
import unittest
from IoTPy.core.stream import run, Stream, StreamArray
from IoTPy.core.agent import Agent, BasicAgent
#------------------------------------------------------------------------------------------
# Simple Agent Test
#------------------------------------------------------------------------------------------


class test_agent(unittest.TestCase):

    def test_(self):

        def copy(list_of_in_lists, state):
            return ([in_list.list[in_list.start:in_list.stop] for in_list in list_of_in_lists],
                    state, [in_list.stop for in_list in list_of_in_lists])

        input_stream_0 = Stream('input_stream_0', num_in_memory=32)
        input_stream_1 = Stream('input_stream_1', num_in_memory=32 )
        output_stream_0 = Stream('output_stream_0', num_in_memory=32)
        output_stream_1 = Stream('output_stream_1', num_in_memory=32)
        A = Agent(in_streams=[input_stream_0, input_stream_1 ],
                  out_streams=[output_stream_0, output_stream_1],
                  transition=copy,
                  name='A')
        
        input_stream_0.extend(list(range(10)))
        run()
        assert(output_stream_0.stop == 10)
        assert(output_stream_1.stop == 0)
        assert(output_stream_0.recent[:10] == list(range(10)))
        assert(input_stream_0.start == {A:10})
        assert(input_stream_1.start == {A:0})

        input_stream_1.extend(list(range(10, 25, 1)))
        run()
        assert(output_stream_0.stop == 10)
        assert(output_stream_1.stop == 15)
        assert(output_stream_0.recent[:10] == list(range(10)))
        assert(output_stream_1.recent[:15] == list(range(10, 25, 1)))
        assert(input_stream_0.start == {A:10})
        assert(input_stream_1.start == {A:15})

if __name__ == '__main__':
    unittest.main()
    
