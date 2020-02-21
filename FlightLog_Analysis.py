import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft
import peakutils 

logFile = open("flight_log.txt","r", encoding = "ISO-8859-1")

SECTOR_SIZE             = 512

START_INDICATOR = ord('C')
END_INDICATOR = ord('K')

GYRO_SCALE = 1.0/16.4

# empty arrays to append new bytes to end.
gyroRawResults_Roll         = []
gyroFilteredResults_Roll    = []

gyroRawResults_Pitch        = []
gyroFilteredResults_Pitch   = []

gyroRawResults_Yaw          = []
gyroFilteredResults_Yaw     = []

altHold_throttle            = []

rcData_roll                 = []
rcData_pitch                = []
rcData_yaw                  = []
rcData_throttle             = []

motor_final1                = []
motor_final2                = []
motor_final3                = []
motor_final4                = []

imuAngle_roll               = []
imuAngle_pitch              = []
imuAngle_yaw                = []

loop_cycle                  = []

flags                       = []

timeArray                   = []

currentTime = 0

sector_counter = 0

def FindPeak_Frequency(peaks):
    
    # This method finds the frequency of the peaks.
    # Peak returns the array location where peaks occur.
    # To find the peak_freq, these locations in the timeArray is needed.
    # Difference between two timeArray result will show the period of the peak. 
    
    freq_array = []
    freqArray_index = 0
    size = len(peaks)
    
    for i in range(size - 1):
        
        if(i < size - 2):
            
            peak1 = timeArray[peaks[i]]
            peak2  = timeArray[peaks[i+1]]
            
            period = peak2 - peak1
            freq = 1 / period
            freq_array.append(freq) 
            freqArray_index += 1
    
    return freq_array, len(freq_array)
    


def FFT_Calculate(array, SAMPLE_PERIOD):
        
    # Calculate fft of array    
    rawFFT = fft(array)
    
    # Number of samples
    N = len(array) 
     
    # Freq values array from 0 to 4000KHz
    freq = np.linspace(0.0, (1.0 / (2.0 * SAMPLE_PERIOD)), N / 2)
    
    finalFFT = (2.0 / N) * np.abs(rawFFT[0:int(N/2)])
    
    peakIndexes = peakutils.indexes(finalFFT, 0.025, min_dist = 50, thres_abs=True)
    
    return freq, finalFFT, peakIndexes


# First sector is used to store information necessary to read file correctly
# such as how many sector are written etc.
def Read_InfoSector():
    
    currentBytes = logFile.read(SECTOR_SIZE)
    
    if(currentBytes[0] == 'C' and currentBytes[1] == 'K'):
        if(currentBytes[9] == '4' and currentBytes[11] == '7'):
        
            current1 = (np.uint8)(ord(currentBytes[16]))
            current2 = (np.uint8)(ord(currentBytes[17]))
            current3 = (np.uint8)(ord(currentBytes[18]))        
            current4 = (np.uint8)(ord(currentBytes[19]))
            
            total_sectors = (np.uint32)((current1 << 24) | (current2 << 16) | (current3 << 8) | (current4)) 
            
            current1 = (np.uint8)(ord(currentBytes[32]))
            current2 = (np.uint8)(ord(currentBytes[33]))
            
            main_loop_time = (np.uint16)(current1 << 8 | current2)
            
            return total_sectors, main_loop_time  



(NUMBER_OF_SECTORS, FLIGHT_CONTROLLER_LOOP_TIME) = Read_InfoSector()


SAMPLE_PERIOD = (FLIGHT_CONTROLLER_LOOP_TIME * 0.000001)
SAMPLE_FREQUENCY = 1 / SAMPLE_PERIOD  
TIME_INCREMENT = SAMPLE_PERIOD

print("Started Reading")
#print("Wait It might take upto %d sec") % (NUMBER_OF_SECTORS/500) # flight controller log freq. is 500

