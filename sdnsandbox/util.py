import time
import logging
import math
from dataclasses import dataclass
from typing import Dict

from geopy.distance import geodesic
from subprocess import run, PIPE
from pkg_resources import resource_filename
from os.path import join as pj
from re import fullmatch

lightspeed_m_per_millisec = 299792.458
optical_fibre_refraction_index = 1.4475
optical_fibre_lightspeed_m_per_millisec = lightspeed_m_per_millisec / optical_fibre_refraction_index


def countdown(printer_func, seconds, time_format='{:02d}:{:02d}', delay_func=time.sleep):
    while seconds:
        mins, secs = divmod(seconds, 60)
        time_left = time_format.format(mins, secs)
        printer_func(time_left)
        delay_func(1)
        seconds -= 1
    printer_func('Done!')


def remove_bad_chars(text, bad_chars):
    for c in bad_chars:
        if c in text:
            text = text.replace(c, "")
    return text


def calculate_geodesic_latency(lat_src, long_src, lat_dst, long_dst):
    """Effective speed based on https://en.wikipedia.org/wiki/Optical_fiber"""
    dist = geodesic((lat_src, long_src), (lat_dst, long_dst)).meters
    return dist / optical_fibre_lightspeed_m_per_millisec


def calculate_manual_geodesic_latency(lat_src, long_src, lat_dst, long_dst):
    """This is here for backwards compatibility.
       CALCULATION EXPLANATION

       Distance formula:
       dist(SP,EP) = arccos{ sin(La[EP]) * sin(La[SP]) + cos(La[EP]) * cos(La[SP]) * cos(Lo[EP] - Lo[SP])} * r
       Earth's r = 6378.137 km

       Latency formula:
       t = distance / speed of light
       t (in ms) = ( distance in km * 1000 (for meters) ) / ( speed of light / 1000 (for ms))"""
    logging.debug("Calculating with src_lat=%s src_lon=%s dst_lat=%s dst_lon=%s",
                  lat_src, long_src,
                  lat_dst, long_dst)
    latitude_src = math.radians(lat_src)
    latitude_dst = math.radians(lat_dst)
    longitude_src = math.radians(long_src)
    longitude_dst = math.radians(long_dst)
    first_product = math.sin(latitude_dst) * math.sin(latitude_src)
    second_product_first_part = math.cos(latitude_dst) * math.cos(latitude_src)
    second_product_second_part = math.cos(longitude_dst - longitude_src)
    distance = math.acos(first_product + (second_product_first_part * second_product_second_part)) * 6378.137
    return (distance * 1000) / optical_fibre_lightspeed_m_per_millisec


def run_script(script_name, info_print, err_print):
    script_path = resource_filename('sdnsandbox', pj("scripts", script_name))
    result = run(script_path, universal_newlines=True, stdout=PIPE, stderr=PIPE)
    if result.stdout:
        info_print(result.stdout)
    if result.stderr:
        err_print(result.stderr)
    result.check_returncode()


@dataclass
class Interface:
    num: int
    name: str
    net_meaning: str


def get_interface_net_meaning(intf_name: str, switches: Dict[int, str]):
    split = intf_name.split('@')
    for switch in split:
        switch_name = switch.split('-')[0]
        switch_num = int(switch_name[1:])
        intf_name = intf_name.replace(switch_name+'-', switches[switch_num]+'-')
    return intf_name


def get_inter_switch_port_interfaces(switches: Dict[int, str],
                                     port_re="s[0-9]+-eth[0-9]+@s[0-9]+-eth[0-9]+",
                                     ip_a_getter=lambda:
                                     run(["ip", "a"], universal_newlines=True, stdout=PIPE, stderr=PIPE).stdout,
                                     interface_meaning_getter=get_interface_net_meaning)\
        -> Dict[int, Interface]:
    ip_a_out = ip_a_getter()
    interfaces = {}
    for line in ip_a_out.splitlines():
        # ignore none-main lines (those with extra data, not intf definition)
        if line[0] == ' ':
            continue
        intf_split = line.split(':')
        intf_num = int(intf_split[0])
        intf_name = intf_split[1].strip()
        logging.debug("found interface #%d: \n%s", intf_num, intf_name)
        if fullmatch(port_re, intf_name):
            interfaces[intf_num] = Interface(intf_num, intf_name, interface_meaning_getter(intf_name, switches))
        else:
            logging.debug("Interface %s doesn't have inter switch port name, irrelevant - dropped...", intf_name)
    return interfaces
