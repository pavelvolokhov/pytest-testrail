from dataclasses import dataclass


@dataclass
class TestRailModel:
    assign_user_id: int
    cert_check: bool = False
    # client = None
    project_id: int = None
    # results: list = None
    suite_id: int = None
    include_all: bool = None
    testrun_name: str = None
    testrun_description: str = None
    testrun_id: int = None
    testplan_id: int = None
    version: str = None
    close_on_complete: bool = None
    publish_blocked: bool = None
    skip_missing: bool = None
    milestone_id: int = None
    custom_comment: str = None
    test_run_flag: bool = False
    tr_keys: list = list