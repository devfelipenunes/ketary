from setuptools import setup, Extension
from qiskit.capi import get_include
setup(name="ketary-capi-probe",version="0.0.1",
      ext_modules=[Extension("_ketary_capi_probe",["probe.c"],include_dirs=[get_include()])])
