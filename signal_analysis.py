# oet24 amc272
# Oximeter Program

# Libraries
from numpy import fft
import numpy as np
import matplotlib.pyplot as plt

print("THIS SOFTWARE IS NOT MEDICALLY ACCURATE")
print("Do not base health decisions on the output of this program, seek help from a medical professional")

# Configurable options

SIGNAL_FILENAME = "signal.txt"
BANDPASS_UPPER = 4
BANDPASS_LOWER = 0.5
MOVING_AVERAGE_FACTOR = 10

# Class Definitions

class Signal:
    def __init__(self, signalFileName=None, signalData=None):
        """
        Retrieves oximeter data from text file or stores provided signal data.
        Holds one version of a signal and stores useful information about it.

        Args:
            signalFileName (string) location of the signal textfile
            signalData (List[float, float]) Holds a signal in [time, signal] format

        Attributes:
            signal (List[float, float]) Holds the signal in [time, signal] format
            readings (int) Contains the amount of signal readings collected from the textfile
            duration (float) Contains the duration of the collected signal
            dt (float) Contains the time divisions between each signal reading
            sampleFreq (float) Contains the frequency that the signal was sampled
            fundamentalFreq (float) The smallest frequency that can be represented given the length of the signal
            spectrum (List[complex]) Holds the frequency domain version of the signal
            signalFileName (string) as above
            """
        self.signal = []
        self.signalFileName = signalFileName
        if signalFileName != None:
            self.AddSignal()
        elif signalData != None:
            self.signal = signalData
        self.ValidateData()
        self.readings = len(self.signal)
        self.duration = self.signal[self.readings-1][0]
        self.dt = self.duration/(self.readings-1)
        self.sampleFreq = 1/self.dt
        self.fundamentalFreq = self.sampleFreq/self.readings
        self.spectrum = []

    def ValidateData(self):
        """
        Error checking, ensures enough data is present in the signal and removes
        any invalid readings. Quits the program if there is an issue to prevent an
        error.
        """
        for reading in self.signal:
            if reading[0] == "" or reading[1] == "":
                self.signal.remove(reading)
        if len(self.signal) < 2:
            print("Not enough data for processing")
            quit()

    def RemoveDCDrift(self):
        """
        Finds and subtracts the mean from every signal value. This removes the DC
        component from the signal that may interfere with calculations later on.
        """
        sum = 0
        for i in self.GetSignal():
            sum += i
        mean = sum/self.readings
        newSignal = []
        for i in self.GetSignal():
            newSignal.append(i - mean)
        self.SetSignal(newSignal)

    def AddSignal(self):
        """
        Reads the textfile containing the signal. Performs basic error checking
        by discarding invalid readings and stops the program if there is an issue
        opening the file to prevent an error.
        """
        try:
            with open(self.signalFileName, "r") as f:
                content = f.readlines()
        except:
            print("Signal file can't be found!")
            quit()
        for line in content:
            if line.strip():
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    try:
                        time = float(parts[0])
                        value = float(parts[1])
                        self.signal.append([time, value])
                    except:
                        pass
        f.close()

    def GetSignal(self):
        """
        Getter for the signal values.

        Returns:
            signalValues (List[float]) The signal component ONLY of the signal
        """
        signalValues = []
        for reading in self.signal:
            signalValues.append(reading[1])
        return signalValues

    def GetTimes(self):
        """
        Getter for the time values of the signal.

        Returns:
            timeValues (List[float]) The time component ONLY of the signal
        """
        timeValues = []
        for reading in self.signal:
            timeValues.append(reading[0])
        return timeValues

    def GetSignalInfo(self):
        """
        Getter for the signal information output at the end.

        Returns:
            List[float] containing signal duration, sample frequency, fundamental frequency,
                time division and reading count
        """
        return [self.duration, self.sampleFreq, self.fundamentalFreq, self.dt, self.readings]

    def SetSignal(self, newSignal):
        """
        Setter for the signal values.

        Args:
            newSignal (List[float]) Contains the new version of the signal being overwritten
        """
        signalValues = []
        for reading in range(self.readings):
            signalValues.append([self.GetTimes()[reading], newSignal[reading]])
        self.signal = signalValues

