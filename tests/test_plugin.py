# -*- coding: UTF-8 -*-
from datetime import datetime
from freezegun import freeze_time
from mock import call, create_autospec, MagicMock
import pytest
from pytest_testrail import vars, plugin
from pytest_testrail.plugin import PyTestRailPlugin
from pytest_testrail.testrail_api import APIClient
from pytest_testrail.vars import TESTRAIL_TEST_STATUS

pytest_plugins = "pytester"

ASSIGN_USER_ID = 3
FAKE_NOW = datetime(2015, 1, 31, 19, 5, 42)
MILESTONE_ID = 5
PROJECT_ID = 4
PYTEST_FILE = """
    from pytest_testrail.plugin import testrail, pytestrail
    @testrail('C1234', 'C5678')
    def test_func():
        pass
    @pytestrail.case('C8765', 'C4321')
    @pytestrail.defect('PF-418', 'PF-517')
    def test_other_func():
        pass
"""
SUITE_ID = 1
TR_NAME = None
DESCRIPTION = 'This is a test description'
TESTPLAN = {
    "id": 58,
    "is_completed": False,
    "entries": [{
        "id": "ce2f3c8f-9899-47b9-a6da-db59a66fb794",
        "name": "Test Run 5/23/2017",
        "runs": [{
            "id": 59,
            "name": "Test Run 5/23/2017",
            "is_completed": False,
        }]
    }, {
        "id": "084f680c-f87a-402e-92be-d9cc2359b9a7",
        "name": "Test Run 5/23/2017",
        "runs": [{
            "id": 60,
            "name": "Test Run 5/23/2017",
            "is_completed": True,
        }]
    }, {
        "id": "775740ff-1ba3-4313-a9df-3acd9d5ef967",
        "name": "Test Run 5/23/2017",
        "runs": [{
            "id": 61,
            "is_completed": False,
        }]
    }]
}

CUSTOM_COMMENT = "This is custom comment"


@pytest.fixture
def api_client():
    spec = create_autospec(APIClient)
    spec.get_error = APIClient.get_error  # don't mock get_error
    return spec


@pytest.fixture
def tr_plugin(api_client):
    return PyTestRailPlugin(api_client, ASSIGN_USER_ID, PROJECT_ID, SUITE_ID, False, True, TR_NAME, DESCRIPTION,
                            version='1.0.0.0', milestone_id=MILESTONE_ID, custom_comment=CUSTOM_COMMENT)


@pytest.fixture
def pytest_test_items(testdir):
    testdir.makepyfile(PYTEST_FILE)
    return [item for item in testdir.getitems(PYTEST_FILE) if item.name != 'testrail']


@freeze_time(FAKE_NOW)
def test_testrun_name():
    assert plugin.testrun_name() == 'Automated Run {}'.format(FAKE_NOW.strftime(vars.DT_FORMAT))


def test_failed_outcome(tr_plugin):
    assert plugin.get_test_outcome('failed') == vars.PYTEST_TO_TESTRAIL_STATUS['failed']


def test_successful_outcome(tr_plugin):
    passed_outcome = vars.PYTEST_TO_TESTRAIL_STATUS['passed']
    assert plugin.get_test_outcome('passed') == passed_outcome


def test_clean_test_ids():
    assert list(plugin.clean_test_ids(['C1234', 'C12345'])) == [1234, 12345]


def test_get_testrail_keys(pytest_test_items, testdir):
    items = plugin.get_testrail_keys(pytest_test_items)
    assert list(items[0][1]) == [1234, 5678]
    assert list(items[1][1]) == [8765, 4321]


def test_add_result(tr_plugin):
    status = TESTRAIL_TEST_STATUS["passed"]
    result = tr_plugin.add_result(1, status, comment='ERROR!', duration=3600, defects='PF-456')

    assert result == {
        'case_id': 1,
        'status_id': status,
        'comment': 'ERROR!',
        'duration': 3600,
        'defects': 'PF-456',
        'test_parametrize': None,
        'suite_id': 0,
        'test_comments': [],
    }


def test_pytest_runtest_makereport(pytest_test_items, tr_plugin):
    rep = MagicMock()
    rep.sections = []
    rep.when = "call"
    rep.failed = True
    rep.longreprtext = "An error"
    rep.skipped = False
    rep.duration = 2
    rep.outcome = "failed"

    class FakeOutcome:
        def get_result(self):
            return rep

    tr_plugin.testrail_data.actual_suites_with_case_ids = {SUITE_ID: [1234, 5678]}

    f = tr_plugin.pytest_runtest_makereport(pytest_test_items[0], None)
    next(f)
    try:
        f.send(FakeOutcome())
    except StopIteration:
        pass

    results = tr_plugin.testrail_data.results
    assert len(results) == 2
    case_ids = {r['case_id'] for r in results}
    assert case_ids == {1234, 5678}
    for r in results:
        assert r['status_id'] == TESTRAIL_TEST_STATUS["failed"]
        assert r['comment'] == "An error"
        assert r['duration'] == 2


