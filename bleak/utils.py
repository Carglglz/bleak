# -*- coding: utf-8 -*-
import struct
import bleak
import xml.etree.ElementTree as ET
import traceback
from typing import Union
from bleak.uuids import uuidstr_to_str
from bleak.backends.characteristic import BleakGATTCharacteristic

CHARS_XML_DIR = "{}/characteristics_xml".format(bleak.__path__[0])

# UNITS

CHARS_UNITS = {
    "meter": "m",
    "kilogram": "kg",
    "second": "s",
    "ampere": "A",
    "kelvin": "K",
    "mole": "mol",
    "candela": "cd",
    "square meter": "m2",
    "cubic meter": "m3",
    "meter per second": "m/s",
    "metres per second": "m/s",
    "meter per second squared  ": "m/s2",
    "reciprocal meter": "m-1",
    "kilogram per cubic meter": "kg/m3",
    "cubic meter per kilogram": "m3/kg",
    "ampere per square meter": "A/m2",
    "ampere per meter": "A/m",
    "mole per cubic meter": "mol/m3",
    "candela per square meter": "cd/m2",
    "kilogram per kilogram": "kg/kg",
    "radian": "rad",
    "steradian": "sr",
    "hertz": "Hz",
    "newton": "N",
    "pascal": "Pa",
    "joule": "J",
    "watt": "W",
    "coulomb": "C",
    "volt": "V",
    "farad": "F",
    "ohm": "Ω",
    "siemens": "S",
    "weber": "Wb",
    "tesla": "T",
    "henry": "H",
    "degree celsius": "°C",
    "lumen": "lm",
    "lux": "lx",
    "becquerel": "Bq",
    "gray": "Gy",
    "sievert": "Sv",
    "katal": "kat",
    "pascal second": "Pa·s",
    "newton meter": "N·m",
    "newton per meter": "N/m",
    "radian per second": "rad/s",
    "radian per second squared": "rad/s2",
    "watt per square meter": "W/m2",
    "joule per kelvin": "J/K",
    "joule per kilogram kelvin": "J/(kg·K)",
    "joule per kilogram": "J/kg",
    "watt per meter kelvin": "W/(m·K)",
    "joule per cubic meter": "J/m3",
    "volt per meter": "V/m",
    "coulomb per cubic meter": "C/m3",
    "coulomb per square meter": "C/m2",
    "farad per meter": "F/m",
    "henry per meter": "H/m",
    "joule per mole": "J/mol",
    "joule per mole kelvin": "J/(mol·K)",
    "coulomb per kilogram": "C/kg",
    "gray per second": "Gy/s",
    "watt per steradian": "W/sr",
    "watt per square meter steradian": "W/(m2·sr)",
    "katal per cubic meter": "kat/m3",
    "percentage": "%",
    "beats per minute": "bpm",
    "year": "Y",
    "month": "M",
    "day": "D",
    "watt per square metre": "W/m^2",
    "degree": "º",
    "degree fahrenheit": "ºF",
    "decibel": "dBm",
    "kilometre per hour": "km/h",
    "count per cubic metre": "1/m^3",
    "minute": "min",
    "kilogram per litre": "kg/L",
    "mole per litre": "mol/L",
    "inch": "in",
    "pound": "lb",
    "revolution per minute": "RPM",
    "kilogram calorie": "kcal",
    "kilometre per minute": "km/min",
    "metre": "m",
    "step per minute": "stp/min",
    "stroke per minute": "str/min",
    "hour": "h",
    "newton metre": "Nm",
}


# DATA UNPACK FORMATS

DATA_FMT = {
    "sint8": "b",
    "uint8": "B",
    "sint16": "h",
    "uint16": "H",
    "uint24": "I",
    "sint32": "i",
    "uint32": "I",
    "uint40": "Q",
    "uint48": "Q",
    "utf8s": "utf8",
    "8bit": "B",
    "16bit": "h",
    "float64": "d",
    "variable": "X",
    "gatt_uuid": "X",
    "boolean": "?",
    "32bit": "I",
    "FLOAT": "f",
    "24bit": "I",
    "SFLOAT": "f",
    "sint24": "I",
    "nibble": "B",
    "2bit": "B",
    "uint128": "2Q",
    "uint12": "H",
    "4bit": "B",
    "characteristic": "X",
}


