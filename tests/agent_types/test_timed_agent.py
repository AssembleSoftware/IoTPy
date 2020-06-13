
import unittest
# agent, stream are in ../core

from IoTPy.core.agent import Agent, InList
from IoTPy.core.stream import Stream, StreamArray, run
# helper_control, recent_values are in ../helper_functions
from IoTPy.core.helper_control import _no_value, _multivalue
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.agent_types.timed_agent import timed_zip, timed_window_function
from IoTPy.agent_types.timed_agent import timed_window

class test_timed_zip_agents(unittest.TestCase):

  def test_timed_zip_agents(self):
      x = Stream('x')
      y = Stream('y')
      z = Stream('z')

      # timed_zip_agent(in_streams=[x,y], out_stream=z, name='a')
      z = timed_zip([x, y])

      def concat_operator(timed_list):
          result = ''
          for timestamp_value in timed_list:
              result = result + timestamp_value[1]
          return result

      r = timed_window_function(concat_operator, x, 5, 5)
      s = timed_window_function(concat_operator, x, 20, 10)

      x.extend([[1, 'a'], [3, 'b'], [10, 'd'], [15, 'e'], [17, 'f']])
      y.extend([[2, 'A'], [3, 'B'], [9, 'D'], [20, 'E']])
      run()
      assert z.recent[:z.stop] == \
        [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
         [10, ['d', None]], [15, ['e', None]], [17, ['f', None]]]
      assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd')]
      assert s.recent[:s.stop] == []
      
      x.extend([[21, 'g'], [23, 'h'], [40, 'i'], [55, 'j'], [97, 'k']])
      y.extend([[21, 'F'], [23, 'G'], [29, 'H'], [55, 'I']])
      run()
      assert z.recent[:z.stop] == \
        [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
         [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
         [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
         [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']]]
      assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                   (25, 'gh'), (45, 'i'), (60, 'j')]
      assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                   (50, 'i'), (60, 'ij'), (70, 'j')]

      x.extend([[100, 'l'], [105, 'm']])
      y.extend([[100, 'J'], [104, 'K'], [105, 'L'], [107, 'M']])
      run()
      assert z.recent[:z.stop] == \
        [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
         [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
         [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
         [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']],
         [97, ['k', None]], [100, ['l', 'J']], [104, [None, 'K']], [105, ['m', 'L']]]
      assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                   (25, 'gh'), (45, 'i'), (60, 'j'),
                                   (100, 'k'), (105, 'l')]
      assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                   (50, 'i'), (60, 'ij'), (70, 'j'), (100, 'k')
                                   ]

      x.extend([[106, 'n'], [110, 'o']])
      run()
      assert z.recent[:z.stop] == \
        [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
         [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
         [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
         [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']],
         [97, ['k', None]], [100, ['l', 'J']], [104, [None, 'K']], [105, ['m', 'L']],
         [106, ['n', None]], [107, [None, 'M']]
       ]
      assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                   (25, 'gh'), (45, 'i'), (60, 'j'),
                                   (100, 'k'), (105, 'l'), (110, 'mn')]
      assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                   (50, 'i'), (60, 'ij'), (70, 'j'), (100, 'k'),
                                   (110, 'klmn')]
      return

  def test_timed_window(self):
      x = Stream('x')
      y = Stream('y')

      def f(v): return v

      timed_window(
          func=f, in_stream=x, out_stream=y,
          window_duration=10, step_time=10)

      x.extend([(1, 'a'), (8, 'b'), (12, 'c'), (14, 'd'), (32, 'e'), (50, 'f')])
      run()
      assert (recent_values(y) == [
          (10, [(1, 'a'), (8, 'b')]), (20, [(12, 'c'),
          (14, 'd')]), (40, [(32, 'e')])])


if __name__ == '__main__':
  unittest.main()