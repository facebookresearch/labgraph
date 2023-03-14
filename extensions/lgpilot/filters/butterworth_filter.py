import numpy as np

def filter_function(x, cutoff_freq, sample_rate, order=4):
    """
    A function to apply a Butterworth filter to a signal.
    
    Args:
        x (numpy.ndarray): The input signal to be filtered.
        cutoff_freq (float): The cutoff frequency of the filter.
        sample_rate (float): The sample rate of the signal.
        order (int): The order of the filter. Defaults to 4.
    
    Returns:
        numpy.ndarray: The filtered signal.
    """
    nyquist_freq = sample_rate / 2
    normal_cutoff = cutoff_freq / nyquist_freq
    b = np.zeros(order+1)
    a = np.zeros(order+1)
    
    for i in range(order+1):
        binomial_coefficient = 1
        for j in range(order):
            if j != i:
                binomial_coefficient *= (normal_cutoff - np.exp(1j*np.pi*(j-i)/order)) / (1 - np.exp(1j*np.pi*(j-i)/order))
        b[i] = np.real(binomial_coefficient)
        a[i] = np.imag(binomial_coefficient)
    
    gain = 1 / np.abs(np.polyval(b, 1j*normal_cutoff) / np.polyval(a, 1j*normal_cutoff))
    b *= gain

    y = np.zeros_like(x)
    
    for i in range(len(x)):
        y[i] = np.sum(b * x[max(0,i-len(b)+1):i+1]) - np.sum(a[1:] * x[max(0,i-len(a)):i])
    
    return y
