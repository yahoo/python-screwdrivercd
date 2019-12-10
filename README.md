[![Build Status](https://cd.screwdriver.cd/pipelines/3063/badge?nocache=true)](https://cd.screwdriver.cd/pipelines/3063)
[![Package](https://img.shields.io/badge/package-pypi-blue.svg)](https://pypi.org/project/screwdrivercd/)
[![Codecov](https://codecov.io/gh/yahoo/python-screwdrivercd/branch/master/graph/badge.svg?nocache=true)](https://codecov.io/gh/yahoo/python-screwdrivercd)
[![Codestyle](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Documentation](https://img.shields.io/badge/Documentation-latest-blue.svg)](https://yahoo.github.io/python-screwdrivercd/)


# screwdrivercd

Python helper utilities for CI/CD

Implementing CI Pipeline templates for screwdriver?  This package provides a number of useful utility scripts that can
be called from CI jobs to automate common operations.

These utilities are used by the screwdrivercd python templates but can be used with other CI/CD
systems as well.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Contribute](#contribute)
- [License](#license)

## Background

Screwdriver templates that perform complicated operations can be tricky to write and test.  This package contains a number of useful and tested scripts used by Yahoo/Oath/Verizon to perform steps within Screwdriver CI/CD templates.

## Install

This package can be installed using the Python pip package manager that has been configured to use the Oath/Yahoo
internal package repository.

In order to install this package the python environment must have:

* Python version 3.6 or newer
* pip version 8.1.1 or higher
* setuptools 31.0.0 or higher

Install this package using the Python package installer

```console
$ pip install screwdrivercd
```

## Usage

This package contains a number of scripts which are documented in the [project documentation](https://yahoo.github.io/python-screwdrivercd/)

## Contribute

Please refer to [the contributing.md file](Contributing.md) for information about how to get involved. We welcome issues, questions, and pull requests. Pull Requests are welcome.

## Maintainers
Dwight Hubbard: dhubbard@verizonmedia.com

## License

This project is licensed under the terms of the [BSD](LICENSE) open source license. Please refer to [LICENSE](LICENSE) for the full terms.

