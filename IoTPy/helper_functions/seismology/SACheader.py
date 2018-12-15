# coding=utf-8
# Modified by RWC to match modified sac header that includes more station info
#  2013/11/25

"""
Descriptor of SAC header values.

Details from manual in manual.rst.

"""


import collections
import datetime

import SACbinary as binary


# Used by directory and reader to attempt automated assignment of components.
NORTH_COMPONENTS = {'HNN', 'HN1', 'HN2', 'HN3'}
EAST_COMPONENTS = {'HNE'}
Z_COMPONENTS = {'HNZ'}

# Size of header in bytes. Skip to this byte position to read the data without
# reading the header.
HEADER_SIZE = 632

# Simple list of all field names in the header.
FIELDS = []

# Maps field names to byte positions so that values can be read or written
# out of sequence, if desired.
POSITION_MAP = {}
# Used for reading and writing the header, so maintained in order.
FIELD_TYPES = collections.OrderedDict()
STRING_LENGTHS = {}
FRIENDLY_NAMES = {}
FIELD_DESCRIPTIONS = {}


def field(name, position, field_type, str_len, friendly_name, docstring):
    FIELDS.append(name)
    POSITION_MAP[name] = position
    FIELD_TYPES[name] = field_type
    if str_len:
        STRING_LENGTHS[name] = str_len
    if friendly_name:
        FRIENDLY_NAMES[name] = friendly_name
    FIELD_DESCRIPTIONS[name] = docstring if docstring else 'No docstring.'


field('delta',     0,   float, None, 'delta',
      'Increment between evenly spaced samples.')
field('depmin',    4,   float, None, 'value_min',
      'MINimum value of DEPendent variable.')
field('depmax',    8,   float, None, 'value_max',
      'MAXimum value of DEPendent variable.')
field('scale',     12,  float, None, 'value_scale',
      'Mult SCALE factor for dependent variable.')
field('odelta',    16,  float, None, None,
      'Observed increment if different than DELTA.')
field('b',         20,  float, None, 'value_initial',
      'Beginning value of the independent variable.')
field('e',         24,  float, None, 'value_final',
      'Ending value of the independent variable.')
field('o',         28,  float, None, 'event_origin_time',
      'Event origin time.')
field('a',         32,  float, None, 'event_arrival_time',
      'First arrival time.')
field('internal1', 36,  float, None, None, None)
# Tn: user-defined time-picks or markers n=1,2,...,9
# T(1)=T0, T(2)=T1, etc.')
field('t0',        40,  float, None, 'time_pick_0', None)
field('t1',        44,  float, None, 'time_pick_1', None)
field('t2',        48,  float, None, 'time_pick_2', None)
field('t3',        52,  float, None, 'time_pick_3', None)
field('t4',        56,  float, None, 'time_pick_4', None)
field('t5',        60,  float, None, 'time_pick_5', None)
field('t6',        64,  float, None, 'time_pick_6', None)
field('t7',        68,  float, None, 'time_pick_7', None)
field('t8',        72,  float, None, 'time_pick_8', None)
field('t9',        76,  float, None, 'time_pick_9', None)
field('f',         80,  float, None, None,
      'Fini of event time.')
# RESPn: instrument RESPonse parameters n=1,2,...,9
# RESP(1)=RESP0, RESP(2)=RESP1, etc.')
field('resp0',     84,  float, None, None, None)
field('resp1',     88,  float, None, None, None)
field('resp2',     92,  float, None, None, None)
field('resp3',     96,  float, None, None, None)
field('resp4',     100, float, None, None, None)
field('resp5',     104, float, None, None, None)
field('resp6',     108, float, None, None, None)
field('resp7',     112, float, None, None, None)
field('resp8',     116, float, None, None, None)
field('resp9',     120, float, None, None, None)
field('stla',      124, float, None, 'latitude',
      'STation LAttitude.')
field('stlo',      128, float, None, 'longitude',
      'STation LOngtitude.')
field('stel',      132, float, None, 'elevation',
      'STation ELevation.')
field('stdp',      136, float, None, 'depth',
      'STation DePth below surface.')
field('evla',      140, float, None, 'event_latitude',
      'EVent LAttitude.')
field('evlo',      144, float, None, 'event_longitude',
      'EVent LOngtitude.')
field('evel',      148, float, None, 'event_elevation',
      'EVent ELevation.')
field('evdp',      152, float, None, 'event_depth',
      'EVent DePth below surface.')
