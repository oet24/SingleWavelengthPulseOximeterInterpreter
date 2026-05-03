# oet24 amc272
# Oximeter Program

from numpy import fft
import numpy as np
import math
import matplotlib.pyplot as plt

class Signal:
    def __init__(self):
        self.signal = []
        self.AddSignal()      
        self.readings = len(self.signal)
        self.duration = self.signal[self.readings-1][0]
        self.dt = self.duration/self.readings
        self.sampleFreq = 1/self.dt
        self.fundamentalFreq = self.sampleFreq/self.readings
        self.RemoveDCDrift()
        self.spectrum = []

    def RemoveDCDrift(self):
        sum = 0
        for i in self.GetSignal():
            sum += i
        mean = sum/self.GetReadings()
        newSignal = []
        for i in self.GetSignal():
            newSignal.append(i - mean)
        self.SetSignal(newSignal)     

    def AddSignal(self):
        with open("signal.txt", "r") as f:
            content = f.readlines()
        for line in content:
            if line.strip(): 
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    time = float(parts[0])
                    value = float(parts[1])
                    self.signal.append([time, value])
        f.close()      

    def GetSignal(self):
        signalValues = []
        for reading in self.signal:
            signalValues.append(reading[1])
        return signalValues

    def GetTimes(self):
        timeValues = []
        for reading in self.signal:
            timeValues.append(reading[0])
        return timeValues
    
    def GetReadings(self):
        return self.readings
    
    def GetSampleFreq(self):
        return self.sampleFreq
    
    def GetDuration(self):
        return self.duration
    
    def GetDivisions(self):
        return self.dt
    
    def GetFundFreq(self):
        return self.fundamentalFreq

    def SetSignal(self, newSignal):
        for reading in range(self.readings-1):
            self.signal[reading][1] = newSignal[reading]
       
    def SetSpectrum(self, spectrum):
        self.spectrum = spectrum

    def GetSpectrum(self):
        return self.spectrum


class SignalProcessor:
    def __init__(self, movAvgFactor, upperCutoff, lowerCutoff):
        self.movAvgFactor = movAvgFactor
        self.upperCutoff = upperCutoff
        self.lowerCutoff = lowerCutoff

    def MovingAverage(self, signal, length):
        for i in range(self.movAvgFactor):
            signal.append(signal[length-1])
        for reading in range(length):
            sum = 0
            for i in range(self.movAvgFactor):
                sum += signal[reading+i]
            signal[reading] = sum/self.movAvgFactor
        return signal
        

    def BandPass(self, signal,readings,fs):
        fftResult, freqs = self.FFT(signal, fs, readings)
        fftResult[freqs < self.lowerCutoff] = 0
        fftResult[freqs > self.upperCutoff] = 0
        filteredSignal = self.IFFT(fftResult, readings)
        return filteredSignal

    def FFT(self, signal, fs, readings):
        fftResult = fft.rfft(signal)
        freqs = fft.rfftfreq(readings, 1/fs)
        return fftResult, freqs
    
    def IFFT(self, fftResult, readings):
        reconstructedSignal = fft.irfft(fftResult, n=readings)
        return reconstructedSignal


class SignalAnalysis:
    def __init__(self, filter, signal):
        self.filter = filter
        self.signal = signal
        self.CalculateSpectrum()
        self.output = SignalResult()

    def CleanSignal(self):
        self.signal.SetSignal(self.filter.MovingAverage(self.signal.GetSignal(), self.signal.GetReadings()))

    def FilterSignal(self):
        self.signal.SetSignal(self.filter.BandPass(self.signal.GetSignal(),self.signal.GetReadings(), self.signal.GetSampleFreq()))

    def CalculateSpectrum(self):
        self.signal.SetSpectrum(self.filter.FFT(self.signal.GetSignal(), self.signal.GetSampleFreq(), self.signal.GetReadings()))

    def Plot(self):  
        self.output.PlotSignal(self.signal.GetTimes(), self.signal.GetSignal())
        self.CleanSignal()
        self.FilterSignal()
        self.output.PlotSignal(self.signal.GetTimes(), self.signal.GetSignal()) 
        self.output.PlotSpectrum(self.signal.GetSpectrum()[0], self.signal.GetSpectrum()[1])
    
    def GetBPM(self):
        fftResult, freqs = self.filter.FFT(self.signal.GetSignal(), self.signal.GetSampleFreq(), self.signal.GetReadings())
        peak = max(fftResult)
        BPM = 0
        i = 1
        for result in fftResult:
            if result == peak:
                BPM = i
                print(BPM)
            else:
                i += 1
        BPM = freqs[BPM] * 60
        return BPM
    
    def Results(self):
        self.output.OutputSignalInfo(self.GetBPM(), self.signal)



class SignalResult():
    def __init__(self):
        pass

    def PlotSpectrum(self, spectrum, freqs):
        plt.show()
        plt.plot(freqs, np.abs(spectrum))
        plt.xlim(0,4)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        

    def PlotSignal(self, time, signal):
        plt.show()
        plt.plot(time, signal)
        plt.xlabel('Time (s)')      
        plt.ylabel('Signal (V)')

    def OutputSignalInfo(self, BPM, signal):
        print("The patient has a heart rate of:", str(round(BPM)), "beats per minute (BPM)")
        print("The input signal had the following characteristics:")
        print("Duration:", str(signal.GetDuration()), " s")
        print("Sampling Frequency:", str(round(signal.GetSampleFreq(), 4)), " hz")
        print("Fundamental Frequency:", str(round(signal.GetFundFreq(), 4)), " hz")
        print("Time divisons", str(round(signal.GetDivisions(), 6)), " s")
        print("Readings:", str(signal.GetReadings()))
    


Filter = SignalProcessor(20, 3.5, 0.5)
signal = Signal()
Analysis = SignalAnalysis(Filter, signal)

Analysis.Plot()
Analysis.Results()
