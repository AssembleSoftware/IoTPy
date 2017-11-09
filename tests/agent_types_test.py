from element_test import test_element
from list_test import test_list
from window_test import test_window_agents
from merge_test import test_merge_agents
from split_test import test_split_agents
from multi_test import test_multi
from sink_test import test_sink
from source_test import test_source
def test():
    test_element()
    test_list()
    test_window_agents()
    test_merge_agents()
    test_split_agents()
    test_multi()
    test_sink()
    print 'starting test of source. Takes few seconds'
    test_source()


if __name__ == '__main__':
    test()
