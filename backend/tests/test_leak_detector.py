from app.core.leak_detector import detect_answer_leak, normalize


def test_normalize_strips_punct_and_lowercases():
    assert normalize("X = 7 . ") == "x=7"
    assert normalize("结果是 12 ") == "结果是12"


def test_exact_numeric_leak_detected():
    assert detect_answer_leak(response_text="所以答案是 7。", reference_answer="7")


def test_no_leak_when_only_method_mentioned():
    assert not detect_answer_leak(
        response_text="你能先写出方程吗？",
        reference_answer="x=7",
    )


def test_chinese_numeral_leak_detected():
    assert detect_answer_leak(
        response_text="所以 x 等于 三", reference_answer="x=3"
    )


def test_substring_inside_word_not_false_positive():
    # reference is "12", text contains "120" — should NOT count as leak
    assert not detect_answer_leak(
        response_text="如果有 120 个苹果……", reference_answer="12"
    )


def test_multi_value_reference_all_must_appear_for_leak():
    # reference "x=2, y=3" leaks only if both numbers in vicinity
    assert detect_answer_leak(
        response_text="解出 x=2 然后 y=3",
        reference_answer="x=2,y=3",
    )
    assert not detect_answer_leak(
        response_text="想想 x 的值",
        reference_answer="x=2,y=3",
    )
