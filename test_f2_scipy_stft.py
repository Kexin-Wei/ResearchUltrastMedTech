import numpy as np
from scipy import fft, signal

source = np.arange(start=-9, stop=91)

# fft compare, passed
sourceFft = fft.fft(source)

# stft compare
# all in, after scaled passed
f, t, s = signal.stft(
    source,
    fs=1,
    window="hann",
    nperseg=100,
    noverlap=2,
    boundary=None,  # type: ignore
    return_onesided=False)
win = signal.get_window("hann", 100)
scale = np.sqrt(win.sum()**2)
s *= scale
sMagnitude = np.absolute(s)

# all in, one-side, passed
f, t, s = signal.stft(
    source,
    fs=1,
    window="hann",
    nperseg=100,
    noverlap=2,
    boundary=None,  # type: ignore
    return_onesided=True)
win = signal.get_window("hann", 100)
scale = np.sqrt(win.sum()**2)
s *= scale
sMagnitude = np.absolute(s)

# segmented
# two-side, passed
f, t, s = signal.stft(
    source,
    fs=1,
    window="hann",
    nperseg=50,
    noverlap=2,
    boundary=None,  # type: ignore
    padded=False,
    return_onesided=False)
win = signal.get_window("hann", 50)
scale = np.sqrt(win.sum()**2)
s *= scale
sMagnitude = np.absolute(s)

# one-side, passed
f, t, s = signal.stft(
    source,
    fs=1,
    window="hann",
    nperseg=50,
    noverlap=2,
    boundary=None,  # type: ignore
    padded=False,
    return_onesided=True)
win = signal.get_window("hann", 50)
scale = np.sqrt(win.sum()**2)
s *= scale
sMagnitude = np.absolute(s)

# Big fft length
# one-sided, passed
f, t, s = signal.stft(
    source,
    fs=1,
    window="hann",
    nperseg=50,
    noverlap=2,
    nfft=70,
    boundary=None,  # type: ignore
    padded=False,
    return_onesided=True)
win = signal.get_window("hann", 50)
scale = np.sqrt(win.sum()**2)
s *= scale
sMagnitude = np.absolute(s)
print("done")
