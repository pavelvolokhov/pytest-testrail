# -*- coding: UTF-8 -*-
import os
import sys
from .plugin import PyTestRailPlugin
from .testrail_api import APIClient

if sys.version_info.major == 2:
    # python2
    import ConfigParser as configparser
else:
    # python3
    import configparser


class Messages:
    TESTRAIL = 'Create and update testruns with TestRail'
    TR_CONFIG = 'Path to the config file containing information about the TestRail server (defaults to testrail.cfg)'
    TR_URL = 'TestRail address you use to access TestRail with your web browser (config file: url in API section)'
    TR_EMAIL = 'Email for the account on the TestRail server (config file: email in API section)'
    TR_PASSWORD = 'Password for the account on the TestRail server (config file: password in API section)'
    TR_TIMEOUT = 'Set timeout for connecting to TestRail server'
    TR_TESTRUN_ASSIGNED_TO = 'ID of the user assigned to the test run (config file: assignedto_id in TESTRUN section)'
    TR_TESTRUN_PROJECT_ID = 'ID of the project the test run is in (config file: project_id in TESTRUN section)'
    TR_TESTRUN_SUITE_ID = 'ID of the test suite containing the test cases (config file: suite_id in TESTRUN section)'
    TR_TESTRUN_SUITE_INCLUDE_ALL = 'Include all test cases in specified test suite when creating test run config file: include_all in TESTRUN section)'
    TR_TESTRUN_NAME = 'Name given to testrun, that appears in TestRail (config file: name in TESTRUN section)'
    TR_TESTRUN_DESCRIPTION = 'Description given to testrun, that appears in TestRail config file: description in TESTRUN section'
    TR_RUN_ID = 'Identifier of testrun, that appears in TestRail. If provided, option "--tr-testrun-name" will be ignored'
    TR_TEST_PLAN_ID = 'Identifier of testplan, that appears in TestRail (config file: plan_id in TESTRUN section). If provided, option "--tr-testrun-name" will be ignored'
    TR_TEST_PLAN_NAME = 'Name given to testplan, that appears in TestRail (config file: name in TESTRUN section)'
    TR_TEST_PLAN_DESCRIPTION = 'Description given to testplan, that appears in TestRail (config file: name in TESTRUN section)'
    TR_TEST_PLAN_DESCRIPTION_DEFAULT = 'Test Plan was created via AutoTest'
    TR_VERSION = 'Indicate a version in Test Case result'
    TR_NO_SSL_CHECK = 'Do not check for valid SSL certificate on TestRail host'
    TR_CLOSE_ON_COMPLETE = 'Close a test run on completion'
    TR_DONT_PUBLISH_BLOCKED = 'Determine if results of "blocked" testcases (in TestRail) are published or not'
    TR_SKIP_MISSING = 'Skip test cases that are not present in testrun'
    TR_MILESTONE_ID = 'Identifier of milestone, to be used in run creation (config file: milestone_id in TESTRUN section)'
    TC_CUSTOM_COMMENT = 'Custom comment, to be appended to default comment for test case (config file: custom_comment in TESTCASE section)'


