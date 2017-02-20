# -*- coding: utf-8
"""
Using the pvlib with feedinlib's weather object.
Using the windpowerlib with feedinlib's weather object.
"""

from matplotlib import pyplot as plt
import pvlib
import logging
import oemof.db as db
from oemof.db import coastdat
import os
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.tools import cosd
import feedinlib.weather as weather
from windpowerlib import basicmodel
from urllib.request import urlretrieve
from shapely import geometry as geopy

print(pvlib.__version__)

wittenberg = {
    'altitude': 34,
    'name': 'Wittenberg',
    'latitude': 52,
    'longitude': 13,
    }

logging.getLogger().setLevel(logging.INFO)

# loading feedinlib's weather data
my_weather = weather.FeedinWeather()
my_weather.read_feedinlib_csv('weather_wittenberg.csv')
# print(my_weather.data)
# my_weather.data.plot()
# plt.show()
# exit(0)
# #####################################
# ********** pvlib ********************
# #####################################

conn = db.connection()
my_weather_single = coastdat.get_weather(
    conn, geopy.Point(wittenberg['longitude'], wittenberg['latitude']), 2010)

my_weather = my_weather_single
wittenberg = {
    'altitude': 34,
    'name': 'Wittenberg',
    'latitude': my_weather.latitude,
    'longitude': my_weather.longitude,
    }
# preparing the weather data to suit pvlib's needs
# different name for the wind speed
my_weather.data.rename(columns={'v_wind': 'wind_speed'}, inplace=True)
# temperature in degree Celsius instead of Kelvin
my_weather.data['temp_air'] = my_weather.data.temp_air - 273.15
# calculate ghi

# time index from weather data set
times = my_weather.data.index

# get module and inverter parameter from sandia database
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')

# own module parameters
invertername = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'
yingli210 = {
    'module_parameters': sandia_modules['Yingli_YL210__2008__E__'],
    'inverter_parameters': sapm_inverters[invertername],
    'surface_azimuth': 180,
    'surface_tilt': 60,
    'albedo': 0.2,
    }

my_weather.data['ghi'] = my_weather.data.dirhi + my_weather.data.dhi

if my_weather.data.get('dni') is None:
    my_weather.data['dni'] = (my_weather.data.ghi - my_weather.data.dhi) / cosd(
        Location(**wittenberg).get_solarposition(times).zenith.clip(upper=90))

# pvlib's ModelChain
mc = ModelChain(PVSystem(**yingli210),
                Location(**wittenberg),
                orientation_strategy='south_at_latitude_tilt')
mc.complete_irradiance(my_weather.data.index, weather=my_weather.data)
mc.run_model(times)
# mc.complete_irradiance(i.index, i[['ghi', 'dni']])
# mc.weather.plot()
# mc.complete_irradiance(i.index, i[['dhi', 'dni']])
# mc.weather.plot()
# mc.complete_irradiance(i.index, i[['ghi', 'dhi']])
# mc.weather.plot()
mc.dc.p_mp.fillna(0).plot()
plt.show()

# print(mc.weather)
exit(0)

# plot the results
mc.dc.p_mp.fillna(0).plot()

plt.show()
logging.info('Done!')
