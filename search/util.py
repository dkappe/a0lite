import numpy as np

def softmax2(x):
    z = np.array(list(x))
    return np.exp(z)/np.sum(np.exp(z)).tolist()

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    z = np.array(list(x))
    e_x = np.exp(z - np.max(z))
    return e_x / e_x.sum()

def temp_softmax(x, sm=2.2):
    inv = 1.0/sm
    z = list(map(lambda v: v**inv, x))
    total = sum(z)
    if (total > 0.0):
        scale = 1.0/total
        z2 = list(map(lambda v: v*scale, z))
        z = z2
    return z

def cp(Q):
    return int(295 * Q / ( 1 - 0.976953125 * Q**14 ))
