[![PyPI version](https://badge.fury.io/py/ztrack.svg)](https://pypi.python.org/pypi/ztrack)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ztrack.svg)](https://pypi.python.org/pypi/ztrack)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
# ztrack

Toolbox for zebrafish pose estimation.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install ztrack.

```bash
pip install ztrack
```

## Instructions
```bash
#clone repository
git clone git@github.com:kclamar/ztrack.git
# change directory to the repository
cd ztrack
# update the repository
git pull
# switch to the free swim branch
git checkout free-swim
# create conda environment with the name ztrack
conda env create --file environment.yml --name ztrack
# activate the ztrack conda environment
conda activate ztrack
# install the ztrack package
pip install -e .
# create configuration with background subtraction (background is calculated as median of 300 frames)
ztrack create-config --bg-frames 300
# run tracking on a folder with progress bar
ztrack run -r --ignore-errors -v your_folder
```
