# The purpose of this program is to simulate a Cubesat Low
# Earth Orbit Pass. It will accomplish the following:
# 1. Receive user input(power, altitudes, frequencies)
# 2. Utilize astrodynamics python libraries.
# 3. Calculate LinkBudgets
# 4. Store LinkBudgets onto CSV files.
import pandas as pd
import ephem
import math
from datetime import datetime, timedelta

# ISS TLE
line1 = "ISS (ZARYA)"
line2 = "1 25544U 98067A   24178.50504361  .00017145  00000-0  30960-3 0  9995"
line3 = "2 25544  51.6414 269.1334 0010912  10.2405 100.4092 15.49775035459994"

# Satellite Object
iss = ephem.readtle(line1, line2, line3)

# Record user input and assign to variables.
rf_input_power = float(input("Enter RF input power (Watts): "))
frequency = float(input("Enter frequency (MHz): "))
sat_altitude = float(input("Enter Satellite orbital altitude (km): "))
latitude = float(input("Enter latitude: "))
longitude = float(input("Enter longitude: "))
gnd_altitude = float(input("Enter Ground station altitude: "))
tx_Antenna_gain = float(input("Enter Tx Antenna Gain (dB): "))
tx_Cable_Loss = float(input("Enter Tx Cable Loss (dB): "))
data_rate = float(input("Enter Data Rate (kbps): "))

# Get user input
start_str = input("Enter start time (YYYY/MM/DD HH:MM:SS): ")
end_str = input("Enter end time (YYYY/MM/DD HH:MM:SS): ")

# start and end times
start = datetime.strptime(start_str, "%Y/%m/%d %H:%M:%S")
end = datetime.strptime(end_str, "%Y/%m/%d %H:%M:%S")
current_time = start

# Observer
obs = ephem.Observer()
obs.lon = str(longitude)
obs.lat = str(latitude)
obs.elevation = gnd_altitude

# Compute position of the ISS w/ respect to Observer
iss.compute(obs)
distance = iss.range


# FSPL Function
def fspl_function(dist, freq):
    speed_light = ephem.c
    fspl_calc = (20 * math.log(dist, 10)
                 + 20 * math.log(freq * 1e6, 10)
                 + 20 * math.log(4 * math.pi / speed_light, 10))
    return fspl_calc


# Calculate and print FSPL
fspl = fspl_function(distance, frequency)
print(f'The Free-Space Path Loss is: {fspl} dB.')


# Watts to decibels function
def watts_to_db(power):
    m_watts = power * 1000  # First convert to milliwatts
    dbm = 10 * math.log(m_watts, 10)
    return dbm


# EIRP Function
def eirp_function(power, c_loss, a_gain):
    power_db = watts_to_db(power)
    eirp_val = power_db - c_loss + a_gain
    return eirp_val


# Calculate and print Effective Isotropic Radiated Power
eirp = eirp_function(rf_input_power, tx_Cable_Loss, tx_Antenna_gain)
print(f'The Effective Isotropic Radiated Power is: '
      f'{eirp} dB.')

# Create array to hold fspl values
fspl_stored = []

while current_time <= end:
    obs.date = current_time.strftime("%Y/%m/%d %H:%M:%S")
    iss.compute(obs)

    # Distance, Azimuth, and Elevation
    distance = iss.range
    azimuth = math.degrees(iss.az)
    elevation = math.degrees(iss.alt)

    # Calculate FSPL
    fspl = fspl_function(distance, frequency)

    # Calculate EIRP
    eirp = eirp_function(rf_input_power, tx_Cable_Loss, tx_Antenna_gain)

    # Store Data
    fspl_stored.append((current_time.strftime("%H:%M:%S"), fspl, azimuth, elevation,
                        rf_input_power, tx_Antenna_gain, tx_Cable_Loss, data_rate,
                        eirp))
    current_time += timedelta(seconds=1)

# Fields/Column headers
fields = ['Time', 'FSPL (dB)', 'Azimuth (degrees)', 'Elevation (degrees)',
          'RF Input Power (W)', 'Tx Antenna Gain (dBi)', 'Tx Cable Loss (dB)',
          'Data Rate (Kbps)', 'EIRP (dB)']

# Data in a list of lists
data = [[time, fspl, azimuth, elevation, rf_input_power, tx_Antenna_gain,
        tx_Cable_Loss, data_rate, eirp] for time, fspl, azimuth, elevation,
        rf_input_power, tx_Antenna_gain, tx_Cable_Loss, data_rate, eirp in
        fspl_stored]

# File to write to
df = pd.DataFrame(data, columns=fields)
df.to_csv("LinkBudget.csv", index=False)
print("LinkBudget.csv file has been created.")