# XML PARSER --> get char tag and return char_xml class
class CHAR_XML:
    """Parse characteristic xml file"""

    def __init__(self, xml_file):
        self._tree = ET.parse("{}/{}".format(CHARS_XML_DIR, xml_file))
        self._root = self._tree.getroot()
        self.char_metadata = None
        self.name = None
        self.char_type = None
        self.uuid = None
        self.xml_tags = {}
        self.fields = {}
        self._actual_field = None
        self.bitfields = {}
        self._actual_bitfield = None
        self._actual_bit = None
        self._nr = 0
        self._get_data()
        self._get_fields()

    def _get_data(self):
        for val in self._root.iter():
            try:
                if hasattr(val.text, "strip"):
                    self.xml_tags[val.tag] = [val.text.strip(), val.attrib]
                else:
                    self.xml_tags[val.tag] = [val.text, val.attrib]
                if val.tag == "Characteristic":
                    self.char_metadata = val.attrib
                    self.name = self.char_metadata["name"]
                    self.char_type = self.char_metadata["type"]
                    self.uuid = self.char_metadata["uuid"]
            except Exception as e:
                print(traceback.format_exc())

    def _get_fields(self):
        for val in self._root.iter():
            try:
                if val.tag == "Field":
                    self.fields[val.attrib["name"]] = {}
                    self._actual_field = val.attrib["name"]

                if val.tag == "Maximum":
                    if hasattr(val.text, "strip"):
                        if self.fields.keys():
                            self.fields[self._actual_field][val.tag] = val.text.strip()
                    else:
                        if self.fields.keys():
                            self.fields[self._actual_field][val.tag] = val.text
                if val.tag == "Minimum":
                    if hasattr(val.text, "strip"):
                        if self.fields.keys():
                            self.fields[self._actual_field][val.tag] = val.text.strip()
                    else:
                        if self.fields.keys():
                            self.fields[self._actual_field][val.tag] = val.text
                if val.tag == "Requirement":
                    try:
                        if self.fields.keys():
                            if val.tag in self.fields[self._actual_field].keys():
                                self._nr += 1
                                self.fields[self._actual_field][
                                    "{}-{}".format(val.tag, self._nr)
                                ] = val.text
                            else:
                                self.fields[self._actual_field][val.tag] = val.text
                    except Exception as e:
                        print(e)
                if val.tag == "Format":
                    if self.fields.keys():
                        self.fields[self._actual_field][val.tag] = val.text
                        self.fields[self._actual_field]["Ctype"] = DATA_FMT[val.text]

                if val.tag == "Enumeration":
                    if self.fields.keys():
                        if "Enumerations" in self.fields[self._actual_field].keys():
                            self.fields[self._actual_field]["Enumerations"][
                                val.attrib["key"]
                            ] = val.attrib["value"]
                            if "requires" in val.attrib:
                                if (
                                    "Requires"
                                    not in self.fields[self._actual_field][
                                        "Enumerations"
                                    ]
                                ):
                                    self.fields[self._actual_field]["Enumerations"][
                                        "Requires"
                                    ] = {}
                                self.fields[self._actual_field]["Enumerations"][
                                    "Requires"
                                ][val.attrib["key"]] = val.attrib["requires"]

                        else:
                            self.fields[self._actual_field]["Enumerations"] = {}
                            self.fields[self._actual_field]["Enumerations"][
                                val.attrib["key"]
                            ] = val.attrib["value"]
                            if "requires" in val.attrib:
                                if (
                                    "Requires"
                                    not in self.fields[self._actual_field][
                                        "Enumerations"
                                    ]
                                ):
                                    self.fields[self._actual_field]["Enumerations"][
                                        "Requires"
                                    ] = {}
                                self.fields[self._actual_field]["Enumerations"][
                                    "Requires"
                                ][val.attrib["key"]] = val.attrib["requires"]

                if val.tag == "Enumerations":
                    if self.fields.keys():
                        self.fields[self._actual_field][val.tag] = {}

                if val.tag == "BitField":
                    if self.fields.keys():
                        self.fields[self._actual_field][val.tag] = {}
                    self._actual_bitfield = val.tag
                if val.tag == "Bit":
                    if self.fields[self._actual_field].keys():
                        if "name" in val.attrib.keys():
                            bitname = val.attrib["name"]
                        else:
                            bitname = "BitGroup {}".format(val.attrib["index"])
                        self.fields[self._actual_field][self._actual_bitfield][
                            bitname
                        ] = {}
                        self.fields[self._actual_field][self._actual_bitfield][bitname][
                            "index"
                        ] = val.attrib["index"]
                        self.fields[self._actual_field][self._actual_bitfield][bitname][
                            "size"
                        ] = val.attrib["size"]
                        self._actual_bit = bitname

                if val.tag == "Enumeration":
                    if self._actual_bitfield is not None:
                        if (
                            self._actual_bitfield
                            in self.fields[self._actual_field].keys()
                        ):
                            if self.fields[self._actual_field][
                                self._actual_bitfield
                            ].keys():
                                self.fields[self._actual_field][self._actual_bitfield][
                                    self._actual_bit
                                ]["Enumerations"][val.attrib["key"]] = val.attrib[
                                    "value"
                                ]
                                if "requires" in val.attrib:
                                    if (
                                        "Requires"
                                        not in self.fields[self._actual_field][
                                            self._actual_bitfield
                                        ][self._actual_bit]["Enumerations"]
                                    ):
                                        self.fields[self._actual_field][
                                            self._actual_bitfield
                                        ][self._actual_bit]["Enumerations"][
                                            "Requires"
                                        ] = {}
                                    self.fields[self._actual_field][
                                        self._actual_bitfield
                                    ][self._actual_bit]["Enumerations"]["Requires"][
                                        val.attrib["key"]
                                    ] = val.attrib[
                                        "requires"
                                    ]

                if val.tag == "Enumerations":
                    if self._actual_bitfield is not None:
                        if (
                            self._actual_bitfield
                            in self.fields[self._actual_field].keys()
                        ):
                            if self.fields[self._actual_field][
                                self._actual_bitfield
                            ].keys():
                                self.fields[self._actual_field][self._actual_bitfield][
                                    self._actual_bit
                                ][val.tag] = {}
                if val.tag == "DecimalExponent":
                    if self.fields.keys():
                        self.fields[self._actual_field][val.tag] = int(val.text)

                if val.tag == "Unit":
                    self.fields[self._actual_field]["Unit_id"] = val.text
                    # get unit from unit stringcode
                    unit_stringcode_filt = val.text.replace("org.bluetooth.unit.", "")
                    quantity = " ".join(unit_stringcode_filt.split(".")[0].split("_"))
                    self.fields[self._actual_field]["Quantity"] = quantity
                    try:
                        unit = " ".join(
                            unit_stringcode_filt.split(".")[1].split("_")
                        ).strip()
                        self.fields[self._actual_field][val.tag] = unit
                        self.fields[self._actual_field]["Symbol"] = CHARS_UNITS[unit]
                    except Exception as e:
                        try:
                            self.fields[self._actual_field][val.tag] = quantity
                            self.fields[self._actual_field]["Symbol"] = CHARS_UNITS[
                                quantity
                            ]
                        except Exception as e:
                            self.fields[self._actual_field][val.tag] = ""
                            self.fields[self._actual_field]["Symbol"] = ""
                if val.tag == "InformativeText":
                    if self.fields.keys():
                        if hasattr(val.text, "strip"):
                            self.fields[self._actual_field][val.tag] = val.text.strip()
                        else:
                            self.fields[self._actual_field][val.tag] = val.text
                if val.tag == "Reference":
                    if self.fields.keys():
                        if hasattr(val.text, "strip"):
                            self.fields[self._actual_field][val.tag] = val.text.strip()
                        else:
                            self.fields[self._actual_field][val.tag] = val.text
                if val.tag == "BinaryExponent":
                    if self.fields.keys():
                        if hasattr(val.text, "strip"):
                            self.fields[self._actual_field][val.tag] = int(
                                val.text.strip()
                            )
                        else:
                            self.fields[self._actual_field][val.tag] = int(val.text)
                if val.tag == "Multiplier":
                    if self.fields.keys():
                        if hasattr(val.text, "strip"):
                            self.fields[self._actual_field][val.tag] = int(
                                val.text.strip()
                            )
                        else:
                            self.fields[self._actual_field][val.tag] = int(val.text)

                if val.tag == "Reference":
                    if self.fields.keys():
                        if hasattr(val.text, "strip"):
                            self.fields[self._actual_field][val.tag] = " ".join(
                                ch.capitalize()
                                for ch in val.text.strip().split(".")[-1].split("_")
                            )
                        else:
                            self.fields[self._actual_field][val.tag] = val.text
            except Exception as e:
                print(traceback.format_exc())


