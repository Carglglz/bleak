"""
Utils to work with binary data or bytes
 """

import struct
from binascii import hexlify


def encode_FLOAT_ieee11073(value, precision=1, debug=False):
    """
    Binary representation of float value as IEEE-11073:20601 32-bit FLOAT

    FLOAT-Type is defined as a 32-bit value with a 24-bit mantissa and an 8-bit exponent.

    - https://community.hiveeyes.org/t/implementing-ble-gatt-ess-characteristics-with-micropython/2413/3
    """
    encoded = int(value * (10 ** precision)).to_bytes(3, 'little',
                                                      signed=True) + struct.pack('<b', -precision)
    if debug:
        hxval = hexlify(encoded)
        stbytes = hxval.decode()[::-1]
        print('0x'+''.join([stbytes[i-2:i][::-1]
                            for i in range(2, len(stbytes)+2, 2)]))
    return encoded


def decode_FLOAT_ieee11073(value):
    """Defined in ISO/IEEE Std. 11073-20601TM-2008:

    FLOAT-Type is defined as a 32-bit value with a 24-bit mantissa and an 8-bit exponent.

    Special Values:
        > +INFINITY : [exponent 0, mantissa +(2^23 –2) → 0x007FFFFE]
        > NaN (Not a Number): [exponent 0, mantissa +(2^23 –1) → 0x007FFFFF]
        > NRes (Not at this Resolution) [exponent 0, mantissa –(2^23) → 0x00800000]
        > Reserved for future use [exponent 0, mantissa –(2^23–1) → 0x00800001]
        > – INFINITY [exponent 0, mantissa –(2^23 –2) → 0x00800002]
    """
    special_values = {2**23-2: '+INFINITY', 2**23-1: 'NaN',  -2**23: 'NRes',
                      -(2**23-1): 'Reserved for future use',
                      -(2**23-2): '–INFINITY'}
    # UNPACK SIGN, EXPONENT
    sign, exponent = struct.unpack('4b', value)[-2:]
    # SEPARATE EXPONENT AND MANTISSA
    if sign >= 0:
        # PAD MANTISSA TO BE 32 bit Int
        _mantissa_bytes = bytes(value[:-1]) + b'\x00'
    else:
        # PAD MANTISSA TO BE 32 bit Int
        _mantissa_bytes = bytes(value[:-1]) + b'\xff'

    # UNPACK MANTISSA
    mantissa, = struct.unpack('i', _mantissa_bytes)

    # COMPUTE
    # CHECK IF SPECIAL VALUE
    if exponent == 0:
        if mantissa in special_values:
            return special_values[mantissa]

    float_val = mantissa / (1 / (10**exponent))
    return float_val


def twos_comp(val, bits):
    """compute the 2's complement of int value val

    - https://stackoverflow.com/questions/1604464/twos-complement-in-python"""

    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val & ((2 ** bits) - 1)     # return positive value as is


def encode_SFLOAT_ieee11073(value, precision=1, debug=False):
    """
    Binary representation of float value as  ISO/IEEE Std. 11073-20601TM-2008: 16-Bit FLOAT

    The SFLOAT-Type is defined as a 16-bit value with 12-bit mantissa and 4-bit exponent
    """
    val = int(value * (10 ** precision))
    assert val < 2**11, 'Mantissa too big'
    encoded = ((precision << 12) + twos_comp(val, 12)
               ).to_bytes(2, 'little', signed=True)
    if debug:
        hxval = hexlify(encoded)
        stbytes = hxval.decode()[::-1]
        print('0x'+''.join([stbytes[i-2:i][::-1]
                            for i in range(2, len(stbytes)+2, 2)]))
    return encoded


def twos_comp_dec(val, bits):
    """compute the 2's complement of int value val

    - https://stackoverflow.com/questions/1604464/twos-complement-in-python"""

    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val


