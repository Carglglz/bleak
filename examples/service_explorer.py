"""
Service Explorer
----------------

An example showing how to access and print out the services, characteristics and
descriptors of a connected GATT server.

Created on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""
import platform
import asyncio
import logging

from bleak import BleakClient
from bleak.utils import get_char_value, pformat_char_value
from bleak.uuids import uuidstr_to_str


async def run(address, loop, debug=False):
    log = logging.getLogger(__name__)
    if debug:
        import sys

        loop.set_debug(True)
        log.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        log.addHandler(h)

    async with BleakClient(address, loop=loop) as client:
        x = await client.is_connected()
        log.info("Connected: {0}".format(x))

        for service in client.services:
            log.info("[Service] {0}: {1}".format(service.uuid, service.description))
            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = bytes(await client.read_gatt_char(char.uuid))
                        value = get_char_value(value, char)
                        pretty_format = pformat_char_value(value,
                                                           one_line=True,
                                                           prnt=False, rtn=True)
                    except Exception as e:
                        print(e)
                        value = str(e).encode()
                        pretty_format = value
                else:
                    value = None
                    pretty_format = value
                log.info(
                    "\t[Characteristic] {0}: (Handle: {1}) ({2}) | Name: {3}, Value: {4} ".format(
                        char.uuid,
                        char.handle,
                        ",".join(char.properties),
                        uuidstr_to_str(char.uuid),
                        pretty_format,
                    )
                )
                for descriptor in char.descriptors:
                    value = await client.read_gatt_descriptor(descriptor.handle)
                    log.info(
                        "\t\t[Descriptor] {0}: (Handle: {1}) | Value: {2} ".format(
                            descriptor.uuid, descriptor.handle, bytes(value)
                        )
                    )


if __name__ == "__main__":
    address = (
        "24:71:89:cc:09:05"
        if platform.system() != "Darwin"
        else "6DC9757A-EBAD-4B8E-B535-FF65D267A2BB"
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, True))
