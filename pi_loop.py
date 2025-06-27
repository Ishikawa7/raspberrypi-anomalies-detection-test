import time
from gpiozero import LED
import sys
sys.path.append('~/Freenove_Kit/Libs/Python-Libs/ADCDevice-1.0.3')
from ADCDevice import *
import numpy as np
from sklearn.neighbors import LocalOutlierFactor, KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
import pickle

# load the models with pickle
with open('knn_model.pkl', 'rb') as f:
    knn = pickle.load(f)
with open('clf_model.pkl', 'rb') as f:
    clf = pickle.load(f)
with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

adc = ADCDevice() # Define an ADCDevice class object
blue_led = LED(17)
green_led = LED(27)
red_led = LED(26)

def setup():
    global adc
    if(adc.detectI2C(0x48)): # Detect the pcf8591.
        adc = PCF8591()
    elif(adc.detectI2C(0x4b)): # Detect the ads7830
        adc = ADS7830()
    else:
        print("No correct I2C address found, \n"
        "Please use command 'i2cdetect -y 1' to check the I2C address! \n"
        "Program Exit. \n");
        exit(-1)
        
def extract_features(signal):
    mean = np.mean(signal)
    std = np.std(signal)
    fourier_coeffs = np.fft.fft(signal)[:len(signal)//2]
    return [mean, std] + list(fourier_coeffs)

def to_float_array(data):
    result = []
    for x in data:
        if np.iscomplexobj(x):
            result.append(x.real)
            result.append(x.imag)
        else:
            result.append(float(x))
    return np.array(result, dtype=np.float64)

def loop():
    buffer = [177] * 10
    last_anomaly = 0
    while True:
        value = adc.analogRead(7)    # read the ADC value of channel 7
        buffer.pop(0)
        buffer.append(value)
        features = to_float_array(extract_features(buffer))
        scaled_features = scaler.transform([features])
        knn_prediction = knn.predict(scaled_features)
        clf_prediction = clf.predict(scaled_features)
        if knn_prediction[0] == -1 and last_anomaly == -1:
            blue_led.off()
            green_led.off()
            red_led.on()
        else:
            red_led.off()
            if clf_prediction[0] == 0:
                blue_led.off()
                green_led.on()
            else:
                blue_led.on()
                green_led.off()
        last_anomaly = knn_prediction[0]
        time.sleep(0.1)

def destroy():
    adc.close()
    
if __name__ == '__main__':   # Program entrance
    print ('Program is starting ... ')
    try:
        setup()
        loop()
    except KeyboardInterrupt: # Press ctrl-c to end the program.
        destroy()
        print("Ending program")
        
