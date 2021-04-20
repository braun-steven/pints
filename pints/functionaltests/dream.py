#!/usr/bin/env python3
#
# This file is part of PINTS (https://github.com/pints-team/pints/) which is
# released under the BSD 3-clause license. See accompanying LICENSE.md for
# copyright notice and full license details.
#

from __future__ import division

import pints

from ._problems import (RunMcmcMethodOnTwoDimGaussian,
                        RunMcmcMethodOnBanana)


def test_dream_on_two_dim_gaussian(n_iterations=None):
    if n_iterations is None:
        n_iterations = 10000
    problem = RunMcmcMethodOnTwoDimGaussian(
        method=pints.DreamMCMC,
        n_chains=10,
        n_iterations=n_iterations,
        n_warmup=1000
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }


def test_dream_on_banana(n_iterations=None):
    if n_iterations is None:
        n_iterations = 5000
    problem = RunMcmcMethodOnBanana(
        method=pints.DreamMCMC,
        n_chains=20,
        n_iterations=n_iterations,
        n_warmup=1000
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }