import pytest

from app.analysis.static_review import review_code


def test_review_code_detects_multiple_risky_patterns_without_echoing_source():
    findings = review_code(
        "value = eval(user_input)\n"
        "subprocess.run(command, shell=True)\n"
        "password = \"example-hardcoded-secret\"\n"
    )

    assert {item["rule_id"] for item in findings} == {"PY001", "PY005", "PY006"}
    assert [item["line"] for item in findings] == [1, 2, 3]
    assert all("example-hardcoded-secret" not in str(item) for item in findings)


def test_review_code_ignores_comment_lines():
    assert review_code("# eval(user_input)\n// exec(untrusted)") == []


@pytest.mark.parametrize("source", ["", "   ", "\n"])
def test_review_code_rejects_empty_source(source):
    with pytest.raises(ValueError, match="vazio"):
        review_code(source)


def test_review_code_rejects_source_over_limit():
    with pytest.raises(ValueError, match="20 000"):
        review_code("x" * 20_001)


def test_review_code_does_not_flag_safe_subprocess_argument_list():
    assert review_code("subprocess.run(['tool', '--version'], check=True)") == []