def test_pytest_sessionfinish(api_client, tr_plugin):
    tr_plugin.testrail_data.results = [
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["failed"], 'duration': 2.6, 'defects': 'PF-516',
         'comment': '', 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
        {'case_id': 5678, 'status_id': TESTRAIL_TEST_STATUS["blocked"], 'comment': "An error",
         'duration': 0.1, 'defects': None, 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["passed"], 'duration': 2.6,
         'defects': ['PF-517', 'PF-113'], 'comment': '', 'test_parametrize': None, 'test_comments': [],
         'suite_id': SUITE_ID},
    ]
    tr_plugin.testrail_data.testrun_id = 10
    tr_plugin.testrail_data.diff_case_ids = []
    tr_plugin.testrail_data.plan_entry_storage = {
        SUITE_ID: {'testrun_id': 10, 'testplan_entry_id': None, 'case_ids': [1234, 5678]}
    }
    api_client.send_post.return_value = {}

    tr_plugin.publish_results(testrail_data=tr_plugin.testrail_data, results=tr_plugin.testrail_data.results)

    expected_data = {'results': [
        {
            'case_id': 1234,
            'status_id': TESTRAIL_TEST_STATUS["failed"],
            'defects': 'PF-516',
            'version': '1.0.0.0',
            'elapsed': '3s',
            'comment': '{}\n'.format(CUSTOM_COMMENT),
        },
        {
            'case_id': 1234,
            'status_id': TESTRAIL_TEST_STATUS["passed"],
            'defects': ['PF-517', 'PF-113'],
            'version': '1.0.0.0',
            'elapsed': '3s',
            'comment': '{}\n'.format(CUSTOM_COMMENT),
        },
        {
            'case_id': 5678,
            'status_id': TESTRAIL_TEST_STATUS["blocked"],
            'defects': None,
            'version': '1.0.0.0',
            'elapsed': '1s',
            'comment': u'# Pytest result: #\n    An error{}\n'.format(CUSTOM_COMMENT),
        },
    ]}

    api_client.send_post.assert_any_call(vars.ADD_RESULTS_URL.format(10), expected_data, cert_check=True)


def test_pytest_sessionfinish_testplan(api_client, tr_plugin):
    SUITE_ID_2 = 2
    tr_plugin.testrail_data.results = [
        {'case_id': 5678, 'status_id': TESTRAIL_TEST_STATUS["blocked"], 'comment': "An error",
         'duration': 0.1, 'defects': None, 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID_2},
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["passed"], 'duration': 2.6,
         'defects': None, 'comment': '', 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
    ]
    tr_plugin.testrail_data.testrun_id = 0
    tr_plugin.testrail_data.testplan_id = 100
    tr_plugin.testrail_data.diff_case_ids = []
    tr_plugin.testrail_data.plan_entry_storage = {
        SUITE_ID: {'testrun_id': 59, 'testplan_entry_id': 'ce2f3c8f-9899-47b9-a6da-db59a66fb794', 'case_ids': [1234]},
        SUITE_ID_2: {'testrun_id': 61, 'testplan_entry_id': '775740ff-1ba3-4313-a9df-3acd9d5ef967', 'case_ids': [5678]},
    }
    api_client.send_post.return_value = {}

    tr_plugin.publish_results(testrail_data=tr_plugin.testrail_data, results=tr_plugin.testrail_data.results)

    expected_data_59 = {'results': [{
        'case_id': 1234,
        'status_id': TESTRAIL_TEST_STATUS["passed"],
        'defects': None,
        'version': '1.0.0.0',
        'elapsed': '3s',
        'comment': '{}\n'.format(CUSTOM_COMMENT),
    }]}
    expected_data_61 = {'results': [{
        'case_id': 5678,
        'status_id': TESTRAIL_TEST_STATUS["blocked"],
        'defects': None,
        'version': '1.0.0.0',
        'elapsed': '1s',
        'comment': u'# Pytest result: #\n    An error{}\n'.format(CUSTOM_COMMENT),
    }]}

    api_client.send_post.assert_any_call(vars.ADD_RESULTS_URL.format(59), expected_data_59, cert_check=True)
    api_client.send_post.assert_any_call(vars.ADD_RESULTS_URL.format(61), expected_data_61, cert_check=True)


