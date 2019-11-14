# screwdrivercd

Python helper utilities for screwdriver CI/CD

Implementing CI Pipeline templates for screwdriver?  This package provides a number of useful 
utility scripts that can be called from CI jobs to automate common operations.

## Background

Screwdriver templates that perform complicated operations can be tricky to write and test.  This 
package contains a number of useful and tested scripts used by Yahoo/Oath/Verizon to perform steps 
within Screwdriver CI/CD templates.

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