def pytest_addoption(parser):
    group = parser.getgroup('testrail')
    group.addoption('--testrail', action='store_true', help=Messages.TESTRAIL)
    parser.addini("testrail", help=Messages.TESTRAIL, type='bool', default=None)

    group.addoption('--tr-config', action='store', default='testrail.cfg', help=Messages.TR_CONFIG)
    parser.addini('tr-config', help=Messages.TR_CONFIG, default='testrail.cfg')

    group.addoption('--tr-url', action='store', help=Messages.TR_URL)
    parser.addini('tr-url', help=Messages.TR_URL, default=None)

    group.addoption('--tr-email', action='store', help=Messages.TR_EMAIL)
    parser.addini('tr-email', help=Messages.TR_EMAIL, default=None)

    group.addoption('--tr-password', action='store', help=Messages.TR_PASSWORD)
    parser.addini('tr-password', help=Messages.TR_PASSWORD, default=None)

    group.addoption('--tr-timeout', action='store', help=Messages.TR_TIMEOUT)
    parser.addini('tr-timeout', help=Messages.TR_TIMEOUT, default=None)

    group.addoption('--tr-testrun-assignedto-id', action='store', help=Messages.TR_TESTRUN_ASSIGNED_TO)
    parser.addini('tr-testrun-assignedto-id', help=Messages.TR_TESTRUN_ASSIGNED_TO, default=None)

    group.addoption('--tr-testrun-project-id', action='store', help=Messages.TR_TESTRUN_PROJECT_ID)
    parser.addini('tr-testrun-project-id', help=Messages.TR_TESTRUN_PROJECT_ID, default=None)

    group.addoption('--tr-testrun-suite-id', action='store', help=Messages.TR_TESTRUN_SUITE_ID)
    parser.addini('tr-testrun-suite-id', help=Messages.TR_TESTRUN_SUITE_ID, default=None)

    group.addoption(
        '--tr-testrun-suite-include-all', action='store_true', default=None, help=Messages.TR_TESTRUN_SUITE_INCLUDE_ALL
    )
    parser.addini('testrun-suite-include-all', help=Messages.TR_TESTRUN_SUITE_INCLUDE_ALL, default=None)

    group.addoption('--tr-testrun-name', action='store', default=None, help=Messages.TR_TESTRUN_NAME)
    parser.addini('tr-testrun-name', help=Messages.TR_TESTRUN_NAME, default=None)

    group.addoption('--tr-testrun-description', action='store', default=None, help=Messages.TR_TESTRUN_DESCRIPTION)
    parser.addini('tr-testrun-description', help=Messages.TR_TESTRUN_DESCRIPTION, default=None)

    group.addoption('--tr-run-id', action='store', default=0, required=False, help=Messages.TR_RUN_ID)
    parser.addini('tr-run-id', help=Messages.TR_RUN_ID, default=0)

    group.addoption('--tr-plan-id', action='store', required=False, help=Messages.TR_TEST_PLAN_ID)
    parser.addini('tr-plan-id', help=Messages.TR_TEST_PLAN_ID, default=None)

    group.addoption('--tr-testplan-name', action='store', default=None, help=Messages.TR_TEST_PLAN_NAME)
    parser.addini('tr-testplan-name', help=Messages.TR_TEST_PLAN_NAME, default=None)

    group.addoption(
        '--tr-testplan-description',
        action='store',
        default=Messages.TR_TEST_PLAN_DESCRIPTION_DEFAULT,
        help=Messages.TR_TEST_PLAN_DESCRIPTION
    )
    parser.addini(
        'tr-testplan-description',
        help=Messages.TR_TEST_PLAN_DESCRIPTION,
        default=Messages.TR_TEST_PLAN_DESCRIPTION_DEFAULT
    )

    group.addoption('--tr-version', action='store', default='', required=False, help=Messages.TR_VERSION)
    parser.addini('tr-version', help=Messages.TR_VERSION, default='')

    group.addoption('--tr-no-ssl-cert-check', action='store_false', default=None, help=Messages.TR_NO_SSL_CHECK)
    parser.addini('tr-no-ssl-cert-check', help=Messages.TR_NO_SSL_CHECK, default='')

    group.addoption(
        '--tr-close-on-complete', action='store_true', default=False, required=False, help=Messages.TR_CLOSE_ON_COMPLETE
    )
    parser.addini('tr-close-on-complete', help=Messages.TR_CLOSE_ON_COMPLETE, default=False)

    group.addoption(
        '--tr-dont-publish-blocked', action='store_false', required=False, help=Messages.TR_DONT_PUBLISH_BLOCKED
    )
    parser.addini('tr-dont-publish-blocked', help=Messages.TR_DONT_PUBLISH_BLOCKED, default=None)

    group.addoption('--tr-skip-missing', action='store_true', required=False, help=Messages.TR_SKIP_MISSING)
    parser.addini('tr-skip-missing', help=Messages.TR_SKIP_MISSING, default=None)

    group.addoption('--tr-milestone-id', action='store', default=None, required=False, help=Messages.TR_MILESTONE_ID)
    parser.addini('tr-milestone-id', help=Messages.TR_MILESTONE_ID, default=None)

    group.addoption(
        '--tc-custom-comment', action='store', default=None, required=False, help=Messages.TC_CUSTOM_COMMENT
    )
    parser.addini('tc-custom-comment', help=Messages.TC_CUSTOM_COMMENT, default=None)

