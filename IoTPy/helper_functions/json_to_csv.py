import json


def json_to_csv(json_filename, csv_filename):
    with open(json_filename, 'r') as input_json_file:
        #data = json.load(input_json_file)
        data=[]

    with open(csv_filename, 'w') as output_csv_file:
        for v in data:
            output_csv_file.write(str(v) + '\n')
            
