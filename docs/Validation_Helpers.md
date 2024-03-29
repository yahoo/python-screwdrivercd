# Validation helpers

## Code Style Validation - screwdrivercd_validate_style

The `screwdrivercd_validate_style` command runs the codestyle command from the codestyle package.

### Environment Settings

All settings for the `scrwedrivercd_validate_type` command are specified via environment variables.

The following settings are supported:

| Setting                  | Default Value               | Description                                         |
| ------------------------ | --------------------------- | --------------------------------------------------- |
| CODESTYLE_ARGS           |                             | Additional codestyle command arguments              |
| PACKAGE_DIRECTORY        | .                           | Directory containing the package source             |
| STYLE_CHECK_DEBUG        | False                       | Enable style check debug logging                    |

### Example

This example runs the codestyle check.

!!! example  "screwdriver.yaml - With an enforcing type check"

    ```yaml
    version: 4
    jobs:
        style_check:
            template: python/validate_style
    ```

### Artifacts

| Directory | Description |
| --------- | ----------- |
| reports/style_validation | Report files generated by the codestyle command |

## Dependency Validation - screwdrivercd_validate_deps

The `screwdriver_validate_deps` command runs the [safety](https://github.com/pyupio/safety) utility to validate the package does
not use package dependencies with security issues.

### Example

This example runs the dependency check

!!! example "screwdriver.yaml - With dependency check"

    ```yaml
    version: 4
    jobs:
        style_check:
            template: python/validate_dependencies
    ```

### Artifacts

| Directory | Description |
| --------- | ----------- |
| reports/dependency_validation | Report files generated by the safety command |

## Type Validation - screwdrivercd_validate_type
 
The `screwdrivercd_validate_type` command runs type annotation validations using the mypy tool.

### Environment Settings

All settings for the `scrwedrivercd_validate_type` command are specified via environment variables.

The following settings are supported:

| Setting                  | Default Value               | Description                                         |
| ------------------------ | --------------------------- | --------------------------------------------------- |
| BASE_PYTHON              | python3                     | Python interpreter to use                           |
| MYPY_ARGS                | --ignore-missing-imports    | Additional mypy command arguments                   |
| PACKAGE_DIRECTORY        | .                           | Directory containing the package source             |
| TYPE_CHECK_DEBUG         | False                       | Enable debug logging if True                        |
| TYPE_CHECK_ENFORCING     | False                       | Make check enforcing                                |
| TYPE_CHECK_REPORT_FORMAT | txt,cobertura-xml,junit-xml | Comma seperated list of report formats to generate. |
|                          |                             | Supported formats:                                  |
|                          |                             | any-exprs, cobertura-xml, html, junit-xml,          |
|                          |                             | linecount, linecoverage, memory, txt, xml,          |
|                          |                             | xslt-html, xslt-txt                                 |


### Example

This example runs the type check with enforcement enabled.

!!! note "screwdriver.yaml - With an enforcing type check"
    ```yaml
    version: 4
    jobs:
        type_check:
            template: python/validate_type
            environment:
                TYPE_CHECK_ENFORCING: True
    ```

### Artifacts

| Directory | Description |
| --------- | ----------- |
| reports/type_validation | Report files generated by the mypy command |

## Unit Test Validation - screwdrivercd_validate_unittest
 
The `screwdrivercd_validate_unittest` command runs unittests via the [tox](https://tox.readthedocs.io) tool.

### Environment Settings

All settings for the `scrwedrivercd_validate_unittest` command are specified via environment variables.

The following settings are supported:

| Setting                  | Default Value               | Description                                         |
| ------------------------ | --------------------------- | --------------------------------------------------- |
| BASE_PYTHON              | python3                     | Python interpreter to use                           |
| TOX_ARGS                 |                             | Additional tox command arguments                    |
| TOX_ENVLIST              |                             | Only run tests with specific envlist from the tox configuration |

### Example

This example runs the tox command only using a python 3.8 (py38) virtualenv.

!!! note "screwdriver.yaml - With unittest check"
    ```yaml
    version: 4
    jobs:
        type_check:
            template: python/validate_unittest
            environment:
                TOX_ARGS: -v
                TOX_ENVLIST: py38
    ```

### Artifacts

| Directory | Description |
| --------- | ----------- |
| logs/tox  | All of the tox log files |
