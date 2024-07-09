# This program modifies main, using the sun instead of ISS.
# to make a solar position calculator
import pandas as pd
import ephem
import math
from datetime import datetime, timedelta

# Sun Object
sun = ephem.Sun()

# Record user input and assign to variables.
start_time_string = input("Enter start time (YYYY/MM/DD HH:MM:SS): ")
end_time_string = input("Enter end time (YYYY/MM/DD HH:MM:SS): ")
latitude = float(input("Enter Ground station latitude: "))
longitude = float(input("Enter Ground station longitude: "))
gnd_altitude = float(input("Enter Ground station altitude: "))


# Storing times as usable variables
start = datetime.strptime(start_time_string, "%Y/%m/%d %H:%M:%S")
end = datetime.strptime(end_time_string, "%Y/%m/%d %H:%M:%S")
the_time = start


# Observer
obs = ephem.Observer()
obs.lon = str(longitude)
obs.lat = str(latitude)
obs.elevation = gnd_altitude

# Create array to hold data
sun_data_stored = []

while the_time <= end:
    obs.date = the_time.strftime("%Y/%m/%d %H:%M:%S")
    sun.compute(obs)

    # Distance, Azimuth, and Elevation
    azimuth = math.degrees(sun.az)
    elevation = math.degrees(sun.alt)

    # Store Data
    sun_data_stored.append((the_time.strftime("%H:%M:%S"), latitude,
                            longitude, azimuth, elevation))
    the_time += timedelta(seconds=1)


# Fields/Column headers
fields = ['Time', 'Latitude', 'Longitude', 'Azimuth (degrees)', 'Elevation (degrees)']

# Data in a list of lists
data = [[time, latitude, longitude, azimuth, elevation]
        for time, latitude, longitude, azimuth, elevation
        in sun_data_stored]

# File to write to
df = pd.DataFrame(data, columns=fields)
df.to_csv("solar_position_calculation.csv", index=False)
print("solar_position_calculation.csv file has been created.")
