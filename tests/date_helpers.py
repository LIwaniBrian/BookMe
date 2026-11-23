from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def get_future_monday():
    timezone = ZoneInfo("Africa/Johannesburg")
    now = datetime.now(timezone)

    days_until_monday = (7 - now.weekday()) % 7

    if days_until_monday == 0:
        days_until_monday = 7

    future_monday = now.date() + timedelta(days=days_until_monday)

    return datetime.combine(
        future_monday,
        time(10, 0),
        tzinfo=timezone,
    )
