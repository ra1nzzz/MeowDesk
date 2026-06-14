"""Tests for ``meowdesk.core.types.AppConfig`` (de)serialisation."""


from meowdesk.core.types import (
    AgentConfig,
    AppConfig,
    CategoryConfig,
    FileAction,
    PeriodConfig,
    PeriodRecord,
    Reminder,
)


def test_scalar_field_names_lists_expected_keys():
    expected = {
        "archive_dir",
        "temp_dir",
        "window_opacity",
        "auto_open_html",
        "screenshot_action",
        "window_position",
        "scale",
    }
    assert set(AppConfig.scalar_field_names()) == expected


def test_container_field_names_lists_expected_keys():
    expected = {"categories", "agent", "reminders", "period"}
    assert set(AppConfig.container_field_names()) == expected


def test_scalar_and_container_names_are_disjoint():
    assert set(AppConfig.scalar_field_names()).isdisjoint(
        set(AppConfig.container_field_names())
    )


def test_to_dict_roundtrips_through_from_dict():
    config = AppConfig(
        archive_dir="/data/file",
        temp_dir="/data/temp",
        window_opacity=0.5,
        auto_open_html=True,
        screenshot_action=FileAction.ARCHIVE,
        window_position=(100, 200),
        scale=0.7,
        categories={
            "文档": CategoryConfig("文档", [".pdf"], FileAction.ARCHIVE),
        },
        agent=AgentConfig(enabled=True, endpoint="http://x", api_key="k"),
        reminders=[Reminder(name="r1", time="09:00")],
        period=PeriodConfig(enabled=True, cycle_days=30, last_period_start="2026-05-01"),
    )
    data = config.to_dict()
    rebuilt = AppConfig.from_dict(data)
    assert rebuilt == config


def test_from_dict_inherits_missing_scalar_fields_from_defaults():
    defaults = AppConfig(archive_dir="/keep/me", scale=0.3)
    rebuilt = AppConfig.from_dict({}, defaults=defaults)
    assert rebuilt.archive_dir == "/keep/me"
    assert rebuilt.scale == 0.3


def test_from_dict_coerces_window_position_to_tuple():
    rebuilt = AppConfig.from_dict({"window_position": [10, 20]})
    assert rebuilt.window_position == (10, 20)


def test_from_dict_normalises_missing_window_position_to_none():
    rebuilt = AppConfig.from_dict({})
    assert rebuilt.window_position is None


def test_from_dict_coerces_screenshot_action_string_to_enum():
    rebuilt = AppConfig.from_dict({"screenshot_action": "archive"})
    assert rebuilt.screenshot_action == FileAction.ARCHIVE


def test_from_dict_merges_categories_with_defaults():
    defaults = AppConfig.get_default()
    # Drop the 文档 category and add a new one
    user_categories = {
        "新分类": {"exts": [".xyz"], "action": "archive"},
    }
    rebuilt = AppConfig.from_dict({"categories": user_categories}, defaults=defaults)
    assert "新分类" in rebuilt.categories
    # The default 文档 should still be there because we merged
    assert "文档" in rebuilt.categories
    assert "截图" in rebuilt.categories


def test_from_dict_recovers_nested_dataclasses():
    rebuilt = AppConfig.from_dict(
        {
            "agent": {"enabled": True, "endpoint": "http://localhost", "timeout": 60},
            "reminders": [{"name": "r", "time": "08:00", "repeat": "每天"}],
            "period": {
                "enabled": True,
                "cycle_days": 30,
                "records": [{"start_date": "2026-01-01", "end_date": "2026-01-05"}],
            },
        }
    )
    assert isinstance(rebuilt.agent, AgentConfig)
    assert rebuilt.agent.enabled is True
    assert rebuilt.agent.timeout == 60
    assert rebuilt.reminders[0].name == "r"
    assert rebuilt.reminders[0].repeat == "每天"
    assert isinstance(rebuilt.period, PeriodConfig)
    assert rebuilt.period.records[0] == PeriodRecord(
        start_date="2026-01-01", end_date="2026-01-05"
    )


def test_to_dict_serialises_window_position_as_list():
    config = AppConfig(window_position=(10, 20))
    data = config.to_dict()
    assert data["window_position"] == [10, 20]


def test_to_dict_serialises_screenshot_action_as_string():
    config = AppConfig(screenshot_action=FileAction.ARCHIVE)
    data = config.to_dict()
    assert data["screenshot_action"] == "archive"


def test_to_dict_with_no_window_position_emits_none():
    config = AppConfig()
    data = config.to_dict()
    assert data["window_position"] is None


def test_from_dict_handles_unknown_keys_gracefully():
    """Forward compatibility: extra fields in a saved config should
    not crash older versions of the app."""

    rebuilt = AppConfig.from_dict({"some_future_key": "value", "archive_dir": "/x"})
    assert rebuilt.archive_dir == "/x"


def test_get_default_provides_categories():
    config = AppConfig.get_default()
    assert "截图" in config.categories
    assert "文档" in config.categories
