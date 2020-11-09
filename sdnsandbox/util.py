import time
import logging
import math
from geopy.distance import geodesic
from subprocess import run, PIPE
from pkg_resources import resource_filename
from os.path import join as pj

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


def _calculate_latency(lat_src, long_src, lat_dst, long_dst):
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


def run_script(script_name):
    script_path = resource_filename('sdnsandbox', pj("scripts", script_name))
    result = run(script_path, universal_newlines=True, stdout=PIPE, stderr=PIPE)
    if result.stdout:
        logging.info(result.stdout)
    if result.stderr:
        logging.error(result.stderr)
    result.check_returncode()