class SignalProcessor:
    def __init__(self, movAvgFactor, upperCutoff, lowerCutoff):
        """
        Configurable filter stage for the processing of the input signal. Contains
        methods to smooth using moving averages, perform FFT and IFFT and a band
        pass filter.

        Args:
            movAvgFactor (int) The window that will be used during the moving average stage
            upperCutOff (float) The upper corner for the bandpass filter
            lowerCutOff (float) The bottom corner for the bandpass filter

        Attributes:
            movAvgFactor (int) As above
            upperCutOff (float) As above
            lowerCutOff (float) As above
            """
        self.movAvgFactor = movAvgFactor
        self.upperCutoff = upperCutoff
        self.lowerCutoff = lowerCutoff

    def MovingAverage(self, signal):
        """
        Performs smoothing on a signal by moving average. Pads the end of the signal
        to prevent errors when using the moving window, removes the extra values at
        the end.

        Args:
            signal (Signal) the signal to be smoothed

        Returns:
            Signal Holds the now smoothed version of the signal
        """
        signalValues = signal.GetSignal()
        length = signal.readings
        for i in range(self.movAvgFactor):
            signalValues.append(signalValues[length-1])
        for reading in range(length):
            sum = 0
            for i in range(self.movAvgFactor):
                sum += signalValues[reading+i]
            signalValues[reading] = sum/self.movAvgFactor
        newSignal = []
        for reading in range(length):
            newSignal.append([signal.GetTimes()[reading], signalValues[reading]])
        return Signal(signalData=newSignal)

    def BandPass(self, signal):
        """
        Bandpass filter, takes a signal and removes frequency component outside the
        cutoff range defined in instantiation. Does this by converting to the frequency
        domain via FFT and then reconstructing the clean signal using IFFT.

        Args:
            signal (Signal) Holds the signal being filtered

        Returns:
            Signal The signal after filtering
        """
        fftResult, freqs = self.FFT(signal)
        fftResult[freqs < self.lowerCutoff] = 0
        fftResult[freqs > self.upperCutoff] = 0
        filteredSignal = self.IFFT(fftResult, signal.readings)
        newSignal = []
        for reading in range(signal.readings):
            newSignal.append([signal.GetTimes()[reading], filteredSignal[reading]])
        return Signal(signalData=newSignal)

    def FFT(self, signal):
        """
        Performs a fast-fourier-transform on a given signal.

        Args:
            signal (Signal) Holds the signal being processed

        Returns:
            fftResult (List[Complex]) Contains the complex values for use in a frequency spectrum
            freqs (List[float]) holds the frequency values used to plot a spectrum
        """
        fftResult = fft.rfft(signal.GetSignal())
        freqs = fft.rfftfreq(signal.readings, 1/signal.sampleFreq)
        return fftResult, freqs

    def IFFT(self, fftResult, readings):
        """
        Performs inverse fast-fourier-transform on a given signal

        Args:
            fftResult (List[complex]) The output from an FFT, can be filtered
            readings (int) The amount of readings in the original signal
        """
        reconstructedSignal = fft.irfft(fftResult, n=readings)
        return reconstructedSignal

class SignalResult:
    def __init__(self):
        """
        Holds various methods for plotting graphs and formatting values to output
        in the console.
        """
        pass

    def PlotGraph(self, graph, xValues, yValues, xLabel, yLabel, title):
        """
        Plots a graph using given paramters.

        Args:
            graph (subplot) Contains MatPlotLib subplot being plotted
            xValues (List[float]) The values to be plotted on the x-axis
            yValues (List[float]) The values to be plotted on the y-axis
            xLabel (string) The axes label for the x-axis
            yLabel (string) The axes label for the y-axis
            title (string) The graph title, displayed at the top
        """
        graph.plot(xValues, yValues)
        graph.set_xlabel(xLabel)
        graph.set_ylabel(yLabel)
        graph.set_title(title)

    def OutputSignalInfo(self, signal):
        """
        Formats the useful signal values to output to the console.

        Args:
            signalInfo (List[float]) Useful information about the input signal
        """
        signalInfo = signal.GetSignalInfo()
        print("The input signal had the following characteristics:")
        print("Duration:", str(signalInfo[0]), " s")
        print("Sampling Frequency:", str(round(signalInfo[1], 4)), " hz")
        print("Fundamental Frequency:", str(round(signalInfo[2], 4)), " hz")
        print("Time divisons", str(round(signalInfo[3], 6)), " s")
        print("Readings:", str(signalInfo[4]))

