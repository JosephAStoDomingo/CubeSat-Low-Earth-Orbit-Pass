import pandas as pd
import ephem
import math
import csv
from datetime import datetime, timedelta

# ISS TLE
line1 = "ISS (ZARYA)"
line2 = "1 25544U 98067A   24178.50504361  .00017145  00000-0  30960-3 0  9995"
line3 = "2 25544  51.6414 269.1334 0010912  10.2405 100.4092 15.49775035459994"

# Satellite Object
iss = ephem.readtle(line1, line2, line3)

# Hard Coded Values
latitude = '32.6833'
longitude = '-117.2080'
gnd_altitude = '150'
data_rate = 1000
antenna_temp = 290
t_comp = 43
sat_altitude = 510
tx_Antenna_gain = 5.3
rx_antenna_gain = 30.96
eb_n0_required = 10.5
tx_Cable_Loss = 1


# User Input
rf_input_power = float(input("Enter RF input power (Watts): "))
frequency = float(input("Enter frequency (MHz): "))
start_str = input("Enter start time (YYYY/MM/DD HH:MM:SS): ")

# start and end times
start = datetime.strptime(start_str, "%Y/%m/%d %H:%M:%S")

# Observer
obs = ephem.Observer()
obs.lon = str(longitude)
obs.lat = str(latitude)

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


# G/T Ratio of Receiver Gain and System Noise Temperature
def sys_noise_temp(temp_a, temp_comp):
    # Function Calculates System Noise Temperature
    # and converts Kelvin to dB
    return 10 * math.log(temp_a + temp_comp, 10)


def ratio_rec_gain(receiver_gain, sys_temp_db):
    return receiver_gain - sys_temp_db


# Use Functions and store values
total_sys_noise = sys_noise_temp(antenna_temp, t_comp)
g_t_ratio = ratio_rec_gain(rx_antenna_gain, total_sys_noise)


# Carrier to Density Ratio Function
def noise_density_ratio(e_i_r_p, f_s_p_l, g_t):
    c_no = e_i_r_p - f_s_p_l + g_t + 228.6
    return c_no


# Store cN0 and print
cn0 = noise_density_ratio(eirp, fspl, g_t_ratio)

# Calculate Eb / N0
# Convert Data Rate (kbps) to (dB)
data_rate_db = 10 * math.log(data_rate * 1000, 10)

# Calculate and print Eb/N0
eb_n0_available = cn0 - data_rate_db
link_margin = eb_n0_available - eb_n0_required


# Next Pass Info, using next_pass 0 , 2 and 4 for time.
next_pass = obs.next_pass(iss)
tsat_next_rise_horizon = next_pass[0]
tsat_next_peak = next_pass[2]
tsat_next_descend_horizon = next_pass[4]
next_sat_altitude = math.degrees(next_pass[3])
print(f"The next pass will occur from: {tsat_next_rise_horizon}")
print(f"The next pass will be at its highest point at: "
      f"{tsat_next_peak}")
print(f"The next pass will end at: {tsat_next_descend_horizon}")

# Time data
time_data_ascend = ephem.localtime(next_pass[0])
time_data_descend = ephem.localtime(next_pass[4])

# Use these next values to calculate the predicted link margin
# fspl will change due to distance...
next_fspl = fspl_function(distance, frequency)
next_cN0 = noise_density_ratio(eirp, next_fspl, g_t_ratio)
next_eB_n0_ava = next_cN0 - data_rate_db
next_link_margin = next_eB_n0_ava - eb_n0_required
print(f"The next predicted Link Margin is: "
      f"{next_link_margin} (dB)")

fspl_stored = []  # Create array to hold fspl values

while time_data_ascend <= time_data_descend:
    obs.date = ephem.Date(time_data_ascend)
    iss.compute(obs)

    # Distance, Azimuth, and Elevation
    distance = iss.range
    azimuth = math.degrees(iss.az)
    elevation = math.degrees(iss.alt)

    # Calculate FSPL
    fspl = fspl_function(distance, frequency)

    # Calculate EIRP
    eirp = eirp_function(rf_input_power, tx_Cable_Loss, tx_Antenna_gain)

    # Calculate G/T Ratio of Receiver
    total_sys_noise = sys_noise_temp(antenna_temp, t_comp)
    g_t_ratio = ratio_rec_gain(rx_antenna_gain, total_sys_noise)

    cn0 = noise_density_ratio(eirp, fspl, g_t_ratio)
    eb_n0_available = cn0 - data_rate_db
    link_margin = eb_n0_available - eb_n0_required

    # Store Data
    fspl_stored.append((time_data_ascend.strftime("%H:%M:%S"), fspl, azimuth, elevation,
                        rf_input_power, tx_Antenna_gain, data_rate, eirp, link_margin))
    time_data_ascend += timedelta(seconds=1)

# DataFrame for section 1
section_one = [
    ['AOS', tsat_next_rise_horizon, '', ''],
    ['Highest Point Time', tsat_next_peak,
     '', ''],
    ['LOS', tsat_next_descend_horizon, '',
     '']
]

section_one_df = pd.DataFrame(section_one)

# 2nd Data Frame Fields/Column headers
fields = ['Time', 'FSPL (dB)', 'Azimuth (degrees)', 'Elevation (degrees)',
          'RF Input Power (W)', 'Tx Antenna Gain (dBi)', 'Data Rate (Kbps)',
          'EIRP (dB)', 'Link Margin']
second_data_frame = pd.DataFrame(fspl_stored, columns=fields)

# File to write to
with open('LinkBudget.csv', mode='w', newline='') as file:
    writer = csv.writer(file)

    # section 1
    writer.writerow(['Next Pass'])
    writer.writerows(section_one)

    # New line for separation
    file.write('\n')

    # section 2
    writer.writerow(['', '', '', '', 'Next Pass Link Budget'])
    writer.writerow(fields)
    writer.writerows(second_data_frame.values.tolist())
print("LinkBudget.csv file has been created.")
