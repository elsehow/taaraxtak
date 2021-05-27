from datetime import datetime
import pytz

def to_utc (t: datetime) -> datetime:
    return t.astimezone(pytz.utc)

# TODO make this dry!
def is_nonempty_str(my_str: str) -> bool:
    return (type(my_str) == str) & (len(my_str) > 0)