def get_xml_char(characteristic: Union[str, BleakGATTCharacteristic])-> CHAR_XML:
    """Get characteristic metadata from its xml file

    Args:
        characteristic (str, BleakGATTCharacteristic): The name of the
                    characteristic or bleak characteristic class

    Returns:
            characteristic metatada class (CHAR_XML): The characteristic
            metadata parsed from its xml file
        """
    if isinstance(characteristic, BleakGATTCharacteristic):
        characteristic = uuidstr_to_str(characteristic.uuid)
    if "Magnetic Flux" in characteristic:
        char_string = "_".join(
            [
                ch.lower().replace("magnetic", "Magnetic")
                for ch in characteristic.replace("-", " ", 10).replace("–", " ").split()
            ]
        )
        char_string = char_string.replace("3d", "3D").replace("2d", "2D")
    else:
        char_string = "_".join(
            [ch.lower() for ch in characteristic.replace("-", " ", 10).replace("–", " ").split()]
        )
    char_string += ".xml"
    char_string = char_string.replace("_characteristic", "")
    return CHAR_XML(char_string)


def _unpack_data(ctype, data):
    """Unpack 'data' bytes with 'ctype' equivalent format
    """
    if ctype == "utf8":
        return data.decode("utf8")
    else:
        (data,) = struct.unpack(ctype, data)
        return data


