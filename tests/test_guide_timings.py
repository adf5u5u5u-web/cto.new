from dfu_guide.guide import get_schedule


def durations(family: str):
    return [s.duration for s in get_schedule(family)]


def test_6s_schedule():
    d = durations("6s")
    assert d == [8, 10]


def test_7_schedule():
    d = durations("7")
    assert d == [8, 10]


def test_8_schedule_contains_5_and_10():
    d = durations("8")
    assert 5 in d and 10 in d


def test_faceid_schedule_contains_5_and_10():
    d = durations("faceid")
    assert 5 in d and 10 in d
