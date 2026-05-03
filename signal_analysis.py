# oet24 amc272
# Oximeter Program

class Signal:
    def __init__(self):
        self.signal = []
        self.AddSignal()
        self.readings = len(self.signal)
        self.duration = self.signal[self.readings-1][0]
        self.dt = self.duration/self.readings
        self.sampleFreq = 1/self.dt
        self.fundamentalFreq = self.sampleFreq/self.readings
        
        #self.ogSignal =
        #self.spectrum =
        #self.ogSpectrum = 

    def RemoveDCDrift(self):
        pass

    def AddSignal(self):
        pass

    def GetSignal(self):
        pass

    def GetTimes(self):
        pass
    
    def GetReadings(self):
        pass
    
    def GetSampleFreq(self):
        pass

    def SetSpectrum(self):
        pass


class SignalProcessor:
    def __init__(self, movAvgFactor, upperCutoff, lowerCutoff):
        self.movAvgFactor = movAvgFactor
        self.upperCutoff = upperCutoff
        self.lowerCutoff = lowerCutoff

    def MovingAverage(self, signal, length):
        paddedSignal = signal.copy()

        for i in range(self.movAvgFactor):
            paddedSignal.append(signal[length - 1])

        smoothedSignal = []

        for reading in range(length):
            total = 0

            for i in range(self.movAvgFactor):
                total += paddedSignal[reading + i]

            smoothedSignal.append(total / self.movAvgFactor)

        return smoothedSignal

    def BandPass(self, signal, readings, fs):
        fft_result, freqs = self.FFT(signal, fs, readings)

        fft_result[freqs < self.lowerCutoff] = 0
        fft_result[freqs > self.upperCutoff] = 0

        filteredSignal = self.IFFT(signal, fft_result, readings)

        return filteredSignal

    def FFT(self, signal, fs, readings):
        fft_result = fft.rfft(signal)
        freqs = fft.rfftfreq(readings, 1 / fs)

        return fft_result, freqs
   
    def IFFT(self, signal, fft_result, readings):
        reconstructedSignal = fft.irfft(fft_result, n=readings)

        return reconstructedSignal


class SignalAnalysis:
    def __init__(self, filter, signal, output):
        self.filter = filter
        self.signal = signal
        self.output = output

    def CleanSignal(self):
        pass

    def FilterSignal(self):
        pass

    def CalculateSpectrum(self):
        pass

    def GetBPM(self):
        pass


class SignalResult:
    def __init__(self):
        pass

    def PlotSpectrum(self):
        pass

    def PlotSignal(self):
        pass

    def OutputSignalInfo(self):
        pass

    def OutputBPM(self):
        pass


Filter = SignalProcessor(5, 3.5, 0.5)
signal = Signal()
Output =  SignalResult(signal)
Analysis = SignalAnalysis(Filter, signal, Output)



