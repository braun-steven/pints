#
# Utility classes for Pints
#
# This file is part of PINTS.
#  Copyright (c) 2017, University of Oxford.
#  For licensing information, see the LICENSE file distributed with the PINTS
#  software package.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import pints
import numpy as np
import timeit


def strfloat(x):
    """
    Converts a float to a string, with maximum precision.
    """
    return pints.FLOAT_FORMAT.format(float(x))


class Timer(object):
    """
    Provides accurate timing.

    Example::

        timer = pints.Timer()
        print(timer.format(timer.time()))

    """
    def __init__(self, output=None):
        self._start = timeit.default_timer()
        self._methods = {}

    def format(self, time):
        """
        Formats a (non-integer) number of seconds, returns a string like
        "5 weeks, 3 days, 1 hour, 4 minutes, 9 seconds", or "0.0019 seconds".
        """
        if time < 60:
            return '1 second' if time == 1 else str(time) + ' seconds'
        output = []
        time = int(round(time))
        units = [
            (604800, 'week'),
            (86400, 'day'),
            (3600, 'hour'),
            (60, 'minute'),
        ]
        for k, name in units:
            f = time // k
            if f > 0 or output:
                output.append(str(f) + ' ' + (name if f == 1 else name + 's'))
            time -= f * k
        output.append('1 second' if time == 1 else str(time) + ' seconds')
        return ', '.join(output)

    def reset(self):
        """
        Resets this timer's start time.
        """
        self._start = timeit.default_timer()

    def time(self):
        """
        Returns the time (in seconds) since this timer was created, or since
        meth:`reset()` was last called.
        """
        return timeit.default_timer() - self._start


def vector(x):
    """
    Copies ``x`` and returns a 1d read-only numpy array of floats with shape
    ``(n,)``.
    Raises a ``ValueError`` if ``x`` has an incompatible shape.
    """
    x = np.array(x, copy=True, dtype=float)
    x.setflags(write=False)
    if x.ndim != 1:
        n = np.max(x.shape)
        if np.prod(x.shape) != n:
            raise ValueError('Unable to convert to 1d vector of scalar values')
        x = x.reshape((n,))
    return x