@pytest.mark.parametrize('include_all', [True, False])
def test_create_test_run(api_client, tr_plugin, include_all):
    expected_tr_keys = [3453, 234234, 12]
    expect_name = 'testrun_name'

    tr_plugin.create_test_run(ASSIGN_USER_ID, PROJECT_ID, SUITE_ID, include_all, expect_name, expected_tr_keys,
                              MILESTONE_ID, DESCRIPTION)

    expected_uri = vars.ADD_TESTRUN_URL.format(PROJECT_ID)
    expected_data = {
        'suite_id': SUITE_ID,
        'name': expect_name,
        'description': DESCRIPTION,
        'assignedto_id': ASSIGN_USER_ID,
        'include_all': include_all,
        'case_ids': expected_tr_keys,
        'milestone_id': MILESTONE_ID
    }
    check_cert = True
    api_client.send_post.assert_called_once_with(expected_uri, expected_data, cert_check=check_cert)


def test_is_testrun_available(api_client, tr_plugin):
    """ Test of method `is_testrun_available` """
    tr_plugin.testrun_id = 100

    api_client.send_get.return_value = {'is_completed': False}
    assert tr_plugin.is_testrun_available() is True

    api_client.send_get.return_value = {'error': 'An error occured'}
    assert tr_plugin.is_testrun_available() is False

    api_client.send_get.return_value = {'is_completed': True}
    assert tr_plugin.is_testrun_available() is False


def test_is_testplan_available(api_client, tr_plugin):
    """ Test of method `is_testplan_available` """
    tr_plugin.testplan_id = 100

    api_client.send_get.return_value = {'is_completed': False}
    assert tr_plugin.is_testplan_available() is True

    api_client.send_get.return_value = {'error': 'An error occured'}
    assert tr_plugin.is_testplan_available() is False

    api_client.send_get.return_value = {'is_completed': True}
    assert tr_plugin.is_testplan_available() is False


def test_get_available_testruns(api_client, tr_plugin):
    """ Test of method `get_available_testruns` """
    testplan_id = 100
    api_client.send_get.return_value = TESTPLAN
    assert tr_plugin.get_available_testruns(testplan_id) == [59, 61]


def test_close_test_run(api_client, tr_plugin):
    tr_plugin.testrail_data.results = [
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["failed"], 'duration': 2.6, 'defects': None,
         'comment': '', 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
        {'case_id': 5678, 'status_id': TESTRAIL_TEST_STATUS["blocked"], 'comment': "An error",
         'duration': 0.1, 'defects': None, 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["passed"], 'duration': 2.6, 'defects': None,
         'comment': '', 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
    ]
    tr_plugin.testrail_data.testrun_id = 10
    tr_plugin.testrail_data.close_on_complete = True
    tr_plugin.testrail_data.diff_case_ids = []
    tr_plugin.testrail_data.plan_entry_storage = {
        SUITE_ID: {'testrun_id': 10, 'testplan_entry_id': None, 'case_ids': [1234, 5678]}
    }
    api_client.send_post.return_value = {}

    tr_plugin.publish_results(testrail_data=tr_plugin.testrail_data, results=tr_plugin.testrail_data.results)

    api_client.send_post.assert_any_call(vars.CLOSE_TESTRUN_URL.format(10), data={}, cert_check=True)


def test_close_test_plan(api_client, tr_plugin):
    tr_plugin.testrail_data.results = [
        {'case_id': 5678, 'status_id': TESTRAIL_TEST_STATUS["blocked"], 'comment': "An error",
         'duration': 0.1, 'defects': None, 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["passed"], 'duration': 2.6, 'defects': None,
         'comment': '', 'test_parametrize': None, 'test_comments': [], 'suite_id': SUITE_ID},
    ]
    tr_plugin.testrail_data.testplan_id = 100
    tr_plugin.testrail_data.testrun_id = 0
    tr_plugin.testrail_data.close_on_complete = True
    tr_plugin.testrail_data.diff_case_ids = []
    tr_plugin.testrail_data.plan_entry_storage = {
        SUITE_ID: {'testrun_id': 10, 'testplan_entry_id': None, 'case_ids': [1234, 5678]}
    }
    api_client.send_post.return_value = {}

    tr_plugin.publish_results(testrail_data=tr_plugin.testrail_data, results=tr_plugin.testrail_data.results)

    api_client.send_post.assert_any_call(vars.CLOSE_TESTPLAN_URL.format(100), data={}, cert_check=True)


def test_dont_publish_blocked(api_client):
    """ Case: one test is blocked in TestRail — its result should not be published """
    my_plugin = PyTestRailPlugin(api_client, ASSIGN_USER_ID, PROJECT_ID, SUITE_ID, False, True, TR_NAME,
                                 version='1.0.0.0',
                                 publish_blocked=False
                                 )

    results = [
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["blocked"], 'defects': None,
         'comment': '', 'duration': 0, 'test_parametrize': None, 'test_comments': []},
        {'case_id': 5678, 'status_id': TESTRAIL_TEST_STATUS["passed"], 'defects': None,
         'comment': '', 'duration': 0, 'test_parametrize': None, 'test_comments': []},
    ]

    api_client.send_get.return_value = [
        {'case_id': 1234, 'status_id': TESTRAIL_TEST_STATUS["blocked"]},
        {'case_id': 5678, 'status_id': TESTRAIL_TEST_STATUS["passed"]},
    ]
    api_client.send_post.return_value = {}

    my_plugin._add_results(testrun_id=10, results=results)

    api_client.send_get.assert_called_once_with(vars.GET_TESTS_URL.format(10), cert_check=True)

    # case 1234 is blocked in TR → filtered out; only case 5678 (passed) is published
    expected_uri = vars.ADD_RESULTS_URL.format(10)
    expected_data = {'results': [{
        'case_id': 5678,
        'status_id': TESTRAIL_TEST_STATUS["passed"],
        'defects': None,
        'version': '1.0.0.0',
        'comment': '',
    }]}
    api_client.send_post.assert_called_once_with(expected_uri, expected_data, cert_check=True)