# BITMASKS

def _complete_bytes(self, bb):
    """Make bytes number even"""
    len_bytes = len(bb)
    if (len_bytes % 2) == 0:
        pass
    else:
        bb = b'\x00' + bb
    return bb


def _autobitmask(val, total_size, index, size, keymap):
    """Generate a bitmask and apply it to 'val' bits given the 'total_size',
        'index', and 'size' of the BitField"""
    _bitmask = eval(
        "0b{}".format("0" * (total_size - (index + size)) + (size * "1") + "0" * index)
    )
    key = (val & _bitmask) >> index
    key_str = str(key)
    mapped_val = keymap[key_str]
    return mapped_val


def _autobitmask_req(val, total_size, index, size, keymap):
    """Generate a bitmask and apply it to 'val' bits given the 'total_size',
        'index', and 'size' of the BitField"""
    _bitmask = eval(
        "0b{}".format("0" * (total_size - (index + size)) + (size * "1") + "0" * index)
    )
    key = (val & _bitmask) >> index
    key_str = str(key)
    if key_str in keymap:
        mapped_val = keymap[key_str]
        return mapped_val
    else:
        return False


# AUTOFORMAT BITFIELDS

# FLAG VALUES


def _autoformat(char, val, field_to_unpack=None):
    """Given a characteristic and 'val' bytes, obtain the BitField values"""
    fields = {}
    if not field_to_unpack:
        for field in char.fields:
            if "Ctype" in char.fields[field]:
                # ctype = char.fields[field]['Ctype']
                total_size = 0
                if "BitField" in char.fields[field]:
                    fields[field] = {}
                    bitfield = char.fields[field]["BitField"]
                    for bitf in bitfield:
                        total_size += int(bitfield[bitf]["size"])
                    for bitf in bitfield:
                        size = int(bitfield[bitf]["size"])
                        index = int(bitfield[bitf]["index"])
                        key_map = bitfield[bitf]["Enumerations"]
                        fields[field][bitf] = _autobitmask(
                            val,
                            total_size=total_size,
                            index=index,
                            size=size,
                            keymap=key_map,
                        )

        return fields
    else:
        field = field_to_unpack
        if "Ctype" in char.fields[field]:
            # ctype = char.fields[field]['Ctype']
            total_size = 0
            if "BitField" in char.fields[field]:
                fields[field] = {}
                bitfield = char.fields[field]["BitField"]
                for bitf in bitfield:
                    total_size += int(bitfield[bitf]["size"])
                for bitf in bitfield:
                    size = int(bitfield[bitf]["size"])
                    index = int(bitfield[bitf]["index"])
                    key_map = bitfield[bitf]["Enumerations"]
                    fields[field][bitf] = _autobitmask(
                        val,
                        total_size=total_size,
                        index=index,
                        size=size,
                        keymap=key_map,
                    )

        return fields


# FIELDS REQUIREMENTS


def _autoformat_reqs(char, val):
    """Given a 'char' characteristic and 'val' bytes, obtain the BitField values
    requirements"""
    fields = {}
    for field in char.fields:
        if "Ctype" in char.fields[field]:
            # ctype = char.fields[field]['Ctype']
            total_size = 0
            if "BitField" in char.fields[field]:
                fields[field] = {}
                bitfield = char.fields[field]["BitField"]
                for bitf in bitfield:
                    total_size += int(bitfield[bitf]["size"])
                for bitf in bitfield:
                    size = int(bitfield[bitf]["size"])
                    index = int(bitfield[bitf]["index"])
                    key_map = bitfield[bitf]["Enumerations"]
                    if "Requires" in key_map:
                        fields[field][bitf] = _autobitmask_req(
                            val,
                            total_size=total_size,
                            index=index,
                            size=size,
                            keymap=key_map["Requires"],
                        )

    return fields


# GET FIELD REQUIREMENTS
def _get_req(char_field):
    """Get characteristics field requirements"""
    reqs = []
    for key in char_field:
        if "Requirement" in key:
            reqs.append(char_field[key])
    return reqs


# GET FORMATTED VALUE

