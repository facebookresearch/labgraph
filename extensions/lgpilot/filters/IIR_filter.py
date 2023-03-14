import numpy as np

def filter_function(x, a, b):
    """  A function to apply an IRR filter to a signal.
    Input is <x>, and filter parameters are <a> and <b>.
    The output <y> is a signal that has been processed with the filter. 
    """
    z = np.zeros(max(len(b), len(a)))
    y = np.zeros_like(x)
    for n in range(len(x)):
        y[n] = b[0] * x[n]
        for m in range(1, len(b)):
            if n-m >= 0:
                y[n] += b[m] * x[n-m]
        for m in range(1, len(a)):
            if n-m >= 0:
                y[n] -= a[m] * y[n-m]
        z[0] = x[n]
        z[1:] = z[:-1]
    return y 
