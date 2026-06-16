import pytest

from edvibe_bot.main import build_run_config
from edvibe_bot.runner import RunConfig


def test_defaults_minimal_args():
    cfg = build_run_config(["--mode", "dry_run"])
    assert isinstance(cfg, RunConfig)
    assert cfg.mode == "dry_run"
    assert cfg.student_filter is None
    assert cfg.max_students is None
    assert cfg.max_lessons is None
    assert cfg.headed is False
    assert cfg.confidence_threshold == 0.6


def test_mode_passthrough_full_auto():
    cfg = build_run_config(["--mode", "full_auto"])
    assert cfg.mode == "full_auto"


def test_mode_passthrough_review():
    cfg = build_run_config(["--mode", "review"])
    assert cfg.mode == "review"


def test_invalid_mode_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "bogus"])


def test_repeated_student_becomes_list():
    cfg = build_run_config(
        ["--mode", "dry_run", "--student", "Анель", "--student", "Bob"]
    )
    assert cfg.student_filter == ["Анель", "Bob"]


def test_single_student_is_one_element_list():
    cfg = build_run_config(["--mode", "dry_run", "--student", "Анель"])
    assert cfg.student_filter == ["Анель"]


def test_caps_parse_as_ints():
    cfg = build_run_config(
        ["--mode", "dry_run", "--max-students", "3", "--max-lessons", "1"]
    )
    assert cfg.max_students == 3
    assert isinstance(cfg.max_students, int)
    assert cfg.max_lessons == 1
    assert isinstance(cfg.max_lessons, int)


def test_non_integer_cap_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run", "--max-students", "lots"])


def test_headed_flag_sets_true():
    cfg = build_run_config(["--mode", "dry_run", "--headed"])
    assert cfg.headed is True


def test_confidence_omitted_uses_passed_default():
    cfg = build_run_config(["--mode", "dry_run"], default_confidence=0.42)
    assert cfg.confidence_threshold == 0.42


def test_confidence_override_beats_default():
    cfg = build_run_config(
        ["--mode", "dry_run", "--confidence", "0.9"], default_confidence=0.42
    )
    assert cfg.confidence_threshold == 0.9


def test_confidence_zero_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run", "--confidence", "0"])


def test_confidence_above_one_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run", "--confidence", "1.5"])


def test_confidence_exactly_one_is_allowed():
    cfg = build_run_config(["--mode", "dry_run", "--confidence", "1.0"])
    assert cfg.confidence_threshold == 1.0


def test_default_confidence_out_of_range_is_systemexit():
    # A bad resolved default (e.g. misconfigured Settings) must also be rejected.
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run"], default_confidence=0.0)
