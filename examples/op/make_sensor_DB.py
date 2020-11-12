"""
This file creates a database file containing the database table used
to add value to elements of a stream. 
"""
# Import the database
import sqlite3
from sqlite3 import Error

# CREATE CONNECTION TO THE DATABASE
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


# CREATE A TABLE OF THE DATABASE USING A SQL COMMAND
def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


# ADD A ROW --- A SENSOR'S DATA --- TO THE SENSORS_TABLE
def create_sensor(conn, sensors_table):
    """
    Create a new sensor into the sensors table
    :param conn:
    :param sensors_table:
    :return: id
    """
    sql = ''' INSERT INTO sensors_table(name, latitude, NorS, longitude, EorW) VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, sensors_table)
    conn.commit()
    return cur.lastrowid



def main():
    database = r"sensors_table.db"

    sql_create_sensors_table = """ CREATE TABLE IF NOT EXISTS sensors_table (
                                        id integer PRIMARY KEY,
                                        name text,
                                        latitude float,
                                        NorS text,
                                        longitude float,
                                        EorW text
                                    ); """
    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create sensors table
        create_table(conn, sql_create_sensors_table)
    else:
        print("Error! cannot create the database connection.")

    # Created sensors_table

    # Enter rows of the sensor table. Each row describes a sensor.
    with conn:
        # create a new sensor
        Caltech_sensor_data = ('Caltech', '34.1377', 'N', '118.1253', 'W');
        sensor_id = create_sensor(conn, Caltech_sensor_data)
        
        # create a new sensor
        MIT_sensor_data = ('MIT', '42.3601', 'N', '71.0942', 'W');
        sensor_id = create_sensor(conn, MIT_sensor_data)

        # create a new sensor
        Berkeley_sensor_data = ('Berkeley', '37.8719', 'N', '122.2585', 'W');
        sensor_id = create_sensor(conn, Berkeley_sensor_data)

        ## lat_long = get_sensor_lat_long_from_name(conn, 'MIT')
        ## print (lat_long)
    print ('created sensor table')

if __name__ == '__main__':
    main()