while (True):    
    
    # current sector
    sector_counter += 1

    if(sector_counter == NUMBER_OF_SECTORS):
        sector_counter = 0
        break # finish while loop
    
    currentBytes = logFile.read(SECTOR_SIZE)   # read SECTOR_SIZE amount of bytes from .txt file
    
    # current byte of the sector
    byte_index = 0
    while(byte_index < SECTOR_SIZE):
        
        res = ord(currentBytes[byte_index])        # ord converts ascii to int    
        
        # if 1st is start byte start decoding
        if (res == START_INDICATOR):
            
            res = ord(currentBytes[byte_index+31])
            
            # if 32th is end byte start decoding
            if (res == END_INDICATOR):
                
                # Gyro raw and filtered results.
                for axis in range(3):
                    
                    byte_index += 1
                    gyroRaw_MSB = (np.uint8)(ord(currentBytes[byte_index]))
                    byte_index += 1
                    gyroRaw_LSB = (np.uint8)(ord(currentBytes[byte_index]))
                    
                    gyroRaw = (np.int16)(gyroRaw_MSB << 8 | gyroRaw_LSB)
                    gyroRaw *= GYRO_SCALE
                    
                    if(axis == 0):
                        gyroRawResults_Roll.append(gyroRaw) # add new data to array
                    elif(axis == 1):
                        gyroRawResults_Pitch.append(gyroRaw)
                    elif(axis == 2):
                        gyroRawResults_Yaw.append(gyroRaw)                     
                    
                    byte_index += 1
                    gyroFiltered_MSB = (np.uint8)(ord(currentBytes[byte_index]))
                    byte_index += 1
                    gyroFiltered_LSB = (np.uint8)(ord(currentBytes[byte_index]))
                    
                    gyroFiltered = (np.int16)(gyroFiltered_MSB << 8 | gyroFiltered_LSB)
                    
                    if(axis == 0):
                        gyroFilteredResults_Roll.append(gyroFiltered) # add new data to array
                    elif(axis == 1):
                        gyroFilteredResults_Pitch.append(gyroFiltered)
                    elif(axis == 2):
                        gyroFilteredResults_Yaw.append(gyroFiltered)


                # Altitude hold adjustment result
                byte_index += 1
                altHold_thr = (np.uint8)(ord(currentBytes[byte_index]))
                altHold_throttle.append(altHold_thr * 10)
                
                # Roll, pitch, yaw, throttle rc data
                for axis in range(4):
                    byte_index += 1
                    rcData = (np.uint8)(ord(currentBytes[byte_index]))
                    
                    if(axis == 0):
                        rcData_roll.append(rcData * 10)
                    elif(axis == 1):
                        rcData_pitch.append(rcData * 10)
                    elif(axis == 2):
                        rcData_yaw.append(rcData * 10)
                    elif(axis == 3):
                        rcData_throttle.append(rcData * 10)
                        
                
                # Motor final results
                for esc in range(4):
                    byte_index += 1
                    motorfinal = (np.uint8)(ord(currentBytes[byte_index]))
                    
                    if(esc == 0):
                        motor_final1.append(motorfinal * 10)
                    elif(esc == 1):
                        motor_final2.append(motorfinal * 10)
                    elif(esc == 2):
                        motor_final3.append(motorfinal * 10)
                    elif(esc == 3):
                        motor_final4.append(motorfinal * 10)
                    
                # IMU angles
                for axis in range(3):
                    byte_index += 1
                    imu = (np.uint8)(ord(currentBytes[byte_index]))
                    
                    if(axis == 0):
                        imuAngle_roll.append(imu)
                    elif(axis == 1):
                        imuAngle_pitch.append(imu)
                    elif(axis == 2):
                        imuAngle_yaw.append(imu * 2)



                # Loop cycle time
                byte_index += 1
                loopCycle_MSB = (np.uint8)(ord(currentBytes[byte_index]))
                byte_index += 1
                loopCycle_LSB = (np.uint8)(ord(currentBytes[byte_index]))
                loopCycle = (np.int16)(loopCycle_MSB << 8 | loopCycle_LSB)
                loop_cycle.append(loopCycle)
                
                # 2 bytes for flags later decode it
                byte_index += 1
                flags_MSB = (np.uint8)(ord(currentBytes[byte_index]))
                byte_index += 1
                flags_LSB = (np.uint8)(ord(currentBytes[byte_index]))
                flags_bits = (np.int16)(flags_MSB << 8 | flags_LSB)
                flags.append(flags_bits)                
                
                # 2 bytes available for later logging and last byte is end byte
                byte_index += 3       

                currentTime += TIME_INCREMENT
                timeArray.append(currentTime)
                
        else:
            byte_index += 1
    
        
print("End of Reading")
 

######## PLOT ROLL ########

fig = plt.figure(figsize=(8, 6))

fig.add_subplot(2,1,1) # num of row, num of column, plot num nth

plt.title('Gyro Roll Raw/Filtered')
plt.xlabel('Time (Second)')
plt.ylabel('Roll (Degrees)')

plt.grid()

plt.plot(timeArray, gyroRawResults_Roll, 'r')
plt.plot(timeArray, gyroFilteredResults_Roll, 'c')


###########################

ax = fig.add_subplot(2,1,2)

