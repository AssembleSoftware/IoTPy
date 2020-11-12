"""
This file contains a simple example of a stream integrated with a
database. The database is sqlite3.

The example queries a table called sensors_table. The table and
database are created by calling make_sensor_db.py which is also found
in IoTPy/examples/op.

A typical entry in the sensors table is:
'Caltech', '34.1377', 'N', '118.1253', 'W'
which is a name (Caltech), latitiude (34.1377), NorS (N),
longitude (118.1253), EorW (W).

This example shows how information from a database is added to
elements of a stream. The elements of the incoming stream are pairs:
(sensor_name, sensor_reading). An example of such an element is:
('Caltech', 3.0).
The elements of the output stream also have the latitude and longitude
associated with the sensor name. An example of such an element is:
('Caltech', 3.0, 34.1377, 118.1253).
The latitude (34.1377) and longitude (118.1253) are added to the
element of the incoming stream.

[The data is assumed to come from the western half of the northern
hemisphere, so the application doesn't use N, S, E, W for North,
South, East, West.] 


"""

# Import SQL database
import sqlite3
from sqlite3 import Error

import os
import sys
sys.path.append("../")

from IoTPy.core.stream import Stream, run
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.recent_values import recent_values
from examples.op.make_sensor_DB import create_connection

 
def get_sensor_lat_long_from_name(conn, name):
    """
    Query the database to get the latitude and longitude of a sensor
    given its name. 

    Query tasks by name
    :param conn: the Connection object
    :param name: str
    :return:
    """
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT latitude, longitude FROM sensors_table WHERE name=?", (name,))
        rows = cur.fetchall()
    return rows[0]


def simple_example_of_map_element(database):
    # create a database connection
    conn = create_connection(database)

    # Specify streams
    x = Stream('x')
    y = Stream('y')
    
    # Specify encapsulated function used to generate y from x.
    def f(sensor_name_and_reading):
        """
        Input element: sensor_name, sensor_reading
        Output element: sensor_name, sensor_reading, latitude,
                        longitude.

        """
        # An element of the input stream.
        sensor_name, sensor_reading = sensor_name_and_reading
        # Get the latitude and longitude from the database.
        with conn:
            lat, long = get_sensor_lat_long_from_name(
                conn=conn,name=sensor_name)
        # return an element of the output stream.
        return (sensor_name, sensor_reading, lat, long)
    
    # Create agent with input stream x and output stream y.
    map_element(func=f, in_stream=x, out_stream=y)

    # Put test values in the input streams.
    x.extend([['MIT', 1.0], ['MIT', 2.0], ['Caltech', 3.0],
    ['Berkeley', 4.0],  ['Caltech', 3.0] ])
    # Execute a step
    run()
    # Look at recent values of streams.
    print ('recent values of stream y are')
    print (recent_values(y))

if __name__ == '__main__':
    simple_example_of_map_element(database=r"sensors_table.db")
