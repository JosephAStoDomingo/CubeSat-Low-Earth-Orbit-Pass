import pandas as pd
import ephem
import math


# Record user input and assign to variables.
frequency = float(input("Enter frequency (MHz): "))
data_rate = float(input("Enter Data Rate (bps): "))
sat_altitude = float(input("Enter Satellite orbital altitude (km): "))
tx_Antenna_gain = float(input("Enter Tx Antenna Gain (dB): "))
rx_antenna_gain = float(input("Enter Rx Antenna Gain (dB): "))
antenna_temp = float(input("Enter Antenna Temperature (K): "))
rf_input_power = float(input("Enter RF input power (Watts): "))

# Hard Coded Values
tx_Cable_Loss = 1
t_comp = 43
eb_n0_required = 10.5
boltzman = -228.6

# Store Data Rate Conversion
data_rate_db = 10 * math.log(data_rate * 1000, 10)


# FSPL Function
def fspl_function(slt_range, freq):
    speed_light = ephem.c
    fspl_calc = (20 * math.log(slt_range * 1000, 10)
                 + 20 * math.log(freq * 1e6, 10)
                 + 20 * math.log(4 * math.pi / speed_light, 10))
    return fspl_calc


# Watts to decibels function
def watts_to_db(power):
    m_watts = power * 1000  # First convert to milliwatts
    dbm = 10 * math.log(m_watts, 10)
    return dbm


# EIRP Function
def eirp_function(power, c_loss, a_gain):
    power_db = watts_to_db(power)
    eirp_val = power_db - c_loss + a_gain - 30
    return eirp_val


# Calculate and print Effective Isotropic Radiated Power
eirp = eirp_function(rf_input_power, tx_Cable_Loss, tx_Antenna_gain)
print(f'The Effective Isotropic Radiated Power is: '
      f'{eirp} dB.')


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
print(f"The Ratio of Receiver Gain (G/T) is: {g_t_ratio} (dB)")


# Carrier to Density Ratio Function
def noise_density_ratio(e_i_r_p, f_s_p_l, g_t):
    c_no = e_i_r_p - f_s_p_l + g_t + 228.6
    return c_no


# Slant Range function
def slant_range_function(space_alt, delta):
    earth_rad = 6378.14
    delta_rad = math.radians(delta)
    slt_rnge = earth_rad * (math.sqrt((space_alt + earth_rad)
                                      ** 2 / earth_rad ** 2
                                      - math.cos(delta_rad) ** 2)
                                      - math.sin(delta_rad))
    return slt_rnge

# Delta Angles
delta_angles = [90 , 60, 30, 10, 0]

# Create arrays to store fspl and slant range
fspl_array = []
ranges_array = []
cn0_array = []
link_margins_array = []
ebN0_available_array = []

for delta in delta_angles:
    slant_range = slant_range_function(sat_altitude, delta)
    ranges_array.append(slant_range)
    fspl_val = fspl_function(slant_range, frequency)
    fspl_array.append(fspl_val)
    cn0_val = noise_density_ratio(eirp, fspl_val, g_t_ratio)
    cn0_array.append(cn0_val)
    eb_n0_available = cn0_val - data_rate_db
    ebN0_available_array.append(eb_n0_available)
    link_margins = eb_n0_available - eb_n0_required
    link_margins_array.append(link_margins)
    print("---------------------------------------------"
          "------------------------------")
    # Spaces intentional.
    print(f'                        {delta} Degrees: ')
    print(f"The slant range is {slant_range} km at {delta} degrees.")
    print(f"The FSPL value is {fspl_val} db at {delta} degrees.")
    print(f"The carrier to Noise Density Ratio at {delta} degrees is: "
          f"{cn0_val} dB.")
    print(f"The Link Margin at {delta} degrees is: {link_margins} dB")


# Sections, Parameters and units to use for CSV
sections = {
    'Downlink': {
        'Parameters': ['Frequency', 'Data Rate', 'Orbital Altitude'],
        'Units': ['Hz', 'Kbps', 'km']
    },
    'Space Craft Transmit Parameters': {
        'Parameters': ['RF Input Power', 'Tx Cable Loss',
                       'Tx Antenna Gain', 'EIRP'],
        'Units': ['Watts', 'dB', 'dB', 'dBW'],
    },
    'Channel Parameters': {
        'Parameters': ['Free Space Path Loss'],
        'Units': ['dB'],
    },
    'Power Summary': {
        'Parameters': ["Boltzman's Constant", 'C/N0 at Ground Station'],
        'Units': [" ", 'dB/Hz'],
    },
    'Uncoded Offset': {
        'Parameters': ['C/N0', 'Eb/N0', 'Theoretical Eb/N0',
                       'Link Margins'],
        'Units': ['dB', 'dB', 'dB', 'dB']
    }
}

# Storing values capable for csv
orb_alt_csv = sat_altitude


# Create Data Structure
data_structure = []

# Add sections and parameters
for title, content in sections.items():
    # Center Section title to middle column
    total_column = len(delta_angles) + 2
    spacing = (total_column - 1) // 2
    row_title = [' '] * spacing + [title] + [''] * total_column
    data_structure.append(row_title)

    # Use Parameters and Units
    parameters = ['Parameters', 'Units'] + delta_angles
    data_structure.append(parameters)

    # Nested for loop for values
    for param, unit in zip(content['Parameters'], content['Units']):
        if param == 'Frequency':
            values = [frequency] * len(delta_angles)
        elif param == 'Data Rate':
            values = [data_rate] * len(delta_angles)
        elif param == 'Orbital Altitude':
            values = [orb_alt_csv] * len(delta_angles)
        elif param == 'RF Input Power':
            values = [rf_input_power] * len(delta_angles)
        elif param == 'Tx Cable Loss':
            values = [tx_Cable_Loss] * len(delta_angles)
        elif param == 'Tx Antenna Gain':
            values = [tx_Antenna_gain] * len(delta_angles)
        elif param == 'EIRP':
            values = [eirp] * len(delta_angles)
        elif param == 'Free Space Path Loss':
            values = fspl_array
        elif param == "Boltzman's Constant":
            values = [boltzman] * len(delta_angles)
        elif param == 'C/N0 at Ground Station':
            values = cn0_array
        elif param == 'C/N0':
            values = cn0_array
        elif param == 'Eb/N0':
            values = ebN0_available_array
        elif param == 'Theoretical Eb/N0':
            values = [eb_n0_required] * len(delta_angles)
        elif param == 'Link Margins':
            values = link_margins_array
        else:
            values = ['N/A'] * len(delta_angles)

        data_structure.append([param, unit] + values)
    data_structure.append(['' * total_column])

# create data frame
data_frame = pd.DataFrame(data_structure)

csv_file_path = "FinalLinkBudget.csv"
data_frame.to_csv(csv_file_path, index=False, header=False)
print("FinalLinkBudget.csv File has been created.")


