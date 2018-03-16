# to install locally run python3 setup.py sdist && pip3 install -e .

from distutils.core import setup

setup(name='sfm_pipeline',
      version='0.1',
      py_modules=['open_mvg_mvs']
      )