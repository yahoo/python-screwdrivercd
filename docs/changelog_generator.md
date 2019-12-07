## Changelog Generator

The `screwdrivercd_changelog` utility is used to produce useful, summarized news files for your project.

This utility reads "news fragements" which contain information _useful to end users_.  It does not contain
developer focused information which is contained in the git commit history.

The news fragements support Markdown style text formatting.

This changelog functionality is intentionally similar in function to the the popular 
[towncrier](https://towncrier.readthedocs.io) changelog utility.

### Rationale

This utility is designed to simplify the process of generating changelog documents, which document
changes for the end users.  This allows the git commit history to be used to document the developer
focused changes.

### Usage

This utility scans the git release history for release tags and associates the files in the
changelog fragement directory with the release they where added.  It then generates a changelog document
with each release as the title and the content of each of the changelog documents added in that release 
as items.

#### Settings

The follow environment variables can be used to tune the behavior of the utility.

| Setting                     | Default Value                                      | Description                                                          |
| --------------------------- | -------------------------------------------------- | -------------------------------------------------------------------- |
| CHANGELOG_DIR               | changelog.d                                        | Directory containing the changelog news fragements                   |
| CHANGELOG_FILENAME          | $SD_ARTIFACTS_DIR/reports/changelog/changelog.md   | Name of the changelog file                                           |
| CHANGELOG_NAME              | Python package name or Unknown if no package       | The Package/Project name for the changelog                           |
| CHANGELOG_ONLY_VERSION_TAGS | True                                               | Only consider tags that begin with the letter 'v' to be release tags |
| CHANGELOG_RELEASES          | all                                                | Release to generate in the changelog or "all" to have the log have all releases |

#### Changelog header

A markdown format changelog header can be defined in a file named `HEADER.md` in the changelog directory.

#### Changelog Fragement Files

Changelog fragments are Markdown format files in the changelog directory.

These file are named in the following format:

{issuenum}.{changetype}.md

issuenum - Is the issue number for the change, this can be any valid string that does not contain a period.

changetype - Is the type of change, it can be one of the following:

- feature - A new feature
- bugfix - The change fixes a bug
- doc - The change is an improvement to the documentation
- removal - The changed involved removing code or features
- misc - Other kinds of changes

### Example

Write a changelog for the current git repository to a file named `docs/changelog.md`

!!! example "Command"

    ```bash
    $ export CHANGELOG_FILENAME="docs/changelog.md"
    $  screwdrivercd_changelog
    ```
    
!!! example "docs/changelog.md"

    # Python screwdrivercd helpers changes
    
    ---
    ## screwdrivercd v0.1.159685 (2019-11-26)
    ### Features
    - Add support for changelogs (#46), this adds a new command `screwdrivercd_changelog` that will generate
    a changelog based on changelog fragments in the changelog directory.  This command uses the git
    history to determine the release the changelog fragment was added in.  This changelog is written
    to the $SD_ARTIFACTS_DIR/report/changelog directory.