class OximeterAnalyser:
    def __init__(self, filter, signal):
        """
        Main class of the program. Executes operations using the SignalProcessor() on the
        input Signal(). Outputs the result using the SignalResults() class. Analyses the
        oximeter signal to make conclusions about the patient.

        Args:
            filter [SignalProcessor] Instance of SignalProcessor() used to call filters/smoothing
            signal [Signal] The signal collected from the oximeter to be analysed
            BPM [Float] The heart rate retrieved from the oximeter
        """
        self.filter = filter
        self.rawSignal = signal
        self.smoothedSignal = None
        self.filteredSignal = None
        self.output = SignalResult()
        self.BPM = 0

    def CleanSignal(self):
        """
        Retrieves the signal values, uses the moving average method on them, stores
        the amended values.
        """
        self.smoothedSignal = self.filter.MovingAverage(self.rawSignal)

    def FilterSignal(self):
        """
        Retrieves signal values, runs them through a bandpass filter, stores the
        filtered version of the signal.
        """
        self.filteredSignal = self.filter.BandPass(self.smoothedSignal)

    def CalculateSpectrum(self):
        """
        Uses FFT to convert the signal to the frequency domain. Stores it so that
        it can be analysed and plotted later.
        """
        self.filteredSignal.spectrum = self.filter.FFT(self.filteredSignal)

    def AnalyseSignal(self):
        """
        Performs operations on the signal prior to either analysis or plotting
        """
        self.rawSignal.RemoveDCDrift()
        self.CleanSignal()
        self.FilterSignal()
        self.CalculateSpectrum()

    def Plot(self):
        """
        Calls upon methods in the SignalResults() class to plot the 3 graphs of the signal
        at various stages in the filtering process. Frequency spectrum only displays
        the range of the bandpass filter.
        """
        self.AnalyseSignal()
        graphs = plt.subplots(3, 1)[1]
        self.output.PlotGraph(graphs[0], self.rawSignal.GetTimes(), self.rawSignal.GetSignal(), 'Time (s)', 'Signal (V)', 'Original Signal')
        self.output.PlotGraph(graphs[1], self.filteredSignal.GetTimes(), self.filteredSignal.GetSignal(), 'Time (s)', 'Signal (V)', 'Filtered Signal')
        self.output.PlotGraph(graphs[2], self.filteredSignal.spectrum[1], np.abs(self.filteredSignal.spectrum[0]) / self.filteredSignal.readings, 'Frequency (Hz)', 'Magnitude (V)', 'Signal Spectrum')
        graphs[2].set_xlim(BANDPASS_LOWER,BANDPASS_UPPER)
        plt.tight_layout()
        plt.show()

    def CalculateBPM(self):
        """
        Evaluates the FFT of the signal and finds the highest peak. This corresponds to
        the dominant frequency of the signal, which in the range given by the bandpass,
        will be the patients heart-rate. Multiplied by 60 to get BPM.
        """
        self.AnalyseSignal()
        fftResult, freqs = self.filter.FFT(self.filteredSignal)
        fftResult = np.abs(fftResult)
        peak = max(fftResult)
        i = 0
        for result in fftResult:
            if result == peak:
                self.BPM = i
            else:
                i += 1

        print("Dominant frequency: "+str(round(freqs[self.BPM],3))+" Hz")
        self.BPM = freqs[self.BPM] * 60

    def InterpretBPM(self, BPM):
        """
        Interprets the BPM value calculated to make conclusions about the health
        of the patient. Determines if heart rate is too high, too low, ideal or at
        health emergency levels.
        """
        print("The patient has a heart rate of:", str(round(BPM)), "beats per minute (BPM)")
        if self.BPM >= 60 and self.BPM <= 100:
            print("The patient is healthy")
        if self.BPM > 100 and self.BPM <= 180:
            print("The patient has a high heart rate")
        if self.BPM >= 40 and self.BPM < 60:
            print("The patient has a low heart rate")
        if self.BPM < 40 or self.BPM > 180:
            print("The patient needs urgent help!")

    def Results(self):
        """
        Calls the methods to calculate and output the useful signal information
        """
        self.CalculateBPM()
        self.InterpretBPM(self.BPM)
        self.output.OutputSignalInfo(self.rawSignal)


# Initialise Classes
Filter = SignalProcessor(MOVING_AVERAGE_FACTOR, BANDPASS_UPPER, BANDPASS_LOWER)
signal = Signal(SIGNAL_FILENAME)
Analysis = OximeterAnalyser(Filter, signal)

# Analyse and output results
Analysis.Plot()
Analysis.Results()
