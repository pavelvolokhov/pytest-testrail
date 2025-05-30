import sys
from collections import defaultdict
from operator import itemgetter
from pytest_testrail.TestrailModel import TestRailModel
from pytest_testrail.functions import get_case_list, filter_publish_results
from pytest_testrail.vars import TESTRAIL_PREFIX, TESTRAIL_TEST_STATUS, COMMENT_SIZE_LIMIT, ADD_RESULTS_URL, \
    ADD_TESTRUN_URL, ADD_TESTPLAN_ENTRY_URL, UPDATE_RUN_URL, GET_TESTRUN_URL, CLOSE_TESTRUN_URL, CLOSE_TESTPLAN_URL, \
    GET_TESTPLAN_URL, GET_TESTCASES_URL, GET_TESTS_URL, UPDATE_TESTPLAN_ENTRY, ADD_TESTPLAN_URL, GET_SUITES_URL


class TestrailActions:
    def __init__(self, testrail_data: TestRailModel):
        self.testrail_data = testrail_data

    def add_result(self, test_id, status, comment: str = "", defects=None, duration=0, test_parametrize=None, suite_id=0,
                   test_comments: list | None = None):
        """
        Add a new result to results dict to be submitted at the end.

        :param suite_id:
        :param test_id:
        :param test_comments: add text from comment fixture
        :param list test_parametrize: Add test parametrize to test result
        :param defects: Add defects to test result
        :param int status: status code of test (pass or fail).
        :param comment: None or a failure representation.
        :param duration: Time it took to run just the test.
        """
        data = {
            'case_id': test_id,
            'status_id': status,
            'comment': comment,
            'duration': duration,
            'defects': defects,
            'test_parametrize': test_parametrize,
            "suite_id": suite_id,
            "test_comments": test_comments or []
        }
        return data

    def _add_results(self, testrun_id, results):
        """
        Add results one by one to improve errors handling.
        :param testrun_id: Id of the testrun to feed

        """
        # unicode converter for compatibility of python 2 and 3
        try:
            converter = unicode
        except NameError:
            converter = lambda s, c: str(bytes(s, "utf-8"), c)
        # Results are sorted by 'case_id' and by 'status_id' (worst result at the end)
        # Comment sort by status_id due to issue with pytest-rerun failures,
        # for details refer to issue https://github.com/allankp/pytest-testrail/issues/100
        # self.results.sort(key=itemgetter('status_id'))
        results.sort(key=itemgetter('case_id'))

        # Manage case of "blocked" testcases
        if self.testrail_data.publish_blocked is False:
            print('[{}] Option "Don\'t publish blocked testcases" activated'.format(TESTRAIL_PREFIX))
            blocked_tests_list = [
                test.get('case_id') for test in self.get_tests(testrun_id)
                if test.get('status_id') == TESTRAIL_TEST_STATUS["blocked"]
            ]
            print('[{}] Blocked testcases excluded: {}'.format(TESTRAIL_PREFIX,
                                                               ', '.join(str(elt) for elt in blocked_tests_list)))
            results = [result for result in results if result.get('case_id') not in blocked_tests_list]

        # prompt enabling include all test cases from test suite when creating test run
        if self.testrail_data.include_all:
            print('[{}] Option "Include all testcases from test suite for test run" activated'.format(TESTRAIL_PREFIX))

        # Publish results
        chunks = []
        data = {'results': []}
        for result in results:
            entry = {'status_id': result['status_id'], 'case_id': result['case_id'], 'defects': result['defects']}
            if self.testrail_data.version:
                entry['version'] = self.testrail_data.version
            comment = result.get('comment', '')
            test_parametrize = result.get('test_parametrize', '')
            test_comments = result.get('test_comments', [])
            entry['comment'] = u''
            if test_parametrize:
                entry['comment'] += u"# Test parametrize: #\n"
                entry['comment'] += str(test_parametrize) + u'\n\n'
            if test_comments:
                entry['comment'] += u"# Test comments: #\n"
                entry['comment'] += u'\n'.join(test_comments) + u'\n\n'
            if comment and result.get('status_id') != 1:
                # Indent text to avoid string formatting by TestRail. Limit size of comment.
                entry['comment'] += u"# Pytest result: #\n"
                entry['comment'] += u'Log truncated\n...\n' if len(str(comment)) > COMMENT_SIZE_LIMIT else u''
                entry['comment'] += u"    " + converter(str(comment), "utf-8")[-COMMENT_SIZE_LIMIT:].replace('\n',
                                                                                                             '\n    ')  # noqa
            if self.testrail_data.custom_comment:
                entry['comment'] += self.testrail_data.custom_comment + '\n'
            duration = result.get('duration')
            if duration:
                duration = 1 if (duration < 1) else int(round(duration))  # TestRail API doesn't manage milliseconds
                entry['elapsed'] = str(duration) + 's'
            data['results'].append(entry)

            # report data into chunks
            if sys.getsizeof(data.__str__()) > 512 * 1024:
                chunks.append({'results': data['results']})
                data['results'] = []

        chunks.append({'results': data['results']})

        for chunk in chunks:
            response = self.testrail_data.client.send_post(
                ADD_RESULTS_URL.format(testrun_id),
                chunk,
                cert_check=self.testrail_data.cert_check
            )
            error = self.testrail_data.client.get_error(response)
            if error:
                print('[{}] Info: Testcases not published for following reason: "{}"'.format(TESTRAIL_PREFIX, error))

    def publish_results(self, testrail_data: TestRailModel = None, results: list = None):
        print('[{}] Start publishing'.format(TESTRAIL_PREFIX))

        if results:
            results, tests_list = filter_publish_results(results, self.testrail_data.diff_case_ids)
            print('[{}] Testcases to publish: {}'.format(TESTRAIL_PREFIX, ', '.join(set(tests_list))))

            if self.testrail_data.diff_case_ids:
                print(f"[{TESTRAIL_PREFIX}] Not found following testcases in suiteID={self.testrail_data.suite_id}")
                print(f"[{TESTRAIL_PREFIX}] Testcases will be ignored: {self.testrail_data.diff_case_ids}")

            results_by_run = defaultdict(list)
            if self.testrail_data.testrun_id:
                test_suite = list(self.testrail_data.plan_entry_storage.keys())[0]
                for result in results:
                    if str(result['case_id']) in tests_list:
                        if int(result['suite_id']) == int(test_suite):
                            results_by_run[self.testrail_data.plan_entry_storage[result['suite_id']]['testrun_id']].append(
                                result)
                self._add_results(self.testrail_data.testrun_id, results_by_run.get(self.testrail_data.testrun_id))
            else:
                for result in results:
                    if str(result['case_id']) in tests_list:
                        results_by_run[self.testrail_data.plan_entry_storage[result['suite_id']]['testrun_id']].append(
                            result)
                for run_id, result in results_by_run.items():
                    self._add_results(run_id, result)
        else:
            print('[{}] No data published'.format(TESTRAIL_PREFIX))

        if self.testrail_data.close_on_complete and self.testrail_data.testrun_id:
            self.close_test_run(self.testrail_data.testrun_id)
        elif self.testrail_data.close_on_complete and self.testrail_data.testplan_id:
            self.close_test_plan(self.testrail_data.testplan_id)
        print('[{}] End publishing'.format(TESTRAIL_PREFIX))

        if self.testrail_data.testplan_id:
            print('[{}] Test Plan ID: {}'.format(TESTRAIL_PREFIX, self.testrail_data.testplan_id))
            print('[{}] Test Plan URL: {}/index.php?/plans/view/{}'.format(
                TESTRAIL_PREFIX, self.testrail_data.tr_url, self.testrail_data.testplan_id)
            )
        if self.testrail_data.testrun_id:
            print('[{}] Test Run ID: {}'.format(TESTRAIL_PREFIX, self.testrail_data.testrun_id))
            print('[{}] Test Run URL: {}/index.php?/runs/view/{}'.format(
                TESTRAIL_PREFIX, self.testrail_data.tr_url, self.testrail_data.testrun_id)
            )

    def create_test_run(self, assign_user_id, project_id, suite_id, include_all,
                        testrun_name, tr_keys, milestone_id, description=''):
        """
        Create testrun with ids collected from markers.

        :param tr_keys: collected testrail ids.
        """
        data = {
            'suite_id': suite_id,
            'name': testrun_name,
            'description': description,
            'assignedto_id': assign_user_id,
            'include_all': include_all,
            'case_ids': tr_keys,
            'milestone_id': milestone_id,
        }

        response = self.testrail_data.client.send_post(
            ADD_TESTRUN_URL.format(project_id),
            data,
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to create testrun: "{}"'.format(TESTRAIL_PREFIX, error))
            return 0
        else:
            self.testrail_data.plan_entry_storage[suite_id] = {"testplan_entry_id": None,
                                                               "testrun_id": response['id'],
                                                               "case_ids": tr_keys}
            print('[{}] New testrun created with name "{}" and ID={}'.format(TESTRAIL_PREFIX,
                                                                             testrun_name,
                                                                             self.testrail_data.plan_entry_storage[
                                                                                 suite_id]["testrun_id"]))
            return self.testrail_data.testrun_id

    def create_plan_entry(self, suite_id, testrun_name, assign_user_id, plan_id, include_all, tr_keys, description=''):
        data = {
            'suite_id': suite_id,
            'name': testrun_name,
            'description': description,
            'assignedto_id': assign_user_id,
            'include_all': include_all,
            'case_ids': tr_keys
        }

        response = self.testrail_data.client.send_post(
            ADD_TESTPLAN_ENTRY_URL.format(plan_id),
            data,
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to create testplan entry: "{}"'.format(TESTRAIL_PREFIX, error))
            return 0
        else:
            self.testrail_data.plan_entry_storage[suite_id] = {"testplan_entry_id": response['id'],
                                                               "testrun_id": response['runs'][0]['id'],
                                                               "case_ids": tr_keys}
            print('[{}] New TestPlan entry created with name "{}" and ID={}, entry_id={}'
                  .format(TESTRAIL_PREFIX,
                          testrun_name,
                          self.testrail_data.plan_entry_storage[suite_id]["testrun_id"],
                          self.testrail_data.plan_entry_storage[suite_id]["testplan_entry_id"]))

            return self.testrail_data.plan_entry_storage[suite_id]["testrun_id"]

    def create_plan(self, project_id, plan_name, milestone_id, description=''):
        data = {
            'name': plan_name,
            'description': description,
            'milestone_id': milestone_id,
        }

        response = self.testrail_data.client.send_post(
            ADD_TESTPLAN_URL.format(project_id),
            data,
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to create test plan: "{}"'.format(TESTRAIL_PREFIX, error))
            return 0
        else:
            self.testrail_data.testplan_id = response['id']
            print('[{}] New test plan created with name "{}" and ID={}'.format(TESTRAIL_PREFIX,
                                                                               plan_name,
                                                                               self.testrail_data.testplan_id))
            return self.testrail_data.testplan_id

    def update_testrun(self, testrun_id: int, tr_keys: list, suite_id: int, save_previous: bool = True) -> None:
        """
        Updates an existing test run
        :param testrun_id: testrun id
        :param tr_keys: collected testrail ids
        :param suite_id:
        :param save_previous: collected testrail ids
        """
        current_tests = []
        if save_previous:
            current_tests = get_case_list(self.get_tests(run_id=testrun_id))

        data = {
            'case_ids': list(set(tr_keys + current_tests)),
            'include_all': self.testrail_data.include_all
        }

        response = self.testrail_data.client.send_post(
            UPDATE_RUN_URL.format(testrun_id),
            data,
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        self.testrail_data.plan_entry_storage[suite_id] = {"testplan_entry_id": None,
                                                           "testrun_id": testrun_id,
                                                           "case_ids": list(set(tr_keys + current_tests))}
        if error:
            print('[{}] Failed to update testrun: "{}"'.format(TESTRAIL_PREFIX, error))
        else:
            print('[{}] Testrun updated with name "{}" and ID={}'.format(TESTRAIL_PREFIX,
                                                                         self.testrail_data.testrun_name,
                                                                         testrun_id))

    def update_testplan_entry(self, plan_id: int, entry_id: str, run_id: int, tr_keys: list, suite_id: int,
                              save_previous: bool = True) -> None:
        current_tests = []

        if save_previous:
            current_tests = get_case_list(self.get_tests(run_id=run_id))

        data = {
            'case_ids': list(set(tr_keys + current_tests)),
            'include_all': self.testrail_data.include_all
        }

        response = self.testrail_data.client.send_post(
            UPDATE_TESTPLAN_ENTRY.format(plan_id, entry_id),
            data,
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        self.testrail_data.plan_entry_storage[suite_id] = {"testplan_entry_id": entry_id,
                                                           "testrun_id": run_id,
                                                           "case_ids": list(set(tr_keys + current_tests))}
        if error:
            print('[{}] Failed to update testrun: "{}"'.format(TESTRAIL_PREFIX, error))
        else:
            print('[{}] Testrun updated with name "{}" and ID={}, entry_id={}'.format(TESTRAIL_PREFIX,
                                                                                      self.testrail_data.testrun_name,
                                                                                      run_id,
                                                                                      entry_id))

    def is_testrun_available(self):
        """
        Ask if testrun is available in TestRail.

        :return: True if testrun exists AND is open
        """
        response = self.testrail_data.client.send_get(
            GET_TESTRUN_URL.format(self.testrail_data.testrun_id),
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to retrieve testrun: "{}"'.format(TESTRAIL_PREFIX, error))
            return False

        return response['is_completed'] is False

    def close_test_run(self, testrun_id):
        """
        Closes testrun.

        """
        response = self.testrail_data.client.send_post(
            CLOSE_TESTRUN_URL.format(testrun_id),
            data={},
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to close test run: "{}"'.format(TESTRAIL_PREFIX, error))
        else:
            print('[{}] Test run with ID={} was closed'.format(TESTRAIL_PREFIX, self.testrail_data.testrun_id))

    def close_test_plan(self, testplan_id: int):
        """
        Closes testrun.

        """
        response = self.testrail_data.client.send_post(
            CLOSE_TESTPLAN_URL.format(testplan_id),
            data={},
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to close test plan: "{}"'.format(TESTRAIL_PREFIX, error))
        else:
            print('[{}] Test plan with ID={} was closed'.format(TESTRAIL_PREFIX, self.testrail_data.testplan_id))

    def get_cases(self, project_id, suit_id):
        """
        :return: the list of tests containing in a testrun.
        """
        response = self.testrail_data.client.send_get(
            GET_TESTCASES_URL.format(project_id, suit_id),
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print(f'[{TESTRAIL_PREFIX}] Failed to get tests: "{error} for suite: {suit_id}"')
            return []
        return response

    def get_suites(self, project_id):
        """
        :return: The list of suite_ids
        """
        response = self.testrail_data.client.send_get(
            GET_SUITES_URL.format(project_id),
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print(f'[{TESTRAIL_PREFIX}] Failed to get suites: "{error} for project id: {project_id}"')
            return []
        return response

    def get_tests(self, run_id):
        """
        :return: the list of tests containing in a testrun.

        """
        response = self.testrail_data.client.send_get(
            GET_TESTS_URL.format(run_id),
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print(f'[{TESTRAIL_PREFIX}] Failed to get tests: "{error}"')
            return []
        return response

    def get_plan(self, plan_id):
        """
        :return: a list of available testruns associated to a testplan in TestRail.

        """
        response = self.testrail_data.client.send_get(
            GET_TESTPLAN_URL.format(plan_id),
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print(f'[{TESTRAIL_PREFIX}] Failed to retrieve testplan: "{error}"')
        return response

    def get_run(self, run_id) -> dict:
        """
        Return info
        """
        response = self.testrail_data.client.send_get(
            GET_TESTRUN_URL.format(run_id),
            cert_check=self.testrail_data.cert_check
        )
        error = self.testrail_data.client.get_error(response)
        if error:
            print(f'[{TESTRAIL_PREFIX}] Failed to retrieve testrun: "{error}"')
        return response

    def get_testplan_entry_id(self, plan_id, run_id):
        """
        :return: a list of available testruns associated to a testplan in TestRail.

        """
        response = self.get_plan(plan_id)
        for entry in response['entries']:
            for run in entry['runs']:
                if str(run['id']) == run_id:
                    self.testrail_data.testplan_entry_id = entry['id']
                    return self.testrail_data.testplan_entry_id
        return None

    def get_available_testruns(self, plan_id):
        """
        :return: a list of available testruns associated to a testplan in TestRail.

        """
        testruns_list = []
        response = self.get_plan(plan_id)
        for entry in response['entries']:
            for run in entry['runs']:
                if not run['is_completed']:
                    testruns_list.append(run['id'])
        return testruns_list

    def is_testplan_available(self):
        """
        Ask if testplan is available in TestRail.

        :return: True if testplan exists AND is open
        """
        response = self.get_plan(self.testrail_data.testplan_id)
        error = self.testrail_data.client.get_error(response)
        if error:
            print('[{}] Failed to retrieve testplan: "{}"'.format(TESTRAIL_PREFIX, error))
            return False

        return response['is_completed'] is False