field('unused1',   156, float, None, None, None)
field('user0',     160, float, None, 'user_float_0', None)
field('user1',     164, float, None, 'user_float_1', None)
field('user2',     168, float, None, 'user_float_2', None)
field('user3',     172, float, None, 'user_float_3', None)
field('user4',     176, float, None, 'user_float_4', None)
field('user5',     180, float, None, 'user_float_5', None)
field('user6',     184, float, None, 'user_float_6', None)
field('user7',     188, float, None, 'user_float_7', None)
field('user8',     192, float, None, 'user_float_8', None)
field('user9',     196, float, None, 'user_float_9', None)
field('dist',      200, float, None, 'station_to_event_dist',
      'Station to event DISTance (km).')
field('az',        204, float, None, 'event_to_station_deg',
      'Event to station AZimuth (degrees).')
field('baz',       208, float, None, 'station_to_event_deg',
      'Station to event AZimuth (degrees).')
field('gcarc',     212, float, None, 'station_to_great_circle',
      'Station to event Great Circle ARC length (degrees).')
field('internal2', 216, float, None, None, None)
field('internal3', 220, float, None, None, None)
field('depmen',    224, float, None, 'value_mean',
      'MEaN value of DEPendent variable.')
field('cmpaz',     228, float, None, 'component_azimuth',
      'CoMPonent AZimuth (degrees clockwise from north).')
field('cmpinc',    232, float, None, 'component_incident',
      'CoMPonent INCident angle (degrees from vertical).')
field('unused2',   236, float, None, None, None)
field('unused3',   240, float, None, None, None)
field('unused4',   244, float, None, None, None)
field('unused5',   248, float, None, None, None)
field('unused6',   252, float, None, None, None)
field('unused7',   256, float, None, None, None)
field('unused8',   260, float, None, None, None)
field('unused9',   264, float, None, None, None)
field('unused10',  268, float, None, None, None)
field('unused11',  272, float, None, None, None)
field('unused12',  276, float, None, None, None)

# Composite field 'start_time' is constructed out of the following fields.
# Call function get_time_from_fields to build a datetime object.
field('nzyear',    280, int,   None, None,
      'GMT YEAR.')
field('nzjday',    284, int,   None, None,
      'GMT Julian DAY.')
field('nzhour',    288, int,   None, None,
      'GMT HOUR.')
field('nzmin',     292, int,   None, None,
      'GMT MINute.')
field('nzsec',     296, int,   None, None,
      'GMT SECond.')
field('nzmsec',    300, int,   None, None,
      'GMT MilliSECond.')
field('internal4', 304, int,   None, None, None)
field('internal5', 308, int,   None, None, None)
field('internal6', 312, int,   None, None, None)
field('npts',      316, int,   None, 'num_points',
      'Number of PoinTS per data component.')
field('internal7', 320, int,   None, None, None)
field('internal8', 324, int,   None, None, None)
field('unused13',  328, int,   None, None, None)
field('unused14',  332, int,   None, None, None)
field('unused15',  336, int,   None, None, None)
field('iftype',    340, int,   None, None,
      'File TYPE.')
field('idep',      344, int,   None, None,
      'Type of DEPendent variable.')
field('iztype',    348, int,   None, None,
      'Reference time equivalence.')
field('unused16',  352, int,   None, None, None)
field('iinst',     356, int,   None, 'instrument_type',
      'Type of recording INSTrument.')
field('istreg',    360, int,   None, 'station_region',
      'STation geographic REGion.')
field('ievreg',    364, int,   None, 'event_region',
      'EVent geographic REGion.')
field('ievtyp',    368, int,   None, 'event_type',
      'EVent TYPE.')
field('iqual',     372, int,   None, 'data_quality',
      'QUALity of data.')
field('isynth',    376, int,   None, 'synthetic_data',
      'SYNTHetic data flag.')
#
# SAF Modifications
#field('unused17',  380, int,   None, None, None)
#field('unused18',  384, int,   None, None, None)
field('SAFid',     380, int,   None, None, 'SAF ID')
field('floornum',  384, int,   None, None, 'Floor Number')
#
field('unused19',  388, int,   None, None, None)
field('unused20',  392, int,   None, None, None)
field('unused21',  396, int,   None, None, None)
field('unused22',  400, int,   None, None, None)
field('unused23',  404, int,   None, None, None)
field('unused24',  408, int,   None, None, None)
field('unused25',  412, int,   None, None, None)
field('unused26',  416, int,   None, None, None)
field('leven',     420, int,   None, 'evenly_spaced',
      'True, if data are EVENly spaced (required).')
field('lpspol',    424, int,   None, 'positive_polarity',
      'True, if station components have a PoSitive POLarity.')
field('lovrok',    428, int,   None, None,
      'True, if it is OK to OVeRwrite this file in disk.')
field('lcalda',    432, int,   None, None,
      'True, if DIST, AZ, BAZ and GCARC are to be calculated from station and '
      'event coordinates.')
