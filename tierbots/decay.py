from math import ceil


def param_by_zerotime(time, zero_time, decay):
    '''
    >>> param_by_zerotime(49, 60, 0.1)
    2
    >>> param_by_zerotime(50, 60, 0.1)
    1
    >>> param_by_zerotime(59, 60, 0.1)
    1
    >>> param_by_zerotime(60, 60, 0.1)
    0
    >>> param_by_zerotime(1000, 60, 0.1)
    0
    '''
    if time >= zero_time:
        return 0
    return ceil((zero_time - time) * decay)


def zerotime_by_param_change(time, zero_time, decay, param_change):
    '''
    >>> zerotime_by_param_change(50, 60, 0.1, 1)
    70
    >>> zerotime_by_param_change(50, 62, 0.1, 1)
    72
    >>> zerotime_by_param_change(49, 60, 0.1, -1)
    50
    >>> zerotime_by_param_change(50, 60, 0.1, -1)
    50
    >>> zerotime_by_param_change(50, 60, 0.1, -2)
    50
    '''
    if time >= zero_time:
        zero_time = time
    nt = zero_time + ceil(param_change / decay)
    if nt <= time:
        nt = time
    return nt


def param_by_filltime(time, fill_time, growth, max_value):
    '''
    >>> param_by_filltime(49, 60, 0.1, 100)
    98
    >>> param_by_filltime(50, 60, 0.1, 100)
    99
    >>> param_by_filltime(59, 60, 0.1, 100)
    99
    >>> param_by_filltime(60, 60, 0.1, 100)
    100
    >>> param_by_filltime(1000, 60, 0.1, 100)
    100
    '''
    if time >= fill_time:
        return max_value
    return max_value - ceil((fill_time - time) * growth)
