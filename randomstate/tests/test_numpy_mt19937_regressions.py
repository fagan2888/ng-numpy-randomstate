from __future__ import division, absolute_import, print_function

import sys
from numpy.testing import (TestCase, run_module_suite, assert_,
                           assert_array_equal, assert_raises)
from numpy.compat import long
import numpy as np
from randomstate import mt19937

class TestRegression(TestCase):

    def test_VonMises_range(self):
        # Make sure generated random variables are in [-pi, pi].
        # Regression test for ticket #986.
        for mu in np.linspace(-7., 7., 5):
            r = mt19937.vonmises(mu, 1, 50)
            assert_(np.all(r > -np.pi) and np.all(r <= np.pi))

    def test_hypergeometric_range(self):
        # Test for ticket #921
        assert_(np.all(mt19937.hypergeometric(3, 18, 11, size=10) < 4))
        assert_(np.all(mt19937.hypergeometric(18, 3, 11, size=10) > 0))

        # Test for ticket #5623
        args = [
            (2**20 - 2, 2**20 - 2, 2**20 - 2),  # Check for 32-bit systems
        ]
        is_64bits = sys.maxsize > 2**32
        if is_64bits and sys.platform != 'win32':
            args.append((2**40 - 2, 2**40 - 2, 2**40 - 2)) # Check for 64-bit systems
        for arg in args:
            assert_(mt19937.hypergeometric(*arg) > 0)

    def test_logseries_convergence(self):
        # Test for ticket #923
        N = 1000
        mt19937.seed(0)
        rvsn = mt19937.logseries(0.8, size=N)
        # these two frequency counts should be close to theoretical
        # numbers with this large sample
        # theoretical large N result is 0.49706795
        freq = np.sum(rvsn == 1) / float(N)
        msg = "Frequency was %f, should be > 0.45" % freq
        assert_(freq > 0.45, msg)
        # theoretical large N result is 0.19882718
        freq = np.sum(rvsn == 2) / float(N)
        msg = "Frequency was %f, should be < 0.23" % freq
        assert_(freq < 0.23, msg)

    def test_permutation_longs(self):
        mt19937.seed(1234)
        a = mt19937.permutation(12)
        mt19937.seed(1234)
        b = mt19937.permutation(long(12))
        assert_array_equal(a, b)

    def test_randint_range(self):
        # Test for ticket #1690
        lmax = np.iinfo('l').max
        lmin = np.iinfo('l').min
        try:
            mt19937.randint(lmin, lmax)
        except:
            raise AssertionError

    def test_shuffle_mixed_dimension(self):
        # Test for trac ticket #2074
        for t in [[1, 2, 3, None],
                  [(1, 1), (2, 2), (3, 3), None],
                  [1, (2, 2), (3, 3), None],
                  [(1, 1), 2, 3, None]]:
            mt19937.seed(12345)
            shuffled = list(t)
            mt19937.shuffle(shuffled)
            assert_array_equal(shuffled, [t[0], t[3], t[1], t[2]])

    def test_call_within_randomstate(self):
        # Check that custom RandomState does not call into global state
        m = mt19937.RandomState()
        res = np.array([0, 8, 7, 2, 1, 9, 4, 7, 0, 3])
        for i in range(3):
            mt19937.seed(i)
            m.seed(4321)
            # If m.state is not honored, the result will change
            assert_array_equal(m.choice(10, size=10, p=np.ones(10)/10.), res)

    def test_multivariate_normal_size_types(self):
        # Test for multivariate_normal issue with 'size' argument.
        # Check that the multivariate_normal size argument can be a
        # numpy integer.
        mt19937.multivariate_normal([0], [[0]], size=1)
        mt19937.multivariate_normal([0], [[0]], size=np.int_(1))
        mt19937.multivariate_normal([0], [[0]], size=np.int64(1))

    def test_beta_small_parameters(self):
        # Test that beta with small a and b parameters does not produce
        # NaNs due to roundoff errors causing 0 / 0, gh-5851
        mt19937.seed(1234567890)
        x = mt19937.beta(0.0001, 0.0001, size=100)
        assert_(not np.any(np.isnan(x)), 'Nans in mt19937.beta')

    def test_choice_sum_of_probs_tolerance(self):
        # The sum of probs should be 1.0 with some tolerance.
        # For low precision dtypes the tolerance was too tight.
        # See numpy github issue 6123.
        mt19937.seed(1234)
        a = [1, 2, 3]
        counts = [4, 4, 2]
        for dt in np.float16, np.float32, np.float64:
            probs = np.array(counts, dtype=dt) / sum(counts)
            c = mt19937.choice(a, p=probs)
            assert_(c in a)
            assert_raises(ValueError, mt19937.choice, a, p=probs*0.9)

if __name__ == "__main__":
    run_module_suite()
