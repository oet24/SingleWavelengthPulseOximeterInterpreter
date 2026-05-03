# SingleWavelengthPulseOximeterInterpreter
The code for our program that filters and analyses signals collected from a single-wavelength pulse oximeter.

V 0.0.0 (oet24) 27-4-2026
- Added classes based on UML diagram
- Added methods based on UML diagram
 
V 0.1.0 (oet24) 27-4-2026
- Implemented AddSignal(), can now read in the textfile
- Implemented RemoveDCDrift(), DC offset is now removed from loaded signal
- Getters for signal time and signal values added

V 0.2.0 (amc272) 27-4-2026
- Implemented MovingAverage(), can smooth input signal
- Implemented BandPasss(), filters signal
- Implemented FFT()/IFFT() methods, completes a fourier transform on input signal for analysis