def pytest_configure(config):
    # Registration marks
    config.addinivalue_line("markers", "testrail: pytestrail mark (example: @pytestrail")
    config.addinivalue_line("markers", "testrail_defects: mark for defects")
    config.addinivalue_line("markers", "testrail_suites: mark for test suite (example: @pytestrail.suite('S11111'))")

    if config.getoption('--testrail'):
        cfg_file_path = config.getoption('--tr-config')
        config_manager = ConfigManager(cfg_file_path, config)
        client = APIClient(config_manager.getoption('tr-url', 'url', 'API'),
                           config_manager.getoption('tr-email', 'email', 'API'),
                           config_manager.getoption('tr-password', 'password', 'API'),
                           timeout=config_manager.getoption('tr-timeout', 'timeout', 'API'))

        config.pluginmanager.register(
            PyTestRailPlugin(
                client=client,
                assign_user_id=config_manager.getoption('tr-testrun-assignedto-id', 'assignedto_id', 'TESTRUN'),
                user_email=config_manager.getoption('tr-email', 'email', 'API'),
                user_password=config_manager.getoption('tr-password', 'password', 'API'),
                tr_url=config_manager.getoption('tr-url', 'url', 'API'),
                project_id=config_manager.getoption('tr-testrun-project-id', 'project_id', 'TESTRUN'),
                suite_id=config_manager.getoption('tr-testrun-suite-id', 'suite_id', 'TESTRUN'),
                include_all=config_manager.getoption('tr-testrun-suite-include-all', 'include_all', 'TESTRUN',
                                                     is_bool=True, default=False),
                cert_check=config_manager.getoption('tr-no-ssl-cert-check', 'no_ssl_cert_check', 'API', is_bool=True,
                                                    default=True),
                tr_name=config_manager.getoption('tr-testrun-name', 'name', 'TESTRUN'),
                tr_description=config_manager.getoption('tr-testrun-description', 'description', 'TESTRUN'),
                testplan_name=config_manager.getoption('tr-testplan-name', 'name', 'TESTRUN'),
                testplan_description=config_manager.getoption('tr-testplan-description', 'description', 'TESTRUN'),
                run_id=config.getoption('--tr-run-id'),
                plan_id=config_manager.getoption('tr-plan-id', 'plan_id', 'TESTRUN'),
                version=config.getoption('--tr-version'),
                close_on_complete=config.getoption('--tr-close-on-complete'),
                publish_blocked=config.getoption('--tr-dont-publish-blocked'),
                skip_missing=config.getoption('--tr-skip-missing'),
                milestone_id=config_manager.getoption('tr-milestone-id', 'milestone_id', 'TESTRUN'),
                custom_comment=config_manager.getoption('tc-custom-comment', 'custom_comment', 'TESTCASE'),
            ),
            # Name of plugin instance (allow to be used by other plugins)
            name="pytest-testrail-instance"
        )


class ConfigManager(object):
    def __init__(self, cfg_file_path, config):
        '''
        Handles retrieving configuration values.
        Config options set in flags are given preferance over options set in the config file.

        :param cfg_file_path: Path to the config file containing information about the TestRail server.
        :type cfg_file_path: str or None
        :param config: Config object containing commandline flag options.
        :type config: _pytest.config.Config
        '''
        self.cfg_file = None
        if os.path.isfile(cfg_file_path) or os.path.islink(cfg_file_path):
            self.cfg_file = configparser.ConfigParser()
            self.cfg_file.read(cfg_file_path)

        self.config = config

    def getoption(self, flag, cfg_name, section=None, is_bool=False, default=None):
        # priority: cli > config file > default

        # 1. return cli option or pytest.ini option (if set)
        value = self.config.getoption('--{}'.format(flag)) or self.config.inicfg.get(flag)
        if value is not None:
            return value

        # 2. return default if not config file path is specified
        if section is None or self.cfg_file is None:
            return default

        if self.cfg_file.has_option(section, cfg_name):
            # 3. return config file value
            return self.cfg_file.getboolean(section, cfg_name) if is_bool else self.cfg_file.get(section, cfg_name)
        else:
            # 4. if entry not found in config file
            return default
