from dataclasses import dataclass

@dataclasses
class TestRailModel:
    assign_user_id: int
    cert_check: bool = False
    client = None
    project_id: int = None
    # results: list = None
    suite_id = None
    include_all = None
    testrun_name = None
    testrun_description = None
    testrun_id = None
    testplan_id = None
    version = None
    close_on_complete = None
    publish_blocked = None
    skip_missing = None
    milestone_id = None
    custom_comment = None
    test_run_flag = False
    tr_keys = []
    config = None
