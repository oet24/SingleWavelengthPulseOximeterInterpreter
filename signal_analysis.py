# oet24 amc272
# Oximeter Program

# Libraries
from numpy import fft
import numpy as np
import matplotlib.pyplot as plt

print("THIS SOFTWARE IS NOT MEDICALLY ACCURATE")
print("Do not base health decisions on the output of this program, seek help from a medical professional")

# Configurable options

SIGNAL_FILENAME = "sig.txt"
BANDPASS_UPPER = 4
BANDPASS_LOWER = 0.5
MOVING_AVERAGE_FACTOR = 10

# Class Definitions

class Signal:
    def __init__(self, signalFileName):
        """
        Retrieves oximeter data from text file and stores it. Holds the signal in
        various stages of the filtering process. Stores useful information about
        the signal.

        Args:
            signalFileName (string) location of the signal textfile

        Attributes:
            originalSignal (List[float, float]) Holds the original signal in [time, signal] format
            smoothedSignal (List[float, float]) Holds the signal after moving average smoothing, [time, signal] format
            filteredSignal (List[float, float]) Holds the fully filtered signal in [time, signal] format
            readings (int) Contains the amount of signal readings collected from the textfile
            duration (float) Contains the duration of the collected signal
            dt (float) Contains the time divisions between each signal reading
            sampleFreq (float) Contains the frequency that the signal was sampled
            fundamentalFreq (float) The smallest frequency that can be represented given the length of the signal
            spectrum (List[complex]) Holds the frequency domain version of the signal
            signalFileName (string) as above
            """
        self.originalSignal = []
        self.smoothedSignal = []
        self.filteredSignal = []
        self.signalFileName = signalFileName
        self.AddSignal()
        self.ValidateData()
        self.readings = len(self.originalSignal)
        self.duration = self.originalSignal[self.readings-1][0]
        self.dt = self.duration/(self.readings-1)
        self.sampleFreq = 1/self.dt
        self.fundamentalFreq = self.sampleFreq/self.readings
        self.RemoveDCDrift()
        self.spectrum = []



    def ValidateData(self):
        """
        Error checking, ensures enough data is present in the signal and removes
        any invalid readings. Quits the program if there is an issue to prevent an
        error.
        """
        for reading in self.originalSignal:
            if reading[0] == "" or reading[1] == "":
                self.originalSignal.remove(reading)
        if len(self.originalSignal) < 2:
            print("Not enough data for processing")
            quit()


    def RemoveDCDrift(self):
        """
        Finds and subtracts the mean from every signal value. This removes the DC
        component from the signal that may interfere with calculations later on.
        """
        sum = 0
        for i in self.GetSignal(1):
            sum += i
        mean = sum/self.readings
        newSignal = []
        for i in self.GetSignal(1):
            newSignal.append(i - mean)
        self.SetSignal(newSignal, 1)

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
                        self.originalSignal.append([time, value])
                    except:
                        pass
        f.close()

    def GetSignal(self, stage):
        """
        Getter for the 3 variations of the signal.

        Args:
            stage (int) Corresponds to a stage in the filtering process

        Returns:
            signalValues (List[float]) The signal component ONLY of the selected signal
        """
        signalValues = []
        if stage == 1: # Raw signal
            signal = self.originalSignal
        elif stage == 2: # Signal after moving average
            signal = self.smoothedSignal
        else: # Signal after band-pass filter
            signal = self.filteredSignal
        for reading in signal:
            signalValues.append(reading[1])
        return signalValues

    def GetTimes(self):
        """
        Getter for the time values of the signal.

        Returns:
            timeValues (List[float]) The time component ONLY of the signal
        """
        timeValues = []
        for reading in self.originalSignal:
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

    def SetSignal(self, newSignal, stage):
        """
        Setter for all 3 stages of the signal.

        Args:
            newSignal (List[float]) Contains the new version of the signal being overwritten
            stage (int) Corresponds to a stage in the filtering process
        """
        # Stage 1, 2 or 3
        signalValues = []
        for reading in range(self.readings):
            signalValues.append([self.GetTimes()[reading], newSignal[reading]])
        if stage == 1: # Raw signal
            self.originalSignal = signalValues
        elif stage == 2: # Signal after moving average
            self.smoothedSignal = signalValues
        else: # Signal after band-pass
            self.filteredSignal = signalValues

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

    def MovingAverage(self, signal, length):
        """
        Performs smoothing on a signal by moving average. Pads the end of the signal
        to prevent errors when using the moving window, removes the extra values at
        the end.

        Args:
            signal (List[float]) the signal to be smoothed
            length (int) the length of the signal (used for padding)

        Returns:
            signal (List[float]) Holds the now smoothed version of the signal
        """
        for i in range(self.movAvgFactor):
            signal.append(signal[length-1])
        for reading in range(length):
            sum = 0
            for i in range(self.movAvgFactor):
                sum += signal[reading+i]
            signal[reading] = sum/self.movAvgFactor
        return signal

    def BandPass(self, signal,readings,fs):
        """
        Bandpass filter, takes a signal and removes frequency component outside the
        cutoff range defined in instantiation. Does this by converting to the frequency
        domain via FFT and then reconstructing the clean signal using IFFT.

        Args:
            signal (List[float]) Holds the signal being filtered
            readings (int) Amount of values in the signal
            fs (float) sampling frequency of the signal

        Returns:
            filteredSignal (List[float]) The signal after filtering
        """
        fftResult, freqs = self.FFT(signal, fs, readings)
        fftResult[freqs < self.lowerCutoff] = 0
        fftResult[freqs > self.upperCutoff] = 0
        filteredSignal = self.IFFT(fftResult, readings)
        return filteredSignal

    def FFT(self, signal, fs, readings):
        """
        Performs a fast-fourier-transform on a given signal.

        Args:
            signal (List[float]) Holds the signal being processed
            readings (int) Amount of values in the signal
            fs (float) sampling frequency of the signal

        Returns:
            fftResult (List[Complex]) Contains the complex values for use in a frequency spectrum
            freqs (List[float]) holds the frequency values used to plot a spectrum
        """
        fftResult = fft.rfft(signal)
        freqs = fft.rfftfreq(readings, 1/fs)
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


class SignalAnalysis:
    def __init__(self, filter, signal):
        """
        Main class of the program. Executes operations using the SignalProcessor() on the
        Signal(). Outputs the result using the SignalResults() class. Also calculates BPM
        on the signal.

        Args:
            filter [SignalProcessor] Instance of SignalProcessor() used to call filters/smoothing
            signal [Signal] The signal collected from the oximeter to be analysed
            output [SignalOutput] Instance of SignalOutput() for outputting the results

        """
        self.filter = filter
        self.signal = signal
        self.output = SignalResult()

    def CleanSignal(self):
        """
        Retrieves the signal values, uses the moving average method on them, stores
        the amended values.
        """
        self.signal.SetSignal(self.filter.MovingAverage(self.signal.GetSignal(1), self.signal.readings), 2)

    def FilterSignal(self):
        """
        Retrieves signal values, runs them through a bandpass filter, stores the
        filtered version of the signal.
        """
        self.signal.SetSignal(self.filter.BandPass(self.signal.GetSignal(2), self.signal.readings, self.signal.sampleFreq), 3)

    def CalculateSpectrum(self):
        """
        Uses FFT to convert the signal to the frequency domain. Stores it so that
        it can be analysed and plotted later.
        """
        self.signal.spectrum = self.filter.FFT(self.signal.GetSignal(3), self.signal.sampleFreq, self.signal.readings)

    def AnalyseSignal(self):
        """
        Performs operations on the signal prior to either analysis or plotting
        """
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
        self.output.PlotGraph(graphs[0], self.signal.GetTimes(), self.signal.GetSignal(1), 'Time (s)', 'Signal (V)', 'Original Signal')
        self.output.PlotGraph(graphs[1], self.signal.GetTimes(), self.signal.GetSignal(3), 'Time (s)', 'Signal (V)', 'Filtered Signal')
        self.output.PlotGraph(graphs[2], self.signal.spectrum[1], np.abs(self.signal.spectrum[0]), 'Frequency (Hz)', 'Magnitude', 'Signal Spectrum')
        graphs[2].set_xlim(BANDPASS_LOWER,BANDPASS_UPPER)
        plt.tight_layout()
        plt.show()

    def GetBPM(self):
        """
        Evaluates the FFT of tje signal and finds the highest peak. This corresponds to
        the dominant frequency of the signal, which in the range given by the bandpass,
        will be the patients heart-rate. Multiplied by 60 to get BPM.

        Returns:
            BPM (float) The heart rate of the patient
        """
        self.AnalyseSignal()
        fftResult, freqs = self.filter.FFT(self.signal.GetSignal(3), self.signal.sampleFreq, self.signal.readings)
        fftResult = np.abs(fftResult)
        peak = max(fftResult)
        BPM = 0
        i = 0
        for result in fftResult:
            if result == peak:
                BPM = i
            else:
                i += 1

        print("Dominant frequency: "+str(round(freqs[BPM],3))+" Hz")
        BPM = freqs[BPM] * 60
        return BPM

    def Results(self):
        """
        Calls the method to format and output the useful signal information
        """
        self.output.OutputSignalInfo(self.GetBPM(), signal.GetSignalInfo())



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

    def InterpretBPM(self, BPM):
        """
        Interprets the BPM value calculated to make conclusions about the health
        of the patient. Determines if heart rate is too high, too low, ideal or at
        health emergency levels.

        Args:
            BPM (float) The heart rate of the patient
        """
        if BPM >= 60 and BPM <= 100:
            return "The patient is healthy"
        if BPM > 100 and BPM <= 180:
            return "The patient has a high heart rate"
        if BPM >= 40 and BPM < 60:
            return "The patient has a low heart rate"
        if BPM < 40 or BPM > 180:
            return "The patient needs urgent help!"


    def OutputSignalInfo(self, BPM, signalInfo):
        """
        Formats the useful signal values to output to the console.

        Args:
            BPM (float) The heart rate of the patient
            signal (Signal) The instance of signal, to retrieve useful signal data.
        """
        print("The patient has a heart rate of:", str(round(BPM)), "beats per minute (BPM)")
        print(self.InterpretBPM(BPM))
        print("The input signal had the following characteristics:")
        print("Duration:", str(signalInfo[0]), " s")
        print("Sampling Frequency:", str(round(signalInfo[1], 4)), " hz")
        print("Fundamental Frequency:", str(round(signalInfo[2], 4)), " hz")
        print("Time divisons", str(round(signalInfo[3], 6)), " s")
        print("Readings:", str(signalInfo[4]))


# Initialise Classes
Filter = SignalProcessor(MOVING_AVERAGE_FACTOR, BANDPASS_UPPER, BANDPASS_LOWER)
signal = Signal(SIGNAL_FILENAME)
Analysis = SignalAnalysis(Filter, signal)

# Analyse and output results
Analysis.Plot()
Analysis.Results()


