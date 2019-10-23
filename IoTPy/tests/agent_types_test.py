from element_test import test_element
from list_test import test_list
from window_test import test_window_agents
from merge_test import test_merge_agents
from split_test import test_split_agents
from multi_test import test_multi
from sink_test import test_sink
from source_test import test_source
from shared_variables_test import test_shared_variables
def test():
    test_element()
    test_list()
    test_window_agents()
    test_merge_agents()
    test_split_agents()
    test_multi()
    test_shared_variables()
    test_sink()
    print ('STARTING TEST OF SOURCE. Takes few seconds.')
    print ('This test will output: "Stopped: No more input" a few times.')
    test_source()


if __name__ == '__main__':
    test()
