

def delay_start_of_file(filename, short_filename, start_ptr):
    start_ptr = int(start_ptr)
    with open(filename) as filehandle:
        floats = map(float, filehandle)
    short_version = floats[start_ptr:]
    with open(short_filename, 'w') as short_filehandle:
        for v in short_version:
            short_filehandle.write(str(v) + '\n')

def shorten_file(filename, short_filename, start_ptr, end_ptr):
    with open(filename) as filehandle:
        floats = map(float, filehandle)
    short_version = floats[start_ptr:end_ptr]
    with open(short_filename, 'w') as short_filehandle:
        for v in short_version:
            short_filehandle.write(str(v) + '\n')

def cutoff_tail_of_file(filename, short_filename, end_ptr):
    end_ptr = int(end_ptr)
    with open(filename) as filehandle:
        floats = map(float, filehandle)
    short_version = floats[:end_ptr]
    with open(short_filename, 'w') as short_filehandle:
        for v in short_version:
            short_filehandle.write(str(v) + '\n')

def decimate_file(filename, short_filename, window_size):
    print 'filename ', filename
    print 'short_filename', short_filename
    print 'window_size', window_size
    window_size = int(window_size)
    with open(filename) as filehandle:
        floats = map(float, filehandle)
    length = len(floats)
    start_ptr = 0
    end_ptr = window_size
    short_version = []
    while end_ptr < length:
        window = floats[start_ptr: end_ptr]
        short_version.append(sum(window)/float(window_size))
        start_ptr = end_ptr
        end_ptr = start_ptr + window_size
    with open(short_filename, 'w') as short_filehandle:
        for v in short_version:
            short_filehandle.write(str(v) + '\n')

def average_of_file(filename):
    with open(filename) as filehandle:
        floats = map(float, filehandle)
    print 'average of ', filename, ' : ', sum(floats)/float(len(floats))

def shorten_list_of_list_of_files(
        list_of_list_of_files, start_ptr, end_ptr): 
    shortened_list_of_list_of_files = []
    for list_of_files in list_of_list_of_files:
        shortened_list_of_files = []
        for filename in list_of_files:
            shortened_list_of_files.append(shorten_file(
                filename, 'Short_' + filename, start_ptr, end_ptr))
        shortened_list_of_list_of_files.append(shortened_list_of_files)
    return shortened_list_of_list_of_files

if __name__ == '__main__':
    import sys
    args = sys.argv
    ## shorten_file(
    ##     filename=args[1],
    ##     short_filename=args[2],
    ##     start_ptr=int(args[3]),
    ##     end_ptr=int(args[4])
    ##     )

    ## list_of_list_of_files = [
    ##     ['Sensor1.e.txt', 'Sensor1.n.txt', 'Sensor1.z.txt'],
    ##     ['Sensor2.e.txt', 'Sensor2.n.txt', 'Sensor2.z.txt'],
    ##     ['Sensor3.e.txt', 'Sensor3.n.txt', 'Sensor3.z.txt']
    ##     ]
    ## shorten_list_of_list_of_files(
    ##     list_of_list_of_files, 1140000, 1200000)
    ## args = sys.argv
    delay_start_of_file(filename=args[1],
                        short_filename=args[2],
                        start_ptr=args[3])
    ## cutoff_tail_of_file(filename=args[1],
    ##                     short_filename=args[2],
    ##                     end_ptr=args[3])
    ## decimate_file(filename=args[1],
    ##               short_filename=args[2],
    ##               window_size=args[3])
    ## average_of_file(filename=args[1])
    