plt.title('Gyro Roll Raw/Filtered FFT')
plt.xlabel('Frequency')
plt.ylabel('Amplitude')

# Calculate and Plot FFT
freq_raw, finalFFT_Raw, peaksFFT_Raw = FFT_Calculate(gyroRawResults_Roll, SAMPLE_PERIOD)

freq_filtered, finalFFT_Filtered, peaksFFT_Filtered = FFT_Calculate(gyroFilteredResults_Roll, SAMPLE_PERIOD)

plt.ylim(0, 0.25)    # limit y axis between var1 and var2

ax.set_xticks(np.arange(0, 4000, 500))              # put major lines at every 500th from 0 to 4000
ax.set_xticks(np.arange(0, 4000, 50), minor=True)   # put minor lines at every 50th from 0 to 4000

ax.grid(which='minor')                      # Add minor lines to grid 
ax.grid(which='major', linestyle = '--')    # Add major lines to grid
 
plt.plot(freq_raw,      finalFFT_Raw,      'r')
plt.plot(freq_filtered, finalFFT_Filtered, 'c+')

# Show at which frequencies there was a peak
raw_peak_frequencies = (np.int16)(freq_raw[peaksFFT_Raw])
filtered_peak_frequencies = (np.int16)(freq_filtered[peaksFFT_Filtered])

# Put dots on the peak freq points
for i in range(len(raw_peak_frequencies)):
    plt.plot(raw_peak_frequencies[i], 0.2, 'r*')

# Put dots on the peak freq points
for i in range(len(filtered_peak_frequencies)):
    plt.plot(filtered_peak_frequencies[i], 0.2, 'c*')
    
plt.text(2000, 0.25, raw_peak_frequencies, bbox=dict(facecolor='red', alpha=0.5))
plt.text(2000, 0.10, filtered_peak_frequencies, bbox=dict(facecolor='cyan', alpha=0.5))

######## PLOT PITCH ########

fig = plt.figure(figsize=(8, 6))

fig.add_subplot(2,1,1) # num of row, num of column, plot num nth

plt.title('Gyro Pitch Raw/Filtered')
plt.xlabel('Time (Second)')
plt.ylabel('Pitch (Degrees)')
plt.grid()

plt.plot(timeArray, gyroRawResults_Pitch, 'r')
plt.plot(timeArray, gyroFilteredResults_Pitch, 'c')


############################

ax = fig.add_subplot(2,1,2)

plt.title('Gyro Pitch Raw/Filtered FFT')
plt.xlabel('Frequency')
plt.ylabel('Amplitude')

# Calculate and Plot FFT
freq_raw, finalFFT_Raw, peaksFFT_Raw = FFT_Calculate(gyroRawResults_Pitch, SAMPLE_PERIOD)

freq_filtered, finalFFT_Filtered, peaksFFT_Filtered = FFT_Calculate(gyroFilteredResults_Pitch, SAMPLE_PERIOD)

plt.ylim(0, 0.25)    # limit y axis between var1 and var2

ax.set_xticks(np.arange(0, 4000, 500))              # put major lines at every 500th from 0 to 4000
ax.set_xticks(np.arange(0, 4000, 50), minor=True)   # put minor lines at every 50th from 0 to 4000

ax.grid(which='minor')                      # Add minor lines to grid 
ax.grid(which='major', linestyle = '--')    # Add major lines to grid
 
plt.plot(freq_raw,      finalFFT_Raw,      'r')
plt.plot(freq_filtered, finalFFT_Filtered, 'c+')

# Show at which frequencies there was a peak
raw_peak_frequencies = (np.int16)(freq_raw[peaksFFT_Raw])
filtered_peak_frequencies = (np.int16)(freq_filtered[peaksFFT_Filtered])

# Put dots on the peak freq points
for i in range(len(raw_peak_frequencies)):
    plt.plot(raw_peak_frequencies[i], 0.2, 'r*')

# Put dots on the peak freq points
for i in range(len(filtered_peak_frequencies)):
    plt.plot(filtered_peak_frequencies[i], 0.2, 'c*')
    
plt.text(2000, 0.25, raw_peak_frequencies, bbox=dict(facecolor='red', alpha=0.5))
plt.text(2000, 0.10, filtered_peak_frequencies, bbox=dict(facecolor='cyan', alpha=0.5))


######## PLOT YAW ########

fig = plt.figure(figsize=(8, 6))

fig.add_subplot(2,1,1) # num of row, num of column, plot num nth

plt.title('Gyro Yaw Raw/Filtered')
plt.xlabel('Time (Second)')
plt.ylabel('Yaw (Degrees)')
plt.grid()

plt.plot(timeArray, gyroRawResults_Yaw, 'r')
plt.plot(timeArray, gyroFilteredResults_Yaw, 'c')


##########################

ax = fig.add_subplot(2,1,2)

plt.title('Gyro Yaw Raw/Filtered FFT')
plt.xlabel('Frequency')
plt.ylabel('Amplitude')

# Calculate and Plot FFT
freq_raw, finalFFT_Raw, peaksFFT_Raw = FFT_Calculate(gyroRawResults_Yaw, SAMPLE_PERIOD)

freq_filtered, finalFFT_Filtered, peaksFFT_Filtered = FFT_Calculate(gyroFilteredResults_Yaw, SAMPLE_PERIOD)

plt.ylim(0, 0.25)    # limit y axis between var1 and var2

ax.set_xticks(np.arange(0, 4000, 500))              # put major lines at every 500th from 0 to 4000
ax.set_xticks(np.arange(0, 4000, 50), minor=True)   # put minor lines at every 50th from 0 to 4000

ax.grid(which='minor')                      # Add minor lines to grid 
ax.grid(which='major', linestyle = '--')    # Add major lines to grid
 
plt.plot(freq_raw,      finalFFT_Raw,      'r')
plt.plot(freq_filtered, finalFFT_Filtered, 'c+')

# Show at which frequencies there was a peak
raw_peak_frequencies = (np.int16)(freq_raw[peaksFFT_Raw])
filtered_peak_frequencies = (np.int16)(freq_filtered[peaksFFT_Filtered])

# Put dots on the peak freq points
for i in range(len(raw_peak_frequencies)):
    plt.plot(raw_peak_frequencies[i], 0.2, 'r*')

# Put dots on the peak freq points
for i in range(len(filtered_peak_frequencies)):
    plt.plot(filtered_peak_frequencies[i], 0.2, 'c*')
    
plt.text(2000, 0.25, raw_peak_frequencies, bbox=dict(facecolor='red', alpha=0.5))
plt.text(2000, 0.10, filtered_peak_frequencies, bbox=dict(facecolor='cyan', alpha=0.5))


######## IMU ROLL ########

fig = plt.figure(figsize=(8, 6))

fig.add_subplot(3,1,1) # num of row, num of column, plot num nth

plt.title('IMU Roll')
plt.xlabel('Time (Second)')
plt.ylabel('IMU Roll')
plt.ylim(-180, 180)    # limit y axis between var1 and var2
plt.grid()

plt.plot(timeArray, imuAngle_roll, 'c')

fig.add_subplot(3,1,2) # num of row, num of column, plot num nth

plt.xlabel('Time (Second)')
plt.ylabel('IMU Pitch')
plt.ylim(-180, 180)    # limit y axis between var1 and var2
plt.grid()

plt.plot(timeArray, imuAngle_pitch, 'c')

fig.add_subplot(3,1,3) # num of row, num of column, plot num nth

plt.xlabel('Time (Second)')
plt.ylabel('IMU Yaw')
plt.ylim(0, 360)    # limit y axis between var1 and var2
plt.grid()

plt.plot(timeArray, imuAngle_yaw, 'c')

############## LOOP CYCLE ####################

fig = plt.figure(figsize=(8, 6))

fig.add_subplot(2,1,1) # num of row, num of column, plot num nth

plt.xlabel('Time (Second)')
plt.ylabel('Loop Time')

# Set maximum y limit to the 2 time of the loop period in microsec.
yMax = (np.uint8)(TIME_INCREMENT * 1000000)
plt.ylim(0, yMax*2)# limit y axis between var1 and var2
plt.grid()  

plt.plot(timeArray, loop_cycle, 'c')


fig.add_subplot(2,1,2) # num of row, num of column, plot num nth

plt.xlabel('Time (Second)')
plt.ylabel('Frequency')  
plt.grid()  

loopCyclePeaks = peakutils.indexes(loop_cycle, 140, min_dist = 0.0001, thres_abs=True)
freq_results, results_length = FindPeak_Frequency(loopCyclePeaks)

plt.plot(timeArray[0:results_length], freq_results[0:results_length], 'c')

averageDelayFreq = 0
for i in range(len(freq_results)):
    averageDelayFreq += freq_results[i]

averageDelayFreq /= len(freq_results)

plt.text(1.5, 870, 'Main Delay Freq at:', bbox=dict(facecolor = 'cyan', alpha=0.5))
plt.text(1.5, 800, averageDelayFreq, bbox=dict(facecolor = 'cyan', alpha=0.5))


###########################



plt.show()

  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  




