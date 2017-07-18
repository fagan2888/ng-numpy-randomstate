import os
import sys
from os.path import join

import numpy as np
from randomstate.prng.mlfg_1279_861 import mlfg_1279_861
from randomstate.prng.mrg32k3a import mrg32k3a
from randomstate.prng.mt19937 import mt19937
from randomstate.prng.pcg32 import pcg32
from randomstate.prng.pcg64 import pcg64
from randomstate.prng.xorshift1024 import xorshift1024
from randomstate.prng.xorshift128 import xorshift128
from randomstate.prng.xoroshiro128plus import xoroshiro128plus
from randomstate.prng.dsfmt import dsfmt
from numpy.testing import assert_equal, assert_allclose, assert_array_equal, \
    assert_raises

if (sys.version_info > (3, 0)):
    long = int

pwd = os.path.dirname(os.path.abspath(__file__))


def uniform32_from_uint64(x):
    x = np.uint64(x)
    upper = np.array(x >> np.uint64(32), dtype=np.uint32)
    lower = np.uint64(0xffffffff)
    lower = np.array(x & lower, dtype=np.uint32)
    joined = np.column_stack([lower, upper]).ravel()
    out = (joined >> np.uint32(9)) * (1.0 / 2 ** 23)
    return out.astype(np.float32)


def uniform32_from_uint63(x):
    x = np.uint64(x)
    x = np.uint32(x >> np.uint64(32))
    out = (x >> np.uint32(9)) * (1.0 / 2 ** 23)
    return out.astype(np.float32)


def uniform32_from_uint53(x):
    x = np.uint64(x)
    x = np.uint32(x & np.uint64(0xffffffff))
    out = (x >> np.uint32(9)) * (1.0 / 2 ** 23)
    return out.astype(np.float32)


def uniform32_from_uint32(x):
    return (x >> np.uint32(9)) * (1.0 / 2 ** 23)


def uniform32_from_uint(x, bits):
    if bits == 64:
        return uniform32_from_uint64(x)
    elif bits == 63:
        return uniform32_from_uint63(x)
    elif bits == 53:
        return uniform32_from_uint53(x)
    elif bits == 32:
        return uniform32_from_uint32(x)
    else:
        raise NotImplementedError


def uniform_from_uint(x, bits):
    if bits in (64, 63, 53):
        return uniform_from_uint64(x)
    elif bits == 32:
        return uniform_from_uint32(x)


def uniform_from_uint64(x):
    return (x >> np.uint64(11)) * (1.0 / 9007199254740992.0)


