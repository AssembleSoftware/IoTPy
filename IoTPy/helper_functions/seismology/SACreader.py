#!/usr/bin/env python
# coding=utf-8

"""
Container classes for reading SAC file data.

SACGroupReader is used to read three SACFileReader objects at once. SAC data
that originates from 3-axis accelerometers benefits from this container.

"""

import argparse
import collections
import contextlib
import datetime

import SACbinary as binary
import SACheader as header


class SACFile(object):

    def __init__(self, fields=None):
        """
        Instantiate a SACFile container.

        """
        self.fields = fields if fields else {}
        self._start_time = None

    @property
    def start_time(self):
        if not self._start_time:
            self._start_time = header.get_time_from_fields(self.fields)
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        self.fields.update(header.get_fields_from_time(value))

    @property
    def end_time(self):
        return self.start_time + datetime.timedelta(
            microseconds=self.get('delta') * (self.get('npts') - 1) * 1000000)

    def get(self, field):
        return self.fields.get(field)

    def set(self, field, value):
        field_type = header.FIELD_TYPES[field]
        if value is not None and type(value) != field_type:
            raise ValueError(
                'Cannot set {} as a value of type {}. Type must be {}.'.format(
                    field, type(value), field_type))
        self.fields[field] = value

    def header_to_dict(self, empty_fields=False):
        result = collections.OrderedDict()
        for field in header.FIELDS:
            value = self.fields[field]
            if value is not None or empty_fields:
                result[field] = value
        return result

    def __str__(self, describe=False, empty_fields=False):
        result = [
            'Recording start time: {}'.format(self.start_time),
            'Recording end time: {}'.format(self.end_time)]
        dict_obj = self.header_to_dict(empty_fields=empty_fields)
        for field, value in dict_obj.viewitems():
            string_value = str(value) if value is not None else 'unspecified'
            if describe:
                result.append('# {}'.format(header.FIELD_DESCRIPTIONS[field]))
            result.append('{}: {}'.format(field, string_value))
        return '\n'.join(result)


class SACReader(SACFile):

    def __init__(self, file_obj, streaming=True, skip=0, number=0):
        # the skip and number arguments are introduced for when only a portion of the data are required
        super(SACReader, self).__init__(fields=header.read_header(file_obj))
        self._streaming = streaming
        self._file_obj = file_obj
        if streaming:
            self.data_points = self._guarded_data_point_stream()
        else:
            if skip == 0:
                self.data_points = [pt for pt in self._data_point_stream()]
            else:
                self.data_points = [pt for pt in self._data_point_stream_skip(skip, number)]


    def _guarded_data_point_stream(self):
        if not self._streaming or not self._file_obj:
            raise ValueError(
                'Cannot iterate over the data points in streaming mode '
                'without providing a file to read from.')
        return self._data_point_stream()

    def _data_point_stream(self):
        self._file_obj.seek(header.HEADER_SIZE)
        byte_value = self._file_obj.read(4)
        while byte_value:
            yield binary.get_float(byte_value)
            byte_value = self._file_obj.read(4)
            
    def _data_point_stream_skip(self, skip, number):
        # JJB added this function
        # could modify the following to seek to header size plus skip, but not tried
        self._file_obj.seek(header.HEADER_SIZE + skip*4)
        #for _ in range(skip):
        #    byte_value = self._file_obj.read(4)
        byte_value = self._file_obj.read(4)
        count = 0
        while byte_value:
            count += 1
            if number > 0 and count > number:
                break
            yield binary.get_float(byte_value)
            byte_value = self._file_obj.read(4)


class SACGroup(object):

    FIELDS_REQUIRING_EQUAL_VALUES = [
        'knetwk', 'kstnm', 'stla', 'stlo', 'stdp', 'npts', 'delta',
        'nzyear', 'nzjday', 'nzhour', 'nzmin', 'nzsec', 'nzmsec',
    ]

    def __init__(self, n_fields=None, e_fields=None, z_fields=None):
        self.n = SACFile(fields=n_fields)
        self.e = SACFile(fields=e_fields)
        self.z = SACFile(fields=z_fields)
        self.components = [self.n, self.e, self.z]

    def validate(self):
        # Only working with evenly spaced time series data for now.
        if self.check('leven') != 1 or self.check('iftype') != 1:
            raise ValueError('This program only understands evenly spaced '
                             'data values.')
        if not self.check('odelta', need_value=False) is None:
            raise ValueError('Not able to handle "odelta"')

        component_names = set([c.fields['kcmpnm'] for c in self.components])
        if not len(component_names) == 3:
            raise ValueError(
                'All files should have different component names.')

        for field in self.FIELDS_REQUIRING_EQUAL_VALUES:
            self.check(field)

    @property
    def start_time(self):
        # These fields have already been checked to be equal on read, if files
        # were provided, or set to be equal on write so we can read any
        # component.
        return self.n.start_time

    @start_time.setter
    def start_time(self, value):
        field_updates = header.get_fields_from_time(value)
        for component in self.n, self.e, self.z:
            component.fields.update(field_updates)

    @property
    def end_time(self):
        return self.n.end_time

    def check(self, field, need_value=True):
        """
        Validate that all files in a group have the same value and return it.

        """
        value = self.n.get(field)
        if value is None and need_value:
            raise ValueError('Expected a value for field "{}".'.format(field))
        if value != self.e.get(field) or value != self.z.get(field):
            raise ValueError('Expected all files in a group to have the same '
                             'value for field "{}".'.format(field))
        return value

    def get(self, field):
        """
        Return a value from each component file.

        If they should be equal, use check to return only one value.

        """
        return [component.get(field) for component in self.components]

    def check_or_get(self, field):
        try:
            return self.check(field, need_value=False)
        except ValueError:
            return self.get(field)

    def set(self, field, value):
        # Perform validation and set north value.
        self.n.set(field, value)
        # Directly set remaining values (bypasses additional validation).
        self.e.fields[field] = value
        self.z.fields[field] = value

    def header_to_dict(self, empty_fields=False):
        result = collections.OrderedDict()
        for field in header.FIELDS:
            value = self.check_or_get(field)
            if value is not None or empty_fields:
                result[field] = value
        return result

    def __str__(self, describe=False, empty_fields=False):
        result = ['Recording start time: {}'.format(self.start_time),
                  'Recording end time: {}'.format(self.end_time)]
        dict_obj = self.header_to_dict(empty_fields=empty_fields)
        for field, value in dict_obj.viewitems():
            string_value = str(value) if value is not None else 'unspecified'
            if describe:
                result.append('# {}'.format(header.FIELD_DESCRIPTIONS[field]))
            result.append('{}: {}'.format(field, string_value))
        return '\n'.join(result)


