import pytest
import pytz
from datetime import datetime

import src.shared.utils as shared_utils
import src.shared.types as shared_types


def test_is_nonempty_str():
    ok = shared_utils.is_nonempty_str('hi')
    assert(ok is True)
    not_ok = shared_utils.is_nonempty_str('')
    assert(not_ok is False)
    not_ok = shared_utils.is_nonempty_str(5)
    assert(not_ok is False)


def test_alpha2_codes():
    ok = shared_types.Alpha2('US')
    assert(str(ok) == 'US')
    with pytest.raises(Exception):
        shared_types.Alpha2('blah')
    with pytest.raises(Exception):
        shared_types.Alpha2()
    with pytest.raises(Exception):
        shared_types.Alpha2(5)


def test_to_utc():
    tz = pytz.timezone("US/Pacific")
    t = tz.localize(datetime(2021, 5, 27, 21, 40, 17, 486566))
    t_utc = shared_utils.to_utc(t)
    assert(t_utc.hour == 4)
