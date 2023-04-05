import numpy as np
from scipy.signal import convolve

# Create two arrays
x = np.array([1, 2, 3, 4])
h = np.array([1, 2, 3])

# Perform convolution
y = convolve(x, h)

# Print result
print(y)