"""
.sac files are widely used in seismology whereas .json files are more
widely used generally. This collection of files converts .sac files to
.json files. It was written by Julian Bunn of the California Institute
of Technology.

"""
import sys
import json
import SACreader

def SAC_to_JSON(SAC_filename, JSON_filename):
    data_points = SACreader.open_file(SAC_filename).data_points
    with open(JSON_filename, 'w') as the_file:
        json.dump(data_points, the_file)
    return

if __name__ == '__main__':
    args = sys.argv
    SAC_to_JSON(
        SAC_filename=args[1],
        JSON_filename=args[2]
        )
    
    ## SAC_to_JSON(
    ##     SAC_filename='SAC_test_file.sac',
    ##     JSON_filename='JSON_test_file.json')
         