def _get_single_field(char, val, debug=False):
    """Get characteristic single field data"""
    if debug:
        print("CASE 1: ONE FIELD")
    for field in char.fields:
        if "Ctype" in char.fields[field]:
            ctype = char.fields[field]["Ctype"]
            if "BitField" in char.fields[field]:
                if debug:
                    print("CASE 1A: BITFIELD")
                (raw_data,) = struct.unpack(ctype, val)
                data = list(_autoformat(char, raw_data).values())[0]
                return {field: {"Value": data}}
            else:
                if debug:
                    print("CASE 1B: VALUE")
                if "Enumerations" in char.fields[field]:
                    if debug:
                        print("CASE 1B.1: MAPPED VALUE")
                    keymap = char.fields[field]["Enumerations"]
                    if keymap:
                        (data,) = struct.unpack(ctype, val)  # here read char
                        try:
                            mapped_val = keymap[str(data)]
                            return {field: {"Value": mapped_val}}
                        except Exception as e:
                            if debug:
                                print("Value not in keymap")
                    else:
                        (data,) = struct.unpack(ctype, val)
                else:
                    if debug:
                        print("CASE 1B.2: SINGLE VALUE")
                    data = _unpack_data(ctype, val)
                # Format fields values according to field metadata: (DecimalExponent/Multiplier):
                _FIELDS_VALS = {}
                _FIELDS_VALS[field] = {}
                if "Quantity" in char.fields[field]:
                    _FIELDS_VALS[field]["Quantity"] = char.fields[field]["Quantity"]
                if "Unit" in char.fields[field]:
                    _FIELDS_VALS[field]["Unit"] = char.fields[field]["Unit"]
                if "Symbol" in char.fields[field]:
                    _FIELDS_VALS[field]["Symbol"] = char.fields[field]["Symbol"]

                formatted_value = data
                if "Multiplier" in char.fields[field]:
                    formatted_value *= char.fields[field]["Multiplier"]
                if "DecimalExponent" in char.fields[field]:
                    formatted_value *= 10 ** (char.fields[field]["DecimalExponent"])
                if "BinaryExponent" in char.fields[field]:
                    formatted_value *= 2 ** (char.fields[field]["BinaryExponent"])

                _FIELDS_VALS[field]["Value"] = formatted_value
                return _FIELDS_VALS


