# The pyproject.toml config file

The `screwdrivercd_install_deps` utility is used to define global package build dependencies for multiple packaging
systems in a single configuration file.

## Rationale

This utility provides a single place to configure global/operating system dependencies
and simplifies creating CI/CD Pipelines that install and build the same package for multiple different
operating system environments in a coherent manner.

## Configuration

The `screwdrivercd_install_deps` utility is configured using the `pyproject.toml` file.  

The `pyproject.toml` file is a [toml](https://github.com/toml-lang/toml) format configuration file, that is defined as part of Python [PEP518](https://www.python.org/dev/peps/pep-0518/) to hold the python package build dependencies.  

All of the configuration for the `screwdrivercd.installdeps` package are under the  is under the `tool.sdv4_installdeps` section which contains the configuration values for the tool as a whole and subsections that define the configuration to use for each package type.

### pyproject.toml tool.sdv4_installdeps configuration

The `tool.sdv4_installdeps` configuration section defines settings that configure how the utility functions.

### fail_on_error

Boolean (True/False) value indicating if the installer should immediately fail if a package installation fails.

The default value is False

```toml
[tool.sdv4_installdeps]
    fail_on_error = true
```

### install

The install configuration setting is an ordered list of the package utilities to run.  **Optional**

If not provided, a default that will run all the package utilities, ordered to execute the system package utilities, followed by the global python pip3 installed packages.

```toml
[tool.sdv4_installdeps]
    install = ['apk', 'apt-get', 'brew', 'yum', 'pip3']
```

## Package section

Each package tool has a setting section under the `tool.sdv4_installdeps` section of the `pyproject.toml`.

### Common Package settings

All the package tools have some settings that are common among them, so the same settings have the same format irregardless of the package utility they are defined under.

#### deps

The deps setting is a list of package dependencies in a format based on the Python [PEP 508](https://www.python.org/dev/peps/pep-0508) Package dependency specification.  

The specification used by the `screwdrivercd.installdeps` package adds the following environment markers which contain 
values from the [distro](https://distro.readthedocs.io/en/latest/) package to allow specifying requirements based on 
attributes of the Operating System distribution.

| Marker                                                                      | Python equivalent | Sample values                                   |
| --------------------------------------------------------------------------- | ----------------- | ----------------------------------------------- |
| [distro_codename](https://distro.readthedocs.io/en/latest/#distro.codename) | distro.codename() | Maipo, bionic                                   |
| [distro_id](https://distro.readthedocs.io/en/latest/#distro.id)             | distro.id()       | rhel, ubuntu, darwin                            |
| [distro_like](https://distro.readthedocs.io/en/latest/#distro.like)         | distro.like()     | fedora, debian                                  |
| [distro_name](https://distro.readthedocs.io/en/latest/#distro.name)         | distro.name()     | Darwin, Red Hat Enterprise Linux Server, Ubuntu |
| [distro_version](https://distro.readthedocs.io/en/latest/#distro.version)   | distro.version()  | 7.4, 18.04, 18.6.0 |

For example, the snippet below will use the yum tool to install the `foo_python36` package from the foo python rpm repo 
if the Operating System version is less than 8.0 and install the `python3` package if the operating system is version 
8.0 or higher.

```toml
[tool.sdv4_installdeps.yum]
repos.foo = 'https://foo.bar.com/foo_rpms.repo;distro_version<"8.0"'
deps = [
    'foo_python36;distro_version<"8.0"',
    'python3;distro_version>="8.0'
]

```
#### repos (Optional)

Some package utilities have the concept of package repositories.  The repos setting is a dictionary of repository name 
and values for repositories to add.  

This setting is only valid for the package utilities that have this concept.  The repo setting can be used to define 
package repositories to add to the host configuration before installing the package dependencies.

Like the deps setting, this setting supports using environment markers to specify environments to add the repositories 
too.

For example, this snippet would add the foo yum/rpm repository before installing the packages in Operating system 
versions lower than 8.0.

```toml
[tool.sdv4_installdeps.yum]
repos.foo_rpms = 'https://foo.bar.com/foo_rpms.repo;distro_version<"8.0"'
```

### apk settings

The apk utility does not support repositories.

```toml
[tool.sdv4_installdeps.apk]
    deps = ['python3']
```

### apt-get settings

The apt-get tool supports both the deps and repos settings

```toml
[tool.sdv4_installdeps.apt-get]
    repos.multiverse = 'multiverse'
    repos.ppa_deadsnakes = 'ppa:deadsnakes/ppa;distro_version>"17.04"'
    deps = ['python3']
```

#### repos apt-get specific values
The `apt-get` repos support adding/enabling built in repos, as well as ppa and repository urls.

### brew settings

The brew utility does not currently support repositories.

```toml
[tool.sdv4_installdeps.brew]
    deps = ['python3']
```

### yum settings

The yum tools supports both repos and deps settings.

```toml
[tool.sdv4_installdeps.yum]
    repos.foo_rpms = 'https://foo.bar.com/foo_rpms.repo'
    deps = [
        'foo_python36;distro_version<"8.0"',
        'python3;distro_version>="8.0"'
    ]
```

#### repos yum specific values

The yum repos values are executed in order, so it is possible to add a repository url, then enable/disable 
specific repositories that where added.

The yum utility configuration supports enabling/disabling repos in addition to being able to add/remove them.  

A repo configuration value that begins with `enable:` will enable the repository instead of adding it.

A repo configuraiton value that begins with `disable` will disable the repository instead of adding it.

```toml
repos.foo_rpms = 'https://foo.bar.com/foo_rpms.repo'
repos.foo_rpms_disable_stable = 'disable:foo_rpms-stable'
repos.foo_rpms_enable_beta = 'enable:foo_rpms-beta'
``` 

### pip3 settings

The pip3 tool supports using the python pip3 command to install python packages for global, system wide use.  It does not currently support repos.

```toml
[tool.sdv4_installdeps.pip3]
    deps = ['serviceping']
```

### Environment Settings

Some settings for `scrwedrivercd_install_deps` command are specified via environment variables.

The following settings are supported:

| Setting                  | Default Value               | Description                                         |
| ------------------------ | --------------------------- | --------------------------- |
| INSTALLDEPS_DEBUG        | False                       | Enable verbose debug output |

## Examples

Here is an example that installs the mysql client package and installs the python `serviceping` package properly on multiple different Linux operating systems.

```toml
[tool.sdv4_installdeps]
    install = ['apk', 'apt-get', 'yum', 'pip3']

    [tool.sdv4_installdeps.apk]
        deps = ['mysql-client']

    [tool.sdv4_installdeps.apt-get]
        deps = ['mysql-client']

    [tool.sdv4_installdeps.brew]
        deps = ['mysql-utilities']
        
    [tool.sdv4_installdeps.yum]
        deps = [
            'mysql;distro_version<"7.0"',
            'mariadb;distro_version>="7.0"'
        ]

    [tool.sdv4_installdeps.pip3]
        deps = ['serviceping']
```
