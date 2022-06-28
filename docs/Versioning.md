# Package Versioning Helper

The versioning helper script is used to update and propagate a version for the package.   This helper allows the
version numbers for the package to be defined from the Screwdriver CD Pipeline.  

## Rationale

This allows multiple templates within a CI/CD Pipeline to use the same version number for different operations without
needing to make changes to the source code repository.  This makes it possible to have a single pipeline that uses
templates to generate packages and containers in multiple formats that all have the same version without requiring 
changes to the source code repository.

## screwdrivercd_version usage

The versioning wrapper command line utility is named `screwdrivercd_version`.

    usage: screwdrivercd_version [-h] [--force_update] [--version_type {default,git_revision_count,utc_date,sdv4_SD_BUILD}] [--ignore_meta] [--update_meta]
    
    optional arguments:
      -h, --help            show this help message and exit
      --force_update        Update the version in setup.cfg even if it does not have a metadata section (default: False)
      --version_type {default,git_revision_count,utc_date,sdv4_SD_BUILD}
                            Type of version number to generate (default: sdv4_SD_BUILD)
      --ignore_meta         Ignore the screwdriver v4 metadata (default: False)
      --update_meta         Update the screwdriver v4 metadata with a new version (default: False)

This utility can generate a package version and store it in the screwdriver metadata `package.version` attribute.  The
`--version_type` defines the type of package version to generate.

If no arguments are provided, the utility reads it configuration from the `[screwdrivercd.version]` section of the `setup.cfg` file.

The utility will update the version of the `[metadata]` section of the setup.cfg file with the version number from
the screwdriver pipeline package.version metadata attribute. 

### Environment Settings

Some settings for the `scrwedrivercd_version` command are specified via environment variables.

The following settings are supported:

| Setting                  | Default Value               | Description                                         |
| ------------------------ | --------------------------- | --------------------------------------------------- |
| VERSION_DEBUG            | False                       | Enable debug logging                                |

### setup.cfg settings

The setup.cfg go under the `screwdrivercd.verison` setting.

| Setting         | Default Value      | Description                                                                                                     |
|-----------------|--------------------|-----------------------------------------------------------------------------------------------------------------|
| version_type    | git_revision_count | The versioning format to generate, choices:                                                                     |
|                 |                    | git_revision_count - Update the last digit the number of git revisions                                          |
|                 |                    | sdv4_sd_build - Update the last digit with the value of the SD_BUILD environment variable                       |
|                 |                    | utc_date - Generate a version based on the date,  format: year.monthday.hourminutesecond                        |
|                 |                    | sdv4_date - Generate a version based on the date and SD_BUILD environment variable, format: year.month.SD_BUILD |
 | link_to_project | False              | If set to True, a link to the source repo will be added to [metadata]project_urls in setup.cfg                  |  

### Example

This is an example of the `setup.cfg` file before and after, with the `screwdrivercd_version` command run from a
screwdriver pipeline with a BUILD_ID of 1319.


!!! note "setup.cfg - Before"
    ```ini
    [metadata]
    version=5.0.0
    
    [screwdrivercd.version]
    version_type = sdv4_SD_BUILD
    ```

!!! note "Output from the screwdrivercd_version command run in the CI Pipeline"
    ```console
    New version: 5.0.1319
    ```

!!! note "setup.cfg - After"
    ```ini
    [metadata]
    version=5.0.1319
    
    [screwdrivercd.version]
    version_type = sdv4_SD_BUILD
    ```