def _get_multiple_fields(char, val, rtn_flags=False, debug=False):
    """Get characteristic multiple fields data"""
    if debug:
        print("CASE 2: MULTIPLE FIELDS")
    _FLAGS = None
    _REQS = None
    if "Flags" in char.fields:
        if debug:
            print("CASE 2.A: Flags Field Present")
        if "Ctype" in char.fields["Flags"]:
            ctype_flag = char.fields["Flags"]["Ctype"]
            if "BitField" in char.fields["Flags"]:
                (raw_data,) = struct.unpack(
                    ctype_flag, val[: struct.calcsize(ctype_flag)]
                )
                _FLAGS = list(_autoformat(char, raw_data).values())[0]
                _REQS = list(_autoformat_reqs(char, raw_data).values())[0]

    if _FLAGS:
        # Get fields according to flags
        if debug:
            print(_FLAGS)
            print(_REQS)
            print("Fields to read according to Flags:")
        _FIELDS_TO_READ = []
        for field in char.fields:
            if field != "Flags":
                field_req = None
                # get requirements if any:
                field_req = _get_req(char.fields[field])
                if "Mandatory" in field_req:
                    if debug:
                        print("   - {}: {}".format(field, True))
                    _FIELDS_TO_READ.append(field)
                else:
                    _READ_FIELD = all([req in _REQS.values() for req in field_req])
                    if _READ_FIELD:
                        if debug:
                            print("   - {}: {}".format(field, field_req))
                        _FIELDS_TO_READ.append(field)
        if _FIELDS_TO_READ:
            # get global unpack format: ctype_flag += ctype_field_to_read
            ctype_global = ctype_flag
            # REFERENCE FIELDS
            _REFERENCE_FIELDS = {}
            copy_FIELDS_TO_READ = _FIELDS_TO_READ.copy()
            for field in copy_FIELDS_TO_READ:
                if "Ctype" in char.fields[field]:
                    ctype = char.fields[field]["Ctype"]
                    ctype_global += ctype

                # Get Reference if any and ctype/unit/symbol/decexp/multiplier

                if "Reference" in char.fields[field]:
                    reference = char.fields[field]["Reference"]
                    reference_char = get_xml_char(reference)
                    _LIST_REFERENCES = []
                    for ref_field in reference_char.fields:
                        # Add fields to _REFERENCE_FIELDS
                        _LIST_REFERENCES.append(ref_field)
                        _REFERENCE_FIELDS[ref_field] = reference_char.fields[ref_field]
                        if "Ctype" in reference_char.fields[ref_field]:
                            ctype = reference_char.fields[ref_field]["Ctype"]
                            ctype_global += ctype

                    # Substitute
                    _LIST_REFERENCES.reverse()
                    char_index = _FIELDS_TO_READ.index(field)
                    _FIELDS_TO_READ.pop(char_index)
                    for rf in _LIST_REFERENCES:
                        _FIELDS_TO_READ.insert(char_index, rf)

            # Unpack data
            # First value is the flags value
            # Rest are field values
            if debug:
                print("Global Unpack Format: {}".format(ctype_global))
            val = _complete_bytes(val)
            flag, *data = struct.unpack(ctype_global, val)
            _RAW_VALS = dict(zip(_FIELDS_TO_READ, data))
            _FIELDS_VALS = {}
            # Format fields values according to field metadata: (DecimalExponent/Multiplier):
            for field in _FIELDS_TO_READ:
                _FIELDS_VALS[field] = {}
                if field in char.fields:
                    if "Quantity" in char.fields[field]:
                        _FIELDS_VALS[field]["Quantity"] = char.fields[field]["Quantity"]
                    if "Unit" in char.fields[field]:
                        _FIELDS_VALS[field]["Unit"] = char.fields[field]["Unit"]
                    if "Symbol" in char.fields[field]:
                        _FIELDS_VALS[field]["Symbol"] = char.fields[field]["Symbol"]

                    formatted_value = _RAW_VALS[field]
                    if "Multiplier" in char.fields[field]:
                        formatted_value *= char.fields[field]["Multiplier"]
                    if "DecimalExponent" in char.fields[field]:
                        formatted_value *= 10 ** (char.fields[field]["DecimalExponent"])
                    if "BinaryExponent" in char.fields[field]:
                        formatted_value *= 2 ** (char.fields[field]["BinaryExponent"])
                    if "BitField" in char.fields[field]:
                        formatted_value = list(
                            _autoformat(char, formatted_value, field).values()
                        )[0]

                    _FIELDS_VALS[field]["Value"] = formatted_value
                else:
                    if _REFERENCE_FIELDS:
                        if "Quantity" in _REFERENCE_FIELDS[field]:
                            _FIELDS_VALS[field]["Quantity"] = _REFERENCE_FIELDS[field][
                                "Quantity"
                            ]
                        if "Unit" in _REFERENCE_FIELDS[field]:
                            _FIELDS_VALS[field]["Unit"] = _REFERENCE_FIELDS[field][
                                "Unit"
                            ]
                        if "Symbol" in _REFERENCE_FIELDS[field]:
                            _FIELDS_VALS[field]["Symbol"] = _REFERENCE_FIELDS[field][
                                "Symbol"
                            ]

                        formatted_value = _RAW_VALS[field]
                        if "Multiplier" in _REFERENCE_FIELDS[field]:
                            formatted_value *= _REFERENCE_FIELDS[field]["Multiplier"]
                        if "DecimalExponent" in _REFERENCE_FIELDS[field]:
                            formatted_value *= 10 ** (
                                _REFERENCE_FIELDS[field]["DecimalExponent"]
                            )
                        if "BinaryExponent" in _REFERENCE_FIELDS[field]:
                            formatted_value *= 2 ** (
                                _REFERENCE_FIELDS[field]["BinaryExponent"]
                            )
                        if "BitField" in _REFERENCE_FIELDS[field]:
                            # This exists ?
                            raw_data = struct.pack(
                                _REFERENCE_FIELDS[field]["Ctype"], formatted_value
                            )
                            # formatted_value = list(_autoformat(char, raw_data).values())[0]

                        _FIELDS_VALS[field]["Value"] = formatted_value

            if not rtn_flags:
                return _FIELDS_VALS
            else:
                return [_FIELDS_VALS, _FLAGS]
    else:
        if debug:
            print("CASE 2.B: Flags Field Not Present")
            print("Fields to read:")
        _FIELDS_TO_READ = []
        for field in char.fields:
            if field != "Flags":
                field_req = None
                # get requirements if any:
                field_req = _get_req(char.fields[field])
                if "Mandatory" in field_req:
                    if debug:
                        print("   - {}: {}".format(field, True))
                    _FIELDS_TO_READ.append(field)
                else:
                    _READ_FIELD = all([req in _REQS.values() for req in field_req])
                    if _READ_FIELD:
                        if debug:
                            print("   - {}: {}".format(field, field_req))
                        _FIELDS_TO_READ.append(field)

        # REFERENCE FIELDS
        _REFERENCE_FIELDS = {}
        copy_FIELDS_TO_READ = _FIELDS_TO_READ.copy()
        if _FIELDS_TO_READ:
            # get global unpack format: ctype_flag += ctype_field_to_read
            ctype_global = ""
            for field in copy_FIELDS_TO_READ:
                if "Ctype" in char.fields[field]:
                    ctype = char.fields[field]["Ctype"]
                    ctype_global += ctype

                # Get Reference if any and ctype/unit/symbol/decexp/multiplier

                if "Reference" in char.fields[field]:
                    reference = char.fields[field]["Reference"]
                    reference_char = get_xml_char(reference)
                    _LIST_REFERENCES = []
                    for ref_field in reference_char.fields:
                        # Add fields to _REFERENCE_FIELDS
                        _LIST_REFERENCES.append(ref_field)
                        _REFERENCE_FIELDS[ref_field] = reference_char.fields[ref_field]
                        if "Ctype" in reference_char.fields[ref_field]:
                            ctype = reference_char.fields[ref_field]["Ctype"]
                            ctype_global += ctype

                    # Substitute
                    _LIST_REFERENCES.reverse()
                    char_index = _FIELDS_TO_READ.index(field)
                    _FIELDS_TO_READ.pop(char_index)
                    for rf in _LIST_REFERENCES:
                        _FIELDS_TO_READ.insert(char_index, rf)

            # Unpack data
            # There is no the flags value
            # All fields are values
            if debug:
                print("Global Unpack Format: {}".format(ctype_global))
            data = struct.unpack(ctype_global, val)
            _RAW_VALS = dict(zip(_FIELDS_TO_READ, data))
            _FIELDS_VALS = {}
            # Format fields values according to field metadata: (DecimalExponent/Multiplier):
            for field in _FIELDS_TO_READ:
                _FIELDS_VALS[field] = {}
                if field in char.fields:
                    if "Quantity" in char.fields[field]:
                        _FIELDS_VALS[field]["Quantity"] = char.fields[field]["Quantity"]
                    if "Unit" in char.fields[field]:
                        _FIELDS_VALS[field]["Unit"] = char.fields[field]["Unit"]
                    if "Symbol" in char.fields[field]:
                        _FIELDS_VALS[field]["Symbol"] = char.fields[field]["Symbol"]

                    formatted_value = _RAW_VALS[field]
                    if "Multiplier" in char.fields[field]:
                        formatted_value *= char.fields[field]["Multiplier"]
                    if "DecimalExponent" in char.fields[field]:
                        formatted_value *= 10 ** (char.fields[field]["DecimalExponent"])
                    if "BinaryExponent" in char.fields[field]:
                        formatted_value *= 2 ** (char.fields[field]["BinaryExponent"])

                    _FIELDS_VALS[field]["Value"] = formatted_value
                else:
                    if _REFERENCE_FIELDS:
                        if "Quantity" in _REFERENCE_FIELDS[field]:
                            _FIELDS_VALS[field]["Quantity"] = _REFERENCE_FIELDS[field][
                                "Quantity"
                            ]
                        if "Unit" in _REFERENCE_FIELDS[field]:
                            _FIELDS_VALS[field]["Unit"] = _REFERENCE_FIELDS[field][
                                "Unit"
                            ]
                        if "Symbol" in _REFERENCE_FIELDS[field]:
                            _FIELDS_VALS[field]["Symbol"] = _REFERENCE_FIELDS[field][
                                "Symbol"
                            ]

                        formatted_value = _RAW_VALS[field]
                        if "Multiplier" in _REFERENCE_FIELDS[field]:
                            formatted_value *= _REFERENCE_FIELDS[field]["Multiplier"]
                        if "DecimalExponent" in _REFERENCE_FIELDS[field]:
                            formatted_value *= 10 ** (
                                _REFERENCE_FIELDS[field]["DecimalExponent"]
                            )
                        if "BinaryExponent" in _REFERENCE_FIELDS[field]:
                            formatted_value *= 2 ** (
                                _REFERENCE_FIELDS[field]["BinaryExponent"]
                            )

                        _FIELDS_VALS[field]["Value"] = formatted_value

            if not rtn_flags:
                return _FIELDS_VALS
            else:
                return [_FIELDS_VALS, _FLAGS]