def uniform_from_uint32(x):
    out = np.empty(len(x) // 2)
    for i in range(0, len(x), 2):
        a = x[i] >> 5
        b = x[i + 1] >> 6
        out[i // 2] = (a * 67108864.0 + b) / 9007199254740992.0
    return out


def uint64_from_uint63(x):
    out = np.empty(len(x) // 2, dtype=np.uint64)
    for i in range(0, len(x), 2):
        a = x[i] & np.uint64(0xffffffff00000000)
        b = x[i + 1] >> np.uint64(32)
        out[i // 2] = a | b
    return out


def uniform_from_dsfmt(x):
    return x.view(np.double) - 1.0


def gauss_from_uint(x, n, bits):
    if bits in (64, 63):
        doubles = uniform_from_uint64(x)
    elif bits == 32:
        doubles = uniform_from_uint32(x)
    elif bits == 'dsfmt':
        doubles = uniform_from_dsfmt(x)
    gauss = []
    loc = 0
    x1 = x2 = 0.0
    while len(gauss) < n:
        r2 = 2
        while r2 >= 1.0 or r2 == 0.0:
            x1 = 2.0 * doubles[loc] - 1.0
            x2 = 2.0 * doubles[loc + 1] - 1.0
            r2 = x1 * x1 + x2 * x2
            loc += 2

        f = np.sqrt(-2.0 * np.log(r2) / r2)
        gauss.append(f * x2)
        gauss.append(f * x1)

    return gauss[:n]


class Base(object):
    dtype = np.uint64
    data2 = data1 = {}

    @classmethod
    def setup_class(cls):
        cls.RandomState = xorshift128.RandomState
        cls.bits = 64
        cls.dtype = np.uint64
        cls.seed_error_type = TypeError

    @classmethod
    def _read_csv(cls, filename):
        with open(filename) as csv:
            seed = csv.readline()
            seed = seed.split(',')
            seed = [long(s) for s in seed[1:]]
            data = []
            for line in csv:
                data.append(long(line.split(',')[-1]))
            return {'seed': seed, 'data': np.array(data, dtype=cls.dtype)}

    def test_raw(self):
        rs = self.RandomState(*self.data1['seed'])
        uints = rs.random_raw(1000)
        assert_equal(uints, self.data1['data'])

        rs = self.RandomState(*self.data2['seed'])
        uints = rs.random_raw(1000)
        assert_equal(uints, self.data2['data'])

    def test_gauss_inv(self):
        n = 25
        rs = self.RandomState(*self.data1['seed'])
        gauss = rs.standard_normal(n, method='bm')
        assert_allclose(gauss,
                        gauss_from_uint(self.data1['data'], n, self.bits))

        rs = self.RandomState(*self.data2['seed'])
        gauss = rs.standard_normal(25, method='bm')
        assert_allclose(gauss,
                        gauss_from_uint(self.data2['data'], n, self.bits))

    def test_uniform_double(self):
        rs = self.RandomState(*self.data1['seed'])
        vals = uniform_from_uint(self.data1['data'], self.bits)
        uniforms = rs.random_sample(len(vals))
        assert_allclose(uniforms, vals)
        assert_equal(uniforms.dtype, np.float64)

        rs = self.RandomState(*self.data2['seed'])
        vals = uniform_from_uint(self.data2['data'], self.bits)
        uniforms = rs.random_sample(len(vals))
        assert_allclose(uniforms, vals)
        assert_equal(uniforms.dtype, np.float64)

    def test_uniform_float(self):
        rs = self.RandomState(*self.data1['seed'])
        vals = uniform32_from_uint(self.data1['data'], self.bits)
        uniforms = rs.random_sample(len(vals), dtype=np.float32)
        assert_allclose(uniforms, vals)
        assert_equal(uniforms.dtype, np.float32)

        rs = self.RandomState(*self.data2['seed'])
        vals = uniform32_from_uint(self.data2['data'], self.bits)
        uniforms = rs.random_sample(len(vals), dtype=np.float32)
        assert_allclose(uniforms, vals)
        assert_equal(uniforms.dtype, np.float32)

    def test_seed_float(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(self.seed_error_type, rs.seed, np.pi)
        assert_raises(self.seed_error_type, rs.seed, -np.pi)

    def test_seed_float_array(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(self.seed_error_type, rs.seed, np.array([np.pi]))
        assert_raises(self.seed_error_type, rs.seed, np.array([-np.pi]))
        assert_raises(self.seed_error_type, rs.seed, np.array([np.pi, -np.pi]))
        assert_raises(self.seed_error_type, rs.seed, np.array([0, np.pi]))
        assert_raises(self.seed_error_type, rs.seed, [np.pi])
        assert_raises(self.seed_error_type, rs.seed, [0, np.pi])

    def test_seed_out_of_range(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(ValueError, rs.seed, 2 ** (2 * self.bits + 1))
        assert_raises(ValueError, rs.seed, -1)

    def test_seed_out_of_range_array(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(ValueError, rs.seed, [2 ** (2 * self.bits + 1)])
        assert_raises(ValueError, rs.seed, [-1])


class TestXorshift128(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = xorshift128.RandomState
        cls.bits = 64
        cls.dtype = np.uint64
        cls.data1 = cls._read_csv(join(pwd, './data/xorshift128-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/xorshift128-testset-2.csv'))
        cls.uniform32_func = uniform32_from_uint64
        cls.seed_error_type = TypeError


class TestXoroshiro128plus(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = xoroshiro128plus.RandomState
        cls.bits = 64
        cls.dtype = np.uint64
        cls.data1 = cls._read_csv(join(pwd, './data/xoroshiro128plus-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/xoroshiro128plus-testset-2.csv'))
        cls.seed_error_type = TypeError


class TestXorshift1024(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = xorshift1024.RandomState
        cls.bits = 64
        cls.dtype = np.uint64
        cls.data1 = cls._read_csv(join(pwd, './data/xorshift1024-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/xorshift1024-testset-2.csv'))
        cls.seed_error_type = TypeError


class TestMT19937(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = mt19937.RandomState
        cls.bits = 32
        cls.dtype = np.uint32
        cls.data1 = cls._read_csv(join(pwd, './data/randomkit-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/randomkit-testset-2.csv'))
        cls.seed_error_type = ValueError

    def test_seed_out_of_range(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(ValueError, rs.seed, 2 ** (self.bits + 1))
        assert_raises(ValueError, rs.seed, -1)
        assert_raises(ValueError, rs.seed, 2 ** (2 * self.bits + 1))

    def test_seed_out_of_range_array(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(ValueError, rs.seed, [2 ** (self.bits + 1)])
        assert_raises(ValueError, rs.seed, [-1])
        assert_raises(TypeError, rs.seed, [2 ** (2 * self.bits + 1)])

    def test_seed_float(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(TypeError, rs.seed, np.pi)
        assert_raises(TypeError, rs.seed, -np.pi)

    def test_seed_float_array(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(TypeError, rs.seed, np.array([np.pi]))
        assert_raises(TypeError, rs.seed, np.array([-np.pi]))
        assert_raises(TypeError, rs.seed, np.array([np.pi, -np.pi]))
        assert_raises(TypeError, rs.seed, np.array([0, np.pi]))
        assert_raises(TypeError, rs.seed, [np.pi])
        assert_raises(TypeError, rs.seed, [0, np.pi])


class TestPCG32(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = pcg32.RandomState
        cls.bits = 32
        cls.dtype = np.uint32
        cls.data1 = cls._read_csv(join(pwd, './data/pcg32-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/pcg32-testset-2.csv'))
        cls.seed_error_type = TypeError

    def test_seed_out_of_range_array(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(TypeError, rs.seed, [2 ** (self.bits + 1)])
        assert_raises(TypeError, rs.seed, [-1])
        assert_raises(TypeError, rs.seed, [2 ** (2 * self.bits + 1)])


class TestPCG64(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = pcg64.RandomState
        cls.bits = 64
        cls.dtype = np.uint64
        cls.data1 = cls._read_csv(join(pwd, './data/pcg64-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/pcg64-testset-2.csv'))
        cls.seed_error_type = TypeError

    def test_seed_out_of_range_array(self):
        # GH #82
        rs = self.RandomState(*self.data1['seed'])
        assert_raises(TypeError, rs.seed, [2 ** (self.bits + 1)])
        assert_raises(TypeError, rs.seed, [-1])
        assert_raises(TypeError, rs.seed, [2 ** (2 * self.bits + 1)])


class TestMRG32K3A(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = mrg32k3a.RandomState
        cls.bits = 32
        cls.dtype = np.uint32
        cls.data1 = cls._read_csv(join(pwd, './data/mrg32k3a-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/mrg32k3a-testset-2.csv'))
        cls.seed_error_type = TypeError


class TestMLFG(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = mlfg_1279_861.RandomState
        cls.bits = 63
        cls.dtype = np.uint64
        cls.data1 = cls._read_csv(join(pwd, './data/mlfg-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/mlfg-testset-2.csv'))
        cls.seed_error_type = TypeError

    def test_raw(self):
        rs = self.RandomState(*self.data1['seed'])
        mod_data = self.data1['data'] >> np.uint64(1)
        uints = rs.random_raw(1000)
        assert_equal(uints, mod_data)

        rs = self.RandomState(*self.data2['seed'])
        mod_data = self.data2['data'] >> np.uint64(1)
        uints = rs.random_raw(1000)
        assert_equal(uints, mod_data)


class TestDSFMT(Base):
    @classmethod
    def setup_class(cls):
        cls.RandomState = dsfmt.RandomState
        cls.bits = 53
        cls.dtype = np.uint64
        cls.data1 = cls._read_csv(join(pwd, './data/dSFMT-testset-1.csv'))
        cls.data2 = cls._read_csv(join(pwd, './data/dSFMT-testset-2.csv'))
        cls.seed_error_type = TypeError

    def test_uniform_double(self):
        rs = self.RandomState(*self.data1['seed'])
        aa = uniform_from_dsfmt(self.data1['data'])
        assert_array_equal(uniform_from_dsfmt(self.data1['data']),
                           rs.random_sample(1000))

        rs = self.RandomState(*self.data2['seed'])
        assert_equal(uniform_from_dsfmt(self.data2['data']),
                     rs.random_sample(1000))

    def test_gauss_inv(self):
        n = 25
        rs = self.RandomState(*self.data1['seed'])
        gauss = rs.standard_normal(n, method='bm')
        assert_allclose(gauss,
                        gauss_from_uint(self.data1['data'], n, 'dsfmt'))

        rs = self.RandomState(*self.data2['seed'])
        gauss = rs.standard_normal(25, method='bm')
        assert_allclose(gauss,
                        gauss_from_uint(self.data2['data'], n, 'dsfmt'))
