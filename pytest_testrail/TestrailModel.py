from dataclasses import dataclass, field


@dataclass
class TestRailModel:
    assign_user_id: int
    user_email: str = None
    user_password: str = None
    tr_url: str = None
    cert_check: bool = False
    client: any = None
    project_id: int = None
    results: list = None
    suite_id: int = None
    include_all: bool = None
    testrun_name: str = None
    testrun_description: str = None
    testrun_id: int = None
    testplan_entry_id: str = None
    testplan_id: int = None
    testplan_name: int = None
    testplan_description: str = None
    version: str = None
    close_on_complete: bool = None
    publish_blocked: bool = None
    skip_missing: bool = None
    milestone_id: int = None
    custom_comment: str = None
    test_run_flag: bool = False
    tr_keys: list = None
    actual_suites_with_case_ids: dict = None
    plan_entry_storage: dict = None
    diff_case_ids: list = None
    available_suite_ids: dict = None
    test_comments: list = field(default_factory=[])


@dataclass()
class Store:
    pass
