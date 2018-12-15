# coding=utf-8

"""
Util module for reading/writing SAC binary data.

"""

import struct


#: These values are the default to use in a field when no value is specified.
FLOAT_DEFAULT = -12345.0
LONG_DEFAULT = -12345
STRING_DEFAULT = u'-12345          '

FLOAT_DEFAULT_BYTES = struct.pack('<f', FLOAT_DEFAULT)
LONG_DEFAULT_BYTES = struct.pack('<l', LONG_DEFAULT)


def is_default_value(value):
    if type(value) == str:
        return value == STRING_DEFAULT
    elif type(value) == int:
        return value == LONG_DEFAULT
    elif type(value) == float:
        return value == FLOAT_DEFAULT
    else:
        raise ValueError('Unexpected value of type {} provided.'.format(
            type(value)))


def get_float(byte_value):
    return struct.unpack('<f', byte_value)[0]


def read_float(stream):
    value = get_float(stream.read(4))
    return value if value != FLOAT_DEFAULT else None


def read_long(stream):
    value = struct.unpack('<l', stream.read(4))[0]
    return value if value != LONG_DEFAULT else None


def read_string(stream, length):
    value = struct.unpack('<{}s'.format(length),
                          stream.read(length))
    value = value[0].decode('ascii')
    if value == STRING_DEFAULT[:length]:
        return None
    # Odd that this is necessary. I thought all strings were null filled . . .
    strip_index = None
    for index, char in enumerate(value):
        try:
            if char == STRING_DEFAULT[index]:
                if not strip_index:
                    strip_index = index
                else:
                    strip_index = None
        except:
            continue
    if strip_index:
        value = value[:strip_index]
    return value.replace('\x00', '').strip()


def write_float(stream, float_value):
    if float_value is not None:
        byte_value = struct.pack('<f', float_value)
    else:
        byte_value = FLOAT_DEFAULT_BYTES
    stream.write(byte_value)


def write_long(stream, long_value):
    if long_value is not None:
        byte_value = struct.pack('<l', long_value)
    else:
        byte_value = LONG_DEFAULT_BYTES
    stream.write(byte_value)


def write_string(stream, str_value, str_len):
    if str_value is not None:
        str_value = str_value + STRING_DEFAULT[len(str_value):]
        byte_value = struct.pack('<{}s'.format(str_len),
                                 str_value.encode('ascii'))
    else:
        byte_value = struct.pack('<{}s'.format(str_len),
                                 STRING_DEFAULT[:str_len].encode('ascii'))
    stream.write(byte_value)
