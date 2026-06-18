pytest-testrail
===============

![](https://github.com/pavelvolokhov/pytest-testrail/workflows/PR%20Builder/badge.svg)
[![PyPI version](https://badge.fury.io/py/pytest-testrail.svg)](https://badge.fury.io/py/pytest-testrail)
[![Downloads](https://pepy.tech/badge/pytest-testrail)](https://pepy.tech/project/pytest-testrail)

This is a pytest plugin for creating/editing testplans or testruns based on pytest markers.
The results of the collected tests will be updated against the testplan/testrun in TestRail.

Installation
------------

    pip install pytest-testrail

Configuration
-------------

### Config for Pytest tests

Add a marker to the tests that will be picked up to be added to the run.

```python
from pytest_testrail import pytestrail

@pytestrail.case('C1234', 'C5678')
def test_foo():
    # test code goes here
```

> **Note:** The `@testrail` decorator is **deprecated** and will be removed in a future release.
> Use `@pytestrail.case` instead.

To mark a test with a specific test suite (useful for multi-suite projects — no need to pass `--tr-testrun-suite-id`):

```python
from pytest_testrail import pytestrail

@pytestrail.case('C1234', 'C5678')
@pytestrail.suite('S1111')
def test_foo():
    # test code goes here
```

To add defects to a test case result:

```python
from pytest_testrail import pytestrail

@pytestrail.defect('PF-524', 'BR-543')
def test_bar():
    # test code goes here
```

To add a custom comment to a test case result from within the test body, use the `testrail_comment` fixture:

```python
def test_baz(testrail_comment):
    testrail_comment("Step 1 passed", "Additional details here")
    # test code goes here
```

### Config for TestRail

* Settings file template config:

```ini
[API]
url = https://yoururl.testrail.net/
email = user@email.com
password = <api_key>

[TESTRUN]
assignedto_id = 1
project_id = 2
suite_id = 3
plan_id = 4
name = My Test Run
description = This is an example description
milestone_id = 5

[TESTCASE]
custom_comment = This is a custom comment
```

Or

* Set command line options (see below)

Or configure via **`pytest.ini`**:

```ini
[pytest]
testrail = true
tr-url = https://yoururl.testrail.net/
tr-email = user@email.com
tr-password = <api_key>
tr-testrun-project-id = 2
tr-testrun-suite-id = 3
tr-testrun-name = My Test Run
```

Or configure via **`pyproject.toml`**:

```toml
[tool.pytest.ini_options]
testrail = true
tr-url = "https://yoururl.testrail.net/"
tr-email = "user@email.com"
tr-password = "<api_key>"
tr-testrun-project-id = "2"
tr-testrun-suite-id = "3"
tr-testrun-name = "My Test Run"
```

Options can also be set via environment variables using the option name (without `--`) as the variable name. Priority order: **CLI flag > `pytest.ini`/`pyproject.toml` > environment variable > config file**.

Usage
-----

Basically, the following command will create a testrun in TestRail, add all marked tests to run.
Once the all tests are finished they will be updated in TestRail:

```bash
py.test --testrail --tr-config=<settings file>.cfg
```

The plugin supports **pytest-xdist** for parallel test execution. Results are collected from all workers and published by the controller once the session completes.

Examples
--------

TestRun will be created automatically:
```bash
py.test --testrail --tr-testrun-suite-id=XXXX
```

TestRun will be created automatically with a custom name:
```bash
py.test --testrail --tr-testrun-name='TestRunName' --tr-testrun-suite-id=XXXX
```

TestPlan will be created automatically with a name, and a TestRun will be added to it:
```bash
py.test --testrail --tr-testplan-name='NameTestPlan' --tr-testrun-suite-id=XXXX
```

TestRun will be added to an existing TestPlan:
```bash
py.test --testrail --tr-plan-id=XXXXXX --tr-testrun-suite-id=XXXX
```

Update an existing TestRun (RRRRRR) inside an existing TestPlan (PPPPPP):
```bash
py.test --testrail --tr-plan-id=PPPPPP --tr-run-id=RRRRRR --tr-testrun-suite-id=XXXX
```

### All available options

| Option                           | Description                                                                                                                                          |
|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--testrail`                     | Create and update testruns with TestRail                                                                                                             |
| `--tr-config`                    | Path to the config file containing information about the TestRail server (defaults to `testrail.cfg`)                                                |
| `--tr-url`                       | TestRail address you use to access TestRail with your web browser (config file: `url` in `[API]` section)                                            |
| `--tr-email`                     | Email for the account on the TestRail server (config file: `email` in `[API]` section)                                                               |
| `--tr-password`                  | Password for the account on the TestRail server (config file: `password` in `[API]` section)                                                         |
| `--tr-timeout`                   | Timeout (in seconds) for connecting to the TestRail server                                                                                           |
| `--tr-testrun-assignedto-id`     | ID of the user assigned to the test run (config file: `assignedto_id` in `[TESTRUN]` section)                                                        |
| `--tr-testrun-project-id`        | ID of the project the test run is in (config file: `project_id` in `[TESTRUN]` section)                                                              |
| `--tr-testrun-suite-id`          | ID of the test suite containing the test cases (config file: `suite_id` in `[TESTRUN]` section)                                                      |
| `--tr-testrun-suite-include-all` | Include all test cases in the specified test suite when creating a test run (config file: `include_all` in `[TESTRUN]` section)                       |
| `--tr-testrun-name`              | Name given to the testrun in TestRail (config file: `name` in `[TESTRUN]` section)                                                                   |
| `--tr-testrun-description`       | Description given to the testrun in TestRail (config file: `description` in `[TESTRUN]` section)                                                     |
| `--tr-run-id`                    | Identifier of an existing testrun in TestRail. If provided, `--tr-testrun-name` is ignored                                                           |
| `--tr-plan-id`                   | Identifier of an existing testplan in TestRail (config file: `plan_id` in `[TESTRUN]` section). If provided, `--tr-testrun-name` is ignored           |
| `--tr-testplan-name`             | Name given to a newly created testplan in TestRail                                                                                                   |
| `--tr-testplan-description`      | Description given to a newly created testplan in TestRail                                                                                            |
| `--tr-version`                   | Indicate a version in the Test Case result                                                                                                           |
| `--tr-no-ssl-cert-check`         | Do not check for a valid SSL certificate on the TestRail host                                                                                        |
| `--tr-close-on-complete`         | Close the test plan or test run on completion                                                                                                        |
| `--tr-dont-publish-blocked`      | Do not publish results of "blocked" testcases in TestRail                                                                                            |
| `--tr-skip-missing`              | Skip test cases that are not present in the testrun                                                                                                  |
| `--tr-milestone-id`              | Identifier of the milestone to be assigned to the run (config file: `milestone_id` in `[TESTRUN]` section)                                           |
| `--tc-custom-comment`            | Custom comment, appended to the default comment for each test case result (config file: `custom_comment` in `[TESTCASE]` section)                     |
