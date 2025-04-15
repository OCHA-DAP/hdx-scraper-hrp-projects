# Collector for HRP Projects Datasets
[![Build Status](https://github.com/OCHA-DAP/hdx-scraper-hrp-projects/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-scraper-hrp-projects/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-scraper-hrp-projects/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-scraper-hrp-projects?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This script downloads data from HPC.tools and creates HDX datasets for Response Plan project lists for plans that are effective five or fewer years ago.
It also checks the current HRP and GHO country list for updates. If it finds changes that need to be made, it will fail and output messages detailing those changes, which then need to be reviewed and made to the Countries and Territories Taxonomy spreadsheet.

## Development

### Environment

Development is currently done using Python 3.12. We recommend using a virtual
environment such as ``venv``:

    python3.12 -m venv venv
    source venv/bin/activate

In your virtual environment, please install all packages for
development by running:

    pip install -r requirements.txt

### Installing and running


For the script to run, you will need to have a file called
.hdx_configuration.yaml in your home directory containing your HDX key, e.g.:

    hdx_key: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    hdx_read_only: false
    hdx_site: prod

 You will also need to supply the universal .useragents.yaml file in your home
 directory as specified in the parameter *user_agent_config_yaml* passed to
 facade in run.py. The collector reads the key
 **hdx-scraper-hrp_projects** as specified in the parameter
 *user_agent_lookup*.

 Alternatively, you can set up environment variables: `USER_AGENT`, `HDX_KEY`,
`HDX_SITE`, `EXTRA_PARAMS`, `TEMP_DIR`, and `LOG_FILE_ONLY`.

To install and run, execute:

    pip install .
    python -m hdx.scraper.hrp_projects

### Pre-commit

Be sure to install `pre-commit`, which is run every time
you make a git commit:

```shell
pip install pre-commit
pre-commit install
```

The configuration file for this project is in a
non-standard location. Thus, you will need to edit your
`.git/hooks/pre-commit` file to reflect this. Change
the first line that begins with `ARGS` to:

    ARGS=(hook-impl --hook-type=pre-commit)

With pre-commit, all code is formatted according to
[ruff](https://docs.astral.sh/ruff/) guidelines.

To check if your changes pass pre-commit without committing, run:

    pre-commit run --all-files

### Testing

Ensure you have the required packages to run the tests:

    pip install -r requirements-test.txt

To run the tests and view coverage, execute:

`    pytest -c .config/pytest.ini --cov hdx
`
## Packages

[uv](https://github.com/astral-sh/uv) is used for
package management.  If you’ve introduced a new package to the
source code (i.e.anywhere in `src/`), please add it to the
`project.dependencies` section of `pyproject.toml` with any known version
constraints.

To add packages required only for testing, add them to the `test` section under
`[project.optional-dependencies]`.

Any changes to the dependencies will be automatically reflected in
`requirements.txt` and `requirements-test.txt` with `pre-commit`, but you can
re-generate the files without committing by executing:

    pre-commit run pip-compile --all-files

## Project

[Hatch](https://hatch.pypa.io/) is used for project management. The project
can be built using:

    hatch build

Linting and syntax checking can be run with:

    hatch fmt --check

Tests can be executed using:

    hatch test