def get_char_value(value: bytes, characteristic: Union[BleakGATTCharacteristic,
                                                       str, CHAR_XML],
                   rtn_flags: bool = False,
                   debug: bool = False) -> dict:
    """Given a characteristic and its raw value in bytes,
    obtain the formatted value as a dict instance:

    Args:
        value (bytes): The result of read_gatt_char().
        characteristic (BleakGATTCharacteristic, str, CHAR_XML):
            The characteristic from which get metadata.
        rnt_flags: return the bitflags too if present
        debug: print debug information about bytes unpacking

    Returns:
        Dict instance with the formatted value.

    """

    # Get characteristic metadata from xml file
    if isinstance(characteristic, str) or isinstance(characteristic,
                                                     BleakGATTCharacteristic):
        characteristic = get_xml_char(characteristic)
    # if isinstance(characteristic, BleakGATTCharacteristic):
    #     characteristic = get_xml_char(uuidstr_to_str(characteristic.uuid))

    if len(characteristic.fields) == 1:
        # CASE 1: ONLY ONE FIELD: SINGLE VALUE OR SINGLE BITFIELD
        return _get_single_field(characteristic, value, debug=debug)

    else:
        # CASE 2: MULTIPLE FIELDS: 1º Field flags, Rest of Fields values
        # check if Flags field exists
        # get flags and fields requirements if any
        return _get_multiple_fields(characteristic, value, rtn_flags=rtn_flags,
                                    debug=debug)