def test_skip_missing_only_one_test(api_client, pytest_test_items):
    my_plugin = PyTestRailPlugin(api_client, ASSIGN_USER_ID, PROJECT_ID,
                                 SUITE_ID, False, True, TR_NAME,
                                 run_id=10,
                                 version='1.0.0.0',
                                 publish_blocked=False,
                                 skip_missing=True)

    api_client.send_get.side_effect = [
        [{'id': SUITE_ID, 'name': 'Suite 1'}],                           # get_suites
        [{'id': 1234}, {'id': 5678}],                                     # get_cases
        {'plan_id': None, 'suite_id': SUITE_ID, 'is_completed': False},   # get_run
        [],                                                                # get_tests (update_testrun)
    ]
    api_client.send_post.return_value = {'id': 10}

    my_plugin.pytest_collection_modifyitems(None, None, pytest_test_items)

    assert not pytest_test_items[0].get_closest_marker('skip')
    assert pytest_test_items[1].get_closest_marker('skip')


def test_skip_missing_correlation_tests(api_client, pytest_test_items):
    my_plugin = PyTestRailPlugin(api_client, ASSIGN_USER_ID, PROJECT_ID,
                                 SUITE_ID, False, True, TR_NAME,
                                 run_id=10,
                                 version='1.0.0.0',
                                 publish_blocked=False,
                                 skip_missing=True)

    # Each test function has one case in TR and one not — neither should be skipped
    api_client.send_get.side_effect = [
        [{'id': SUITE_ID, 'name': 'Suite 1'}],                           # get_suites
        [{'id': 1234}, {'id': 8765}],                                     # get_cases: one from each test
        {'plan_id': None, 'suite_id': SUITE_ID, 'is_completed': False},   # get_run
        [],                                                                # get_tests (update_testrun)
    ]
    api_client.send_post.return_value = {'id': 10}

    my_plugin.pytest_collection_modifyitems(None, None, pytest_test_items)

    assert not pytest_test_items[0].get_closest_marker('skip')
    assert not pytest_test_items[1].get_closest_marker('skip')


def test_api_client_timeout(api_client):
    api_client.send_get.return_value = {"timeout": 50.0}
    api_client.send_get('/timeout', timeout='50')
    api_client.send_get.assert_called_with('/timeout', timeout='50')

    api_client.send_get('/timeout', timeout=50.0)
    api_client.send_get.assert_called_with('/timeout', timeout=50.0)

    api_client.send_get('/timeout', timeout=None)
    api_client.send_get.assert_called_with('/timeout', timeout=None)

    api_client.send_post_return_value = {"timeout": 50.0}
    api_client.send_post('/timeout', data={"body": "body"}, timeout='50')
    api_client.send_post.assert_called_with('/timeout', data={"body": "body"}, timeout='50')

    api_client.send_post('/timeout', data={"body": "body"}, timeout=50.0)
    api_client.send_post.assert_called_with('/timeout', data={"body": "body"}, timeout=50.0)

    api_client.send_post('/timeout', data={"body": "body"}, timeout=None)
    api_client.send_post.assert_called_with('/timeout', data={"body": "body"}, timeout=None)
