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
Clone repository
```bash
git clone git@github.com:kclamar/ztrack.git
```
Change directory to the repository
```bash
cd ztrack
```
Update the repository (do this whenever there are updates to the software)
```bash
git pull
```
Switch to the free swim branch
```bash
git checkout free-swim
```
Create conda environment with the name ztrack
```bash
conda env create --file environment.yml --name ztrack
```
Activate the ztrack conda environment
```bash
conda activate ztrack
```
Install the ztrack package
```bash
pip install -e .
```
Create configuration with background subtraction (background is calculated as median of 300 frames)
```bash
ztrack create-config --bg-frames 300
```
Run tracking on a folder with progress bar
```bash
ztrack run -r --ignore-errors -v your_folder
```