def pformat_char_value(data,
                       char="",
                       only_val=False,
                       one_line=False,
                       sep=",",
                       custom=None,
                       symbols=True,
                       prnt=True,
                       rtn=False):
    """Print or return the characteristic value in string format"""
    if not custom:
        if not one_line:
            if char:
                print("{}:".format(char))
            if not only_val:
                for key in data:
                    try:
                        print(
                            "{}: {} {}".format(
                                key, data[key]["Value"], data[key]["Symbol"]
                            )
                        )
                    except Exception as e:
                        print("{}: {} ".format(key, data[key]["Value"]))
            else:
                for key in data:
                    try:
                        print("{} {}".format(
                            data[key]["Value"], data[key]["Symbol"]))
                    except Exception as e:
                        print("{}".format(data[key]["Value"]))
        else:

            if not only_val:
                try:
                    char_string_values = [
                        "{}: {} {}".format(
                            key, data[key]["Value"], data[key]["Symbol"])
                        for key in data
                    ]
                except Exception as e:
                    char_string_values = [
                        "{}: {}".format(key, data[key]["Value"]) for key in data
                    ]
                if char:
                    if prnt:
                        print("{}: {}".format(char, sep.join(char_string_values)))
                    elif rtn:
                        return "{}: {}".format(char, sep.join(char_string_values))
                else:
                    if prnt:
                        print(sep.join(char_string_values))
                    elif rtn:
                        return sep.join(char_string_values)
            else:
                try:
                    char_string_values = [
                        "{} {}".format(data[key]["Value"], data[key]["Symbol"])
                        for key in data
                    ]
                except Exception as e:
                    char_string_values = [
                        "{}".format(data[key]["Value"]) for key in data
                    ]
                if char:
                    if prnt:
                        print("{}: {}".format(char, sep.join(char_string_values)))
                    elif rtn:
                        return "{}: {}".format(char, sep.join(char_string_values))
                else:
                    if prnt:
                        print(sep.join(char_string_values))
                    elif rtn:
                        return sep.join(char_string_values)
    else:
        if not symbols:
            print(custom.format(*[data[k]["Value"] for k in data]))
        else:
            print(
                custom.format(
                    *["{} {}".format(data[k]["Value"], data[k]["Symbol"]) for k in data]
                )
            )


def map_char_value(data, keys=[], string_fmt=False, one_line=True, sep=", "):
    """Map characteristic value with the given keys, return dict or string
    format"""
    if keys:
        if not string_fmt:
            return dict(zip(keys, list(data.values())[0]['Value'].values()))
        else:
            map_values = dict(zip(keys, list(data.values())[0]['Value'].values()))
            if one_line:
                return sep.join(["{}: {}".format(k, v) for k, v in map_values.items()])
            else:
                sep += "\n"
                return sep.join(["{}: {}".format(k, v) for k, v in map_values.items()])


def dict_char_value(data, raw=False):
    """Simplify the characteristic value in dict format"""
    try:
        if raw:
            values = {
                k: {"Value": data[k]["Value"], "Symbol": data[k]["Symbol"]}
                for k in data
            }
        else:
            values = {
                k: "{} {}".format(data[k]["Value"], data[k]["Symbol"]) for k in data
            }
    except Exception as e:
        values = {}
        if raw:
            for k in data:
                if "Symbol" in data[k]:
                    values[k] = {"Value": data[k]["Value"], "Symbol": data[k]["Symbol"]}
                else:
                    values[k] = {"Value": data[k]["Value"]}
        else:
            for k in data:
                if "Symbol" in data[k]:
                    values[k] = "{} {}".format(data[k]["Value"], data[k]["Symbol"])
                else:
                    values[k] = data[k]["Value"]
    return values


def pformat_char_flags(data, sep="\n", prnt=False, rtn=True):
    """Print or return the characteristic flag in string format"""
    try:
        char_string_values = [
            ["{}: {}".format(k, v) for k, v in data[key].items()] for key in data
        ]
        all_values = []
        for values in char_string_values:
            if prnt:
                print(sep.join(values))
            elif rtn:
                all_values.append(sep.join(values))
        if rtn:
            return sep.join(all_values)

    except Exception as e:
        print(e)


def mac_str_2_int(mac):
    """Convert colon separated hex string MAC address to integer.

    Args:
        mac (str): A colon separated hex string MAC address.

    Returns:
        MAC address as integer.

    """
    return int(mac.replace(":", ""), 16)


def mac_int_2_str(mac):
    """Convert integer MAC to colon separated hex string.

    Args:
        mac (int): A positive integer.

    Returns:
        MAC address as colon separated hex string.

    """
    m = hex(mac)[2:].upper().zfill(12)
    return ":".join([m[i: i + 2] for i in range(0, 12, 2)])
