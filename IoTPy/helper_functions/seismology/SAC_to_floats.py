"""
.sac files are widely used in seismology whereas .json files are more
widely used generally. This collection of files converts .sac files to
.json files. It was written by Julian Bunn of the California Institute
of Technology.

"""

import json
import sys
import SACreader

def SAC_to_floats(SAC_filename, floats_filename):
    data_points = SACreader.open_file(SAC_filename).data_points
    with open(floats_filename, 'w') as the_file:
        for data_point in data_points:
            the_file.write(str(data_point))
            the_file.write('\n')
    return

if __name__ == '__main__':
    args = sys.argv
    SAC_to_floats(
        SAC_filename=args[1],
        floats_filename=args[2]
        )
    ## SAC_to_floats(
    ##     SAC_filename='SAC_test_file.sac',
    ##     floats_filename='floats_test_file.json')
         