class SACGroupReader(SACGroup):

    def __init__(self, file_obj1, file_obj2, file_obj3, streaming=True):
        components = [
            SACReader(file_obj1, streaming=streaming),
            SACReader(file_obj2, streaming=streaming),
            SACReader(file_obj3, streaming=streaming),
        ]
        # Attempt automated assignment.
        self.n, self.e, self.z = None, None, None
        for component in components:
            component_name = component.get('kcmpnm')
            if component_name in header.NORTH_COMPONENTS:
                self.n = component
            elif component_name in header.EAST_COMPONENTS:
                self.e = component
            elif component_name in header.Z_COMPONENTS:
                self.z = component
        if self.n and self.e and self.z:
            self.components = [self.n, self.e, self.z]
        # Automatic assignment failed; assume ordering of n, e, z.
        else:
            self.n, self.e, self.z = components
            self.components = components
        self.validate()

    @property
    def data_points(self):
        """
        Yields time along with one data point from each component.

        """
        current_time = self.start_time
        delta_value = datetime.timedelta(seconds=self.n.fields['delta'])
        for n, e, z in zip(*[c.data_points for c in self.components]):
            yield current_time, n, e, z
            current_time += delta_value


def open_file(filename, skip=0, number=0):
    """Thin wrapper around SACReader to open and close a SAC file."""
    with open(filename, 'rb') as in_file:
        return SACReader(in_file, streaming=False, skip=skip, number=number)


@contextlib.contextmanager
def open_file_streaming(filename):
    """Thin wrapper around SACReader to open and close a SAC file."""
    with open(filename, 'rb') as in_file:
        yield SACReader(in_file, streaming=True)


def open_group(n_filename, e_filename, z_filename):
    """Thin wrapper around SACGroupReader to open and close three SAC files."""
    with open(n_filename, 'rb') as n_file:
        with open(e_filename, 'rb') as e_file:
            with open(z_filename, 'rb') as z_file:
                return SACGroupReader(n_file, e_file, z_file, streaming=False)


@contextlib.contextmanager
def open_group_streaming(n_filename, e_filename, z_filename):
    """Thin wrapper around SACGroupReader to open and close three SAC files."""
    with open(n_filename, 'rb') as n_file:
        with open(e_filename, 'rb') as e_file:
            with open(z_filename, 'rb') as z_file:
                yield SACGroupReader(n_file, e_file, z_file, streaming=True)


def main():
    args = parse_args()
    if len(args.filenames) == 1:
        fn = open_file_streaming
    else:
        fn = open_group_streaming
    with fn(*args.filenames) as sac_data:
        if args.json:
            import json
            print json.dumps(
                sac_data.header_to_dict(empty_fields=args.empty),
                indent=2, separators=(',', ': '))
        elif not args.no_header:
            print sac_data.__str__(describe=args.describe,
                                   empty_fields=args.empty)
        if args.data:
            for value in sac_data.data_points:
                if len(args.filenames) > 1:
                    print ' '.join([str(component) for component in value])
                else:
                    print value


def parse_args():
    parser = argparse.ArgumentParser(
        description='Output the header of a SAC file.')
    parser.add_argument(
        '--no_header', action='store_true',
        help='Skip printing the header. Implies --data.')
    parser.add_argument(
        '--empty', action='store_true',
        help='Output empty fields as well.')
    parser.add_argument(
        '--data', action='store_true',
        help='Also print the data points.')
    parser.add_argument(
        '-j', '--json', action='store_true',
        help='Dump header as json data.')
    parser.add_argument(
        '--describe', action='store_true',
        help='Describe header fields.')
    parser.add_argument(
        'filenames', nargs='+',
        help='File to process. Should be one or three files.')
    return parser.parse_args()


def _make_property(field, get_fn_name):
    return property(
        lambda self: getattr(self, get_fn_name)(field),
        lambda self, value: self.set(field, value),
        lambda self: self.set(field, None),
        'Alias for "{}" field. {}'.format(field,
                                          header.FIELD_DESCRIPTIONS[field]),
    )


# Monkey patch SACFile to make attributes available by their friendly names.
# Makes the same friendly names an alias for SACGroup.check of the value. The
# idea being, if the values are not equal, they should be accessed on the
# components separately.
def _monkey_patch():
    for field, friendly_name in header.FRIENDLY_NAMES.viewitems():
        # Separate function necessary to properly enclose field value.
        setattr(SACFile, friendly_name, _make_property(field, 'get'))
        setattr(SACGroup, friendly_name,
                _make_property(field, 'check_or_get'))


_monkey_patch()


if __name__ == '__main__':
    main()