def decode_SFLOAT_ieee11073(value):
    """Defined in ISO/IEEE Std. 11073-20601TM-2008:

    SFLOAT-Type is defined as a 16-bit value with 12-bit mantissa and 4-bit exponent.
    The 16–bit value contains a 4-bit exponent to base 10, followed by a 12-bit mantissa.
    Each is in twos- complement form.

    Special Values:
        > +INFINITY : [exponent 0, mantissa +(2^11 –2) → 0x07FE]
        > NaN (Not a Number): [exponent 0, mantissa +(2^11 –1) → 0x07FF]
        > NRes (Not at this Resolution) [exponent 0, mantissa –(2^11) → 0x0800]
        > Reserved for future use [exponent 0, mantissa –(2^11 –1) → 0x0801]
        > – INFINITY [exponent 0, mantissa –(2^11 –2) → 0x0802]
    """
    special_values = {2**11-2: '+INFINITY', 2**11-1: 'NaN',  -2**11: 'NRes', -
                      (2**11-1): 'Reserved for future use', -(2**11-2): '–INFINITY'}
    # UNPACK SIGN, EXPONENT
    _bitmask_mant = eval(
        "0b{}".format("0" * (16 - (0 + 12)) + (12 * "1") + "0" * 0)
    )
    dec = (value[1] << 8) + value[0]
    exponent = dec >> 12
    _mantissa_uint = (dec & _bitmask_mant) >> 0
    mantissa = twos_comp_dec(_mantissa_uint, 12)

    # COMPUTE
    # CHECK IF SPECIAL VALUE
    if exponent == 0:
        if mantissa in special_values:
            return special_values[mantissa]

    float_val = mantissa / ((10**exponent))
    return float_val


class SuperStruct:
    def __init__(self):
        self._version = 'Struct class ieee11073 compliant'
        self.len_F = 4  # bytes # 8 bit * 4 --> (32 bit)
        self.len_SF = 2  # bytes # 8 bit * 2 --> (16 bit)
        self.spec_formats = ['F', 'S']

    def __repr__(self):
        return(self._version)

    def unpack(self, fmt, bb):
        if any([f in self.spec_formats for f in fmt]):
            values, index = self._get_all_index_bytes(fmt, bb)
            return tuple(values)

        else:
            return struct.unpack(fmt, bb)

    def _get_all_index_bytes(self, fmt_string, bb):
        indexes = []
        intermediate_fmt_string = ""
        values = []
        index = 0
        expected_size = self._get_overall_size(fmt_string)
        assert len(bb) == expected_size, 'unpack requires a buffer of {} bytes'.format(
            expected_size)
        for s in fmt_string:
            if s in self.spec_formats:
                if intermediate_fmt_string:
                    val = struct.unpack(
                        intermediate_fmt_string, bb[index:index+struct.calcsize(intermediate_fmt_string)])
                    for v in val:
                        values.append(v)
                    index += struct.calcsize(intermediate_fmt_string)
                indexes.append(index)
                if s == 'F':
                    val_F = decode_FLOAT_ieee11073(bb[index:index+self.len_F])
                    values.append(val_F)
                    index += self.len_F
                elif s == 'S':
                    val_S = decode_SFLOAT_ieee11073(
                        bb[index:index+self.len_SF])
                    values.append(val_S)
                    index += self.len_SF
                intermediate_fmt_string = ""
            else:
                intermediate_fmt_string += s

        if intermediate_fmt_string:
            val = struct.unpack(
                intermediate_fmt_string, bb[index:index + struct.calcsize(intermediate_fmt_string)])
            for v in val:
                values.append(v)

        return (values, indexes)

    def _get_overall_size(self, fmt_string):
        intermediate_fmt_string = ""
        size_value = 0
        index = 0
        for s in fmt_string:
            if s in self.spec_formats:
                if intermediate_fmt_string:
                    size_value += struct.calcsize(intermediate_fmt_string)
                    index += struct.calcsize(intermediate_fmt_string)
                if s == 'F':
                    size_value += self.len_F
                elif s == 'S':
                    size_value += self.len_SF
                intermediate_fmt_string = ""
            else:
                intermediate_fmt_string += s

        if intermediate_fmt_string:
            size_value += struct.calcsize(intermediate_fmt_string)
        return size_value

    def calcsize(self, fmt):
        return self._get_overall_size(fmt)
