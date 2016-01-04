from distutils.core import setup
from distutils.extension import Extension
from os import getcwd
from os.path import join

import numpy
from Cython.Build import cythonize

rngs = ['RNG_DUMMY', 'RNG_PCG32', 'RNG_PCG64',
        'RNG_MT19937', 'RNG_XORSHIFT128',
        'RNG_XORSHIFT1024', 'RNG_MRG32K3A', 'RNG_MLFG_1279_861']

with open('config.pxi', 'w') as config:
    config.write('# Autogenerated\n\n')
    for key in rngs:
        val = '1' if key == 'RNG_XORSHIFT128' else '0'
        config.write('DEF ' + key + ' = ' + val + '\n')

pwd = getcwd()

sources = [join(pwd, 'wrappers.pyx'),
           join(pwd, 'src', 'common', 'entropy.c'),
           join(pwd, 'distributions.c')]

sources += [join(pwd, 'src', 'xorshift128', p) for p in ('xorshift128.c',)]
sources += [join(pwd, 'shims', 'xorshift128', 'xorshift128-shim.c')]

defs = [('XORSHIFT128_RNG', '1')]

include_dirs = [pwd] + [numpy.get_include()]
include_dirs += [join(pwd, 'src', 'xorshift128')]

setup(ext_modules=cythonize([Extension("core_rng",
                                       sources=sources,
                                       include_dirs=include_dirs,
                                       define_macros=defs,
                                       extra_compile_args=['-std=c99'])
                             ])
      )
