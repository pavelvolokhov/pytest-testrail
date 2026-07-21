from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestRailModel:
    assign_user_id: int
    user_email: str | None = None
    user_password: str | None = None
    tr_url: str | None = None
    cert_check: bool = False
    client: Any = None
    project_id: int | None = None
    results: list = field(default_factory=list)
    suite_id: int | None = None
    include_all: bool | None = None
    testrun_name: str | None = None
    testrun_description: str | None = None
    testrun_id: int | None = None
    testplan_entry_id: str | None = None
    testplan_id: int | None = None
    testplan_name: str | None = None
    testplan_description: str | None = None
    version: str | None = None
    close_on_complete: bool | None = None
    publish_blocked: bool | None = None
    skip_missing: bool | None = None
    milestone_id: int | None = None
    custom_comment: str | None = None
    test_run_flag: bool = False
    tr_keys: list = field(default_factory=list)
    actual_suites_with_case_ids: dict = field(default_factory=dict)
    plan_entry_storage: dict = field(default_factory=dict)
    diff_case_ids: list = field(default_factory=list)
    available_suite_ids: dict = field(default_factory=dict)
    test_comments: list = field(default_factory=list)


@dataclass()
class Store:
    pass
