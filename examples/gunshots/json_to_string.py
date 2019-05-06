import json

def json_to_strings(json_filename, strings_filename, number_output_lines=None):
    with open(json_filename, 'r') as input_json_file:
        data = json.load(input_json_file)
        if number_output_lines:
            data = data[:number_output_lines]
    with open(strings_filename, 'w') as output_strings_file:
        for v in data:
            output_strings_file.write(str(v) + '\n')

if __name__ == '__main__':
    json_filenames = [
        'Sensor1.e.json', 'Sensor1.n.json', 'Sensor1.z.json',
        'Sensor2.e.json', 'Sensor2.n.json', 'Sensor2.z.json',
        'Sensor3.e.json', 'Sensor3.n.json', 'Sensor3.z.json'
        ]
    for json_filename in json_filenames:
        strings_filename = json_filename.replace('.json', '.short.txt')
        json_to_strings(json_filename, strings_filename,
                        number_output_lines=1000)
            