field('unused27',  436, int,   None, None, None)
field('kstnm',     440, str,   8,    'station',
      'STation NaMe (e.g. BAK).')
field('kevnm',     448, str,   16,   'event',
      'EVent NaMe.')
#
# SAF Modifcation
#
#field('khole',     464, str,   8,    'hole_id',
#      'HOLE identification, if nuclear event.')
#field('ko',        472, str,   8,    'origin_time',
#      'Event Origin time identification.')
#field('ka',        480, str,   8,    'arrival_time',
#      'First Arrival time identification.')
#field('kt0',       488, str,   8,    None, None)
#field('kt1',       496, str,   8,    None, None)
#field('kt2',       504, str,   8,    None, None)
#field('kt3',       512, str,   8,    None, None)
#field('kt4',       520, str,   8,    None, None)
#field('kt5',       528, str,   8,    None, None)
#field('kt6',       536, str,   8,    None, None)
#field('kt7',       544, str,   8,    None, None)
#field('kt8',       552, str,   8,    None, None)
#field('kt9',       560, str,   8,    None, None)
#field('kf',        568, str,   8,    'fini_id',
#      'Fini identification.')
#field('kuser0',    576, str,   8,    'user_string_0',
#      'USER-defined variable storage area.')
#field('kuser1',    584, str,   8,    'user_string_1',
#      'USER-defined variable storage area.')
#field('kuser2',    592, str,   8,    'user_string_2',
#      'USER-defined variable storage area.')
field('SAFname',    464, str,   32,    'SAFname', 'SAF description')
field('SensorModel', 496, str,   32,   'SensorModel', 'Sensor description')
field('Building',   528, str,   24,   'Building', 'Building Name')
field('SensorSerial', 552, str,   16,   'SensorSerial', 'Sensor Serial Number')
field('CACRname',   568, str,   16,   'CACRname', 'CACR assigned name')
field('Misc',       584, str,   16,   'Misc', 'Miscellaneous')
#
field('kcmpnm',    600, str,   8,    'component',
      'CoMPonent NaMe.')
field('knetwk',    608, str,   8,    'network',
      'Name of seismic NETWorK (e.g. CI).')
field('kdatrd',    616, str,   8,    'recording_date',
      'DATa Recording Date onto the computer.')
field('kinst',     624, str,   8,    'instrument_name',
      'Generic name of recording INSTrument.')


def read_header(file_obj):
    fields = {}
    for field, field_type in FIELD_TYPES.viewitems():
        fields[field] = read_value(file_obj, field, field_type=None)
    return fields


def read_value(file_obj, field, field_type=None):
    # field_type is derivable from field, but in the most common case with
    # read_header, we're iterating over FIELD_TYPES and already have that
    # information.
    # Making field_type an optional parameter also makes it possible to
    # override the type of a field, such as in the user defined header fields.
    field_type = field_type if field_type else FIELD_TYPES[field]
    if field_type == float:
        return binary.read_float(file_obj)
    elif field_type == int:
        return binary.read_long(file_obj)
    elif field_type == str:
        str_len = STRING_LENGTHS[field]
        return binary.read_string(file_obj, str_len)


def write_header(file_obj, fields):
    for field, field_type in FIELD_TYPES.viewitems():
        write_value(file_obj, field, fields.get(field), field_type=field_type)


def write_value(file_obj, field, value, field_type=None):
    # field_type is derivable from field, but in the most common case with
    # write_header, we're iterating over FIELD_TYPES and already have that
    # information.
    # Making field_type an optional parameter also makes it possible to
    # override the type of a field, such as in the user defined header fields.
    field_type = field_type if field_type else FIELD_TYPES[field]
    if field_type == float:
        binary.write_float(file_obj, value)
    elif field_type == int:
        binary.write_long(file_obj, value)
    elif field_type == str:
        str_len = STRING_LENGTHS[field]
        binary.write_string(file_obj, value, str_len)


def get_time_from_fields(fields):
    first_day = datetime.datetime(
        fields['nzyear'], 1, 1, fields['nzhour'],
        fields['nzmin'], fields['nzsec'], fields['nzmsec'] * 1000)
    return first_day + datetime.timedelta(days=(fields['nzjday'] - 1))


def get_fields_from_time(date_obj):
    fields = {}
    fields['nzyear'] = date_obj.year
    fields['nzjday'] = date_obj.timetuple().tm_yday
    fields['nzhour'] = date_obj.hour
    fields['nzmin'] = date_obj.minute
    fields['nzsec'] = date_obj.second
    fields['nzmsec'] = date_obj.microsecond / 1000
    return fields
