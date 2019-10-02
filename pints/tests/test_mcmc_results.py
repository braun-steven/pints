#!/usr/bin/env python
#
# Tests the basic methods of the adaptive covariance base class.
#
# This file is part of PINTS.
#  Copyright (c) 2017-2019, University of Oxford.
#  For licensing information, see the LICENSE file distributed with the PINTS
#  software package.
#
import pints
import pints.toy as toy
import unittest
import numpy as np
import time
from shared import StreamCapture

# Consistent unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class TestAdaptiveCovarianceMC(unittest.TestCase):
    """
    Tests the basic methods of the adaptive covariance MCMC routine.
    """

    @classmethod
    def setUpClass(cls):
        """ Set up problem for tests. """

        # Create toy model
        cls.model = toy.LogisticModel()
        cls.real_parameters = [0.015, 500]
        cls.times = np.linspace(0, 1000, 1000)
        cls.values = cls.model.simulate(cls.real_parameters, cls.times)

        # Add noise
        cls.noise = 10
        cls.values += np.random.normal(0, cls.noise, cls.values.shape)
        cls.real_parameters.append(cls.noise)
        cls.real_parameters = np.array(cls.real_parameters)

        # Create an object with links to the model and time series
        cls.problem = pints.SingleOutputProblem(
            cls.model, cls.times, cls.values)

        # Create a uniform prior over both the parameters and the new noise
        # variable
        cls.log_prior = pints.UniformLogPrior(
            [0.01, 400, cls.noise * 0.1],
            [0.02, 600, cls.noise * 100]
        )

        # Create a log likelihood
        cls.log_likelihood = pints.GaussianLogLikelihood(cls.problem)

        # Create an un-normalised log-posterior (log-likelihood + log-prior)
        cls.log_posterior = pints.LogPosterior(
            cls.log_likelihood, cls.log_prior)

        # Run MCMC sampler
        xs = [cls.real_parameters * 1.1,
              cls.real_parameters * 0.9,
              cls.real_parameters * 1.15,
              ]

        mcmc = pints.MCMCController(cls.log_posterior, 3, xs,
                                    method=pints.HaarioBardenetACMC)
        mcmc.set_max_iterations(1000)
        mcmc.set_initial_phase_iterations(200)
        mcmc.set_log_to_screen(False)

        start = time.time()
        cls.chains = mcmc.run()
        end = time.time()
        cls.time = end - start

    def test_errors(self):
        # test errors occur when incorrectly calling MCMCResults
        self.assertRaises(ValueError, pints.MCMCResults, self.chains, -3)
        self.assertRaises(ValueError, pints.MCMCResults, self.chains, 0)
        self.assertRaises(ValueError, pints.MCMCResults, self.chains, 1.5,
                          ["param 1"])

    def test_running(self):
        # tests that object works as expected
        results = pints.MCMCResults(self.chains)
        self.assertEqual(results.time(), None)
        self.assertEqual(results.ess_per_second(), None)
        self.assertTrue(len(results.ess()), 3)
        self.assertTrue(len(results.mean()), 3)
        self.assertTrue(len(results.rhat()), 3)
        self.assertTrue(len(results.std()), 3)

        # check positive quantities are so
        for i in range(3):
            self.assertTrue(results.ess()[i] > 0)
            self.assertTrue(results.ess()[i] < 1000)
            self.assertTrue(results.rhat()[i] > 0)
            self.assertTrue(results.std()[i] > 0)
            self.assertTrue(results.mean()[i] > 0)

        # check means are vaguely near true values
        self.assertTrue(np.abs(results.mean()[0] - 0.015) < 0.1)
        self.assertTrue(np.abs(results.mean()[1] - 500) < 100)
        self.assertTrue(np.abs(results.mean()[2] - 10) < 20)

        # check quantiles object
        quantiles = results.quantiles()
        self.assertEqual(quantiles.shape[0], 5)
        self.assertEqual(quantiles.shape[1], 3)
        for i in range(5):
            for j in range(3):
                self.assertTrue(quantiles[i, j] > 0)

    def test_summary(self):
        # tests summary functions when time not given
        results = pints.MCMCResults(self.chains)
        summary = np.array(results.summary())
        self.assertEqual(summary.shape[0], 3)
        self.assertEqual(summary.shape[1], 10)

        with StreamCapture() as c:
            print(results)

        names = ["param", "mean", "std.", "2.5%", "25%", "50%", "75%", "97.5%",
                 "rhat", "ess"]
        for i in range(10):
            self.assertIn(names[i], c.text())

        # tests summary functions when time not given
        results = pints.MCMCResults(self.chains, 20)
        summary = np.array(results.summary())
        self.assertEqual(summary.shape[0], 3)
        self.assertEqual(summary.shape[1], 11)

        with StreamCapture() as c:
            print(results)

        names = ["param", "mean", "std.", "2.5%", "25%", "50%", "75%", "97.5%",
                 "rhat", "ess", "ess per sec."]
        for i in range(11):
            self.assertIn(names[i], c.text())

    def test_ess_per_second(self):
        # tests that ess per second is calculated when time is supplied
        t = 10
        results = pints.MCMCResults(self.chains, t)
        self.assertEqual(results.time(), t)
        ess_per_second = results.ess_per_second()
        ess = results.ess()
        self.assertTrue(len(ess_per_second), 3)
        for i in range(3):
            self.assertEqual(ess_per_second[i], ess[i] / t)

    def test_named_parameters(self):
        # tests that parameter names are used when values supplied
        parameters = ["rrrr", "kkkk", "ssss"]
        results = pints.MCMCResults(self.chains,
                                    parameter_names=parameters)
        with StreamCapture() as c:
            print(results)

        for i in range(3):
            self.assertIn(parameters[i], c.text())

        # with time supplied
        results = pints.MCMCResults(self.chains, time=20,
                                    parameter_names=parameters)
        with StreamCapture() as c:
            print(results)

        for i in range(3):
            self.assertIn(parameters[i], c.text())

        # check errors
        self.assertRaises(ValueError, pints.MCMCResults,
                          self.chains, parameter_names=["a", "b"])

    def test_single_chain(self):
        # tests that single chain is broken up into two bits
        xs = [self.real_parameters * 0.9]
        mcmc = pints.MCMCController(self.log_posterior, 1, xs,
                                    method=pints.HaarioBardenetACMC)
        mcmc.set_max_iterations(1000)
        mcmc.set_initial_phase_iterations(200)
        mcmc.set_log_to_screen(False)
        chains = mcmc.run()
        results = pints.MCMCResults(chains)

        self.assertEqual(results.time(), None)
        self.assertEqual(results.ess_per_second(), None)
        self.assertTrue(len(results.ess()), 3)
        self.assertTrue(len(results.mean()), 3)
        self.assertTrue(len(results.rhat()), 3)
        self.assertTrue(len(results.std()), 3)

        # check positive quantities are so
        for i in range(3):
            self.assertTrue(results.ess()[i] > 0)
            self.assertTrue(results.ess()[i] < 1000)
            self.assertTrue(results.rhat()[i] > 0)
            self.assertTrue(results.std()[i] > 0)
            self.assertTrue(results.mean()[i] > 0)

        # check means are vaguely near true values
        self.assertTrue(np.abs(results.mean()[0] - 0.015) < 0.5)
        self.assertTrue(np.abs(results.mean()[1] - 500) < 200)
        self.assertTrue(np.abs(results.mean()[2] - 10) < 30)

        # check quantiles object
        quantiles = results.quantiles()
        self.assertEqual(quantiles.shape[0], 5)
        self.assertEqual(quantiles.shape[1], 3)
        for i in range(5):
            for j in range(3):
                self.assertTrue(quantiles[i, j] > 0)


if __name__ == '__main__':
    unittest.main()
