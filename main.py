import wave
from struct import unpack
import numpy as np
import pyaudio
import sys
import serial
import time


ser = serial.Serial(
            port='/dev/ttyACM0',
            baudrate=9600,
        )


matrix    = [0,0,0]
weighting = [1,64,64]

def list_devices():
    # List all audio input devices
    p = pyaudio.PyAudio()
    i = 0
    n = p.get_device_count()
    while i < n:
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
           print(str(i)+'. '+dev['name'])
        i += 1

# Audio setup
no_channels = 1
sample_rate = 44100

# Chunk must be a multiple of 8
# NOTE: If chunk size is too small the program will crash
# with error message: [Errno Input overflowed]
chunk = 3200

list_devices()
# Use results from list_devices() to determine your microphone index
device = 1

p = pyaudio.PyAudio()
stream = p.open(format = pyaudio.paInt16,
                channels = no_channels,
                rate = sample_rate,
                input = True,
                frames_per_buffer = chunk,
                input_device_index = device)


# Return power array index corresponding to a particular frequency
def piff(val):
    return int(2*chunk*val/sample_rate)
   
def calculate_levels(data, chunk,sample_rate):
    global matrix
    # Convert raw data (ASCII string) to numpy array
    data = unpack("%dh"%(len(data)/2),data)
    data = np.array(data, dtype='h')
    # Apply FFT - real data
    fourier=np.fft.rfft(data)
    # Remove last element in array to make it the same size as chunk
    fourier=np.delete(fourier,len(fourier)-1)
    # Find average 'amplitude' for specific frequency ranges in Hz
    power = np.abs(fourier)   
    matrix[0]= int(np.mean(power[piff(0)    :piff(100):1]))
    matrix[1]= int(np.mean(power[piff(100)  :piff(2000):1]))
    matrix[2]= int(np.mean(power[piff(2000)  :piff(16000):1]))
    # Tidy up column values for the LED matrix
    matrix=np.divide(np.multiply(matrix,weighting),1000000)
    # Set floor at 0 and ceiling at 8 for LED matrix
    matrix=matrix.clip(0,8)
    #(matrix)
    return matrix

# Main loop
#plt.ion()
while 1:
    try:
        # Get microphone data
        data = stream.read(chunk, exception_on_overflow=False)
        matrix=calculate_levels(data, chunk,sample_rate)
        message = "A{}B{}\n".format(int(matrix[0]/8*38+8),int(matrix[2]/8*38+8))
        print(message)
        ser.write(message.encode())
        #plt.plot(matrix)
        #plt.axis([0,4,0,8])
        #plt.draw()
        #plt.pause(0.0001)
        #plt.clf()
        time.sleep(0.05)
    except KeyboardInterrupt:
        print("Ctrl-C Terminating...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        sys.exit(1)
    except Exception as e:
        print(e)
        print("ERROR Terminating...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        sys.exit(1)


