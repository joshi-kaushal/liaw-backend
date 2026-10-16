import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone, tzinfo

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


def get_timezone(tz_name: str | None = None) -> tzinfo:
    """
    Returns a tzinfo object for the given timezone name.
    Safely falls back to fixed offsets if IANA tzdata is unavailable on Windows.
    """
    name = tz_name or "Asia/Kolkata"
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:
            pass

    if name == "Asia/Kolkata":
        return timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")
    return timezone.utc

# ── Regex building blocks ───────────────────────────────────────────────────

MONTH = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)

WEEKDAY = r"mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?"

# Time parsing regexes
TIME_RE = re.compile(r"^(\d{1,2})(?:[:.](\d{1,2}))?\s*(am|pm)?$", re.IGNORECASE)
TRAILING_TIME_RE = re.compile(
    r"(?:\s+at\s+)?(\d{1,2}(?:[:.]\d{1,2})?\s*(?:am|pm)|(?:[01]?\d|2[0-3]):[0-5]\d|\d{1,2}\.\d{2})$",
    re.IGNORECASE,
)

# Durations
DURATION_TOKEN_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(minutes|minute|mins|min|m|hours|hour|hrs|hr|h|days|day|d|weeks?|wks?|wk|w)",
    re.IGNORECASE,
)
DURATION_PREFIX_RE = re.compile(
    r"^(?:in\s+)?(\d+(?:\.\d+)?)\s*(minutes|minute|mins|min|m|hours|hour|hrs|hr|h|days|day|d|weeks?|wks?|wk|w)\b",
    re.IGNORECASE,
)

UNIT_TO_MINUTES: dict[str, float] = {
    "minutes": 1,
    "minute": 1,
    "mins": 1,
    "min": 1,
    "m": 1,
    "hours": 60,
    "hour": 60,
    "hrs": 60,
    "hr": 60,
    "h": 60,
    "days": 1440,
    "day": 1440,
    "d": 1440,
    "weeks": 10080,
    "week": 10080,
    "wks": 10080,
    "wk": 10080,
    "w": 10080,
}

# Relative date keywords
KEYWORD_RE = re.compile(r"^(today|tonight|tomorrow|tmrw)\b", re.IGNORECASE)
NEXT_RELATIVE_RE = re.compile(r"^next\s+(day|week|month|year)\b", re.IGNORECASE)
WEEKDAY_RE = re.compile(
    rf"^(?:(this|next)\s+)?(mon|tue|wed|thu|fri|sat|sun)\w*\b", re.IGNORECASE
)

# Explicit dates
NAMED_DATE_RE = re.compile(
    rf"^(\d{{1,2}})\s+({MONTH})(?:\s+(\d{{2,4}}))?\b", re.IGNORECASE
)
NUMERIC_DMY_RE = re.compile(r"^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", re.IGNORECASE)
NUMERIC_YMD_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})", re.IGNORECASE)

# Bare times
BARE_TIME_RE = re.compile(
    r"^(\d{1,2})(?:[:.](\d{1,2}))?\s*(am|pm)$|^(\d{1,2}):(\d{2})$|^(\d{1,2})\.(\d{2})$",
    re.IGNORECASE,
)

# ── Combined WHEN pattern for matching front-loaded datetimes ─────────────────

WHEN_PATTERN = (
    r"(?:"
    # date / duration / weekday + optional time
    rf"(?:(?:in\s+)?(?:\d+\s*(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|w|wk|wks|week|weeks)|"
    rf"(?:today|tomorrow|tmrw|tonight|next\s+(?:day|week|month|year))|(?:this\s+|next\s+)?(?:{WEEKDAY})|"
    rf"(?:\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?|\d{{4}}-\d{{1,2}}-\d{{1,2}})|"
    rf"(?:\d{{1,2}}\s+(?:{MONTH})(?:\s+\d{{2,4}})?))\s+(?:at\s+)?(?:\d{{1,2}}(?:[:.]\d{{1,2}})?\s*(?:am|pm)|(?:[01]?\d|2[0-3]):[0-5]\d|\d{{1,2}}\.\d{{2}}))"
    r"|"
    # bare relative
    r"(?:(?:in\s+)?(?:\d+\s*(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|w|wk|wks|week|weeks))|"
    r"(?:today|tomorrow|tmrw|tonight|next\s+(?:day|week|month|year)))"
    r"|"
    # bare weekday
    rf"(?:(?:this\s+|next\s+)?(?:{WEEKDAY}))"
    r"|"
    # bare date (named or numeric)
    rf"(?:(?:\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?|\d{{4}}-\d{{1,2}}-\d{{1,2}})|(?:\d{{1,2}}\s+(?:{MONTH})(?:\s+\d{{2,4}})?))"
    r"|"
    # bare time
    r"(?:\d{1,2}(?:[:.]\d{1,2})?\s*(?:am|pm)|(?:[01]?\d|2[0-3]):[0-5]\d|\d{1,2}\.\d{2})"
    r")"
)

ADD_COMMAND_RE = re.compile(rf"^(?:/add\s+)?({WHEN_PATTERN})\s+(.+)$", re.IGNORECASE)


@dataclass
class ParsedSchedule:
    due_date: date
    due_time: str | None  # "HH:MM" (24-hour) or None
    has_explicit_time: bool


# ── Parsing Helpers ──────────────────────────────────────────────────────────


def parse_time(raw: str) -> tuple[int, int] | None:
    """Parse '10am', '1:30pm', '1.30pm', '13:30', '10.12' into (hour, minute)."""
    match = TIME_RE.match(raw.strip())
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    meridiem = (match.group(3) or "").lower()

    if meridiem == "am":
        hour = 0 if hour == 12 else hour
    elif meridiem == "pm":
        hour = 12 if hour == 12 else hour + 12

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    return hour, minute


def extract_trailing_time(input_str: str) -> tuple[int, int] | None:
    """Extract trailing time suffix like 'tomorrow 10pm', '25 sep at 14:30'."""
    m = TRAILING_TIME_RE.search(input_str.strip())
    if not m:
        return None
    return parse_time(m.group(1))


def strip_trailing_time(input_str: str) -> str:
    """Remove trailing time pattern from string to extract base date part."""
    return TRAILING_TIME_RE.sub("", input_str.strip()).strip()


def parse_duration_to_minutes(raw: str) -> float | None:
    """Sums up duration tokens like '1h 30m' or '2 hours' into minutes."""
    if not raw or not raw.strip():
        return None

    total = 0.0
    found = False
    for match in DURATION_TOKEN_RE.finditer(raw):
        val = float(match.group(1))
        unit = match.group(2).lower()
        mult = UNIT_TO_MINUTES.get(unit)
        if mult is None:
            return None
        total += val * mult
        found = True

    return total if found and total > 0 else None


def parse_weekday_index(name: str) -> int:
    """
    Returns Python weekday index (0=Mon, 1=Tue, ..., 6=Sun), or -1 if invalid.
    """
    low = name.lower()
    if low.startswith("mon"):
        return 0
    if low.startswith("tu"):
        return 1
    if low.startswith("wed"):
        return 2
    if low.startswith("th"):
        return 3
    if low.startswith("fri"):
        return 4
    if low.startswith("sat"):
        return 5
    if low.startswith("sun"):
        return 6
    return -1


def parse_month_index(name: str) -> int:
    """Returns 1-based month index (1=Jan ... 12=Dec), or -1 if invalid."""
    low = name.lower()[:3]
    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    return months.get(low, -1)


def parse_year(raw: str, current_year: int) -> int:
    val = int(raw)
    if val < 100:
        return 2000 + val
    return val


def add_months_to_date(source_date: date, months: int) -> date:
    """Adds months to a date, clamping to the last valid day of that month."""
    new_month = source_date.month + months
    new_year = source_date.year + (new_month - 1) // 12
    new_month = ((new_month - 1) % 12) + 1
    max_day = calendar.monthrange(new_year, new_month)[1]
    return date(new_year, new_month, min(source_date.day, max_day))


# ── Strategies for Parsing <when> ───────────────────────────────────────────


def try_relative_duration(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None] | None:
    m = DURATION_PREFIX_RE.match(input_str.strip())
    if not m:
        return None

    duration_str = f"{m.group(1)} {m.group(2)}"
    mins = parse_duration_to_minutes(duration_str)
    if mins is None:
        return None

    target = now + timedelta(minutes=mins)
    return target.date(), (target.hour, target.minute)


def try_keyword(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None, bool] | None:
    m = KEYWORD_RE.match(input_str.strip())
    if not m:
        return None

    kw = m.group(1).lower()
    time_part = extract_trailing_time(input_str)
    has_time = time_part is not None

    if kw == "today":
        target_date = now.date()
        if time_part:
            # If specified time already passed today, shift to tomorrow
            if (time_part[0], time_part[1]) <= (now.hour, now.minute):
                target_date = target_date + timedelta(days=1)
        return target_date, time_part, has_time

    if kw == "tonight":
        # Tonight defaults to 21:00 (9:00 PM) if not specified
        chosen_time = time_part if time_part else (21, 0)
        target_date = now.date()
        if (chosen_time[0], chosen_time[1]) <= (now.hour, now.minute):
            target_date = target_date + timedelta(days=1)
        return target_date, chosen_time, True

    # tomorrow / tmrw
    target_date = now.date() + timedelta(days=1)
    return target_date, time_part, has_time


def try_next_relative(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None, bool] | None:
    m = NEXT_RELATIVE_RE.match(input_str.strip())
    if not m:
        return None

    unit = m.group(1).lower()
    time_part = extract_trailing_time(input_str)
    has_time = time_part is not None

    if unit == "day":
        return now.date() + timedelta(days=1), time_part, has_time

    if unit == "week":
        # Next Monday
        current_w = now.weekday()  # Mon=0 ... Sun=6
        days_to_mon = (7 - current_w) % 7 or 7
        return now.date() + timedelta(days=days_to_mon), time_part, has_time

    if unit == "month":
        return add_months_to_date(now.date(), 1), time_part, has_time

    # next year
    target_date = date(now.year + 1, now.month, now.day)
    return target_date, time_part, has_time


def try_weekday(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None, bool] | None:
    m = WEEKDAY_RE.match(input_str.strip())
    if not m:
        return None

    prefix = (m.group(1) or "").lower()
    target_w = parse_weekday_index(m.group(2))
    if target_w == -1:
        return None

    time_part = extract_trailing_time(input_str)
    has_time = time_part is not None
    current_w = now.weekday()
    days_until = (target_w - current_w + 7) % 7

    if prefix == "this":
        if days_until == 0:
            # If same day and time already passed, shift to next week
            if time_part and (time_part[0], time_part[1]) <= (now.hour, now.minute):
                days_until = 7
    elif days_until == 0:
        # Bare weekday or "next" -> always next occurrence, never today
        days_until = 7

    target_date = now.date() + timedelta(days=days_until)
    return target_date, time_part, has_time


def try_named_date(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None, bool] | None:
    m = NAMED_DATE_RE.match(input_str.strip())
    if not m:
        return None

    day = int(m.group(1))
    month = parse_month_index(m.group(2))
    if month == -1 or day < 1 or day > 31:
        return None

    time_part = extract_trailing_time(input_str)
    has_time = time_part is not None

    year = parse_year(m.group(3), now.year) if m.group(3) else now.year
    try:
        target_date = date(year, month, day)
    except ValueError:
        return None

    # If no year was given and the date has already passed, bump to next year
    if not m.group(3):
        if target_date < now.date() or (
            target_date == now.date()
            and time_part
            and (time_part[0], time_part[1]) <= (now.hour, now.minute)
        ):
            target_date = date(year + 1, month, day)

    return target_date, time_part, has_time


def try_numeric_date(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None, bool] | None:
    time_part = extract_trailing_time(input_str)
    has_time = time_part is not None
    date_str = strip_trailing_time(input_str)

    # YMD: 2026-09-25
    ymd = NUMERIC_YMD_RE.match(date_str)
    if ymd:
        try:
            target_date = date(int(ymd.group(1)), int(ymd.group(2)), int(ymd.group(3)))
            return target_date, time_part, has_time
        except ValueError:
            return None

    # DMY: 25/09, 25/09/2026, 25-09
    dmy = NUMERIC_DMY_RE.match(date_str)
    if dmy:
        day = int(dmy.group(1))
        month = int(dmy.group(2))
        year = parse_year(dmy.group(3), now.year) if dmy.group(3) else now.year
        try:
            target_date = date(year, month, day)
        except ValueError:
            return None

        if not dmy.group(3):
            if target_date < now.date() or (
                target_date == now.date()
                and time_part
                and (time_part[0], time_part[1]) <= (now.hour, now.minute)
            ):
                target_date = date(year + 1, month, day)
        return target_date, time_part, has_time

    return None


def try_bare_time(
    input_str: str, now: datetime
) -> tuple[date, tuple[int, int] | None, bool] | None:
    time_part = parse_time(input_str.strip())
    if not time_part:
        return None

    target_date = now.date()
    # If time has passed today, shift to tomorrow
    if (time_part[0], time_part[1]) <= (now.hour, now.minute):
        target_date = target_date + timedelta(days=1)

    return target_date, time_part, True


# ── Core Parser ──────────────────────────────────────────────────────────────


def parse_when(when_str: str, tz: tzinfo | None = None) -> ParsedSchedule | None:
    """
    Parses a when string into a ParsedSchedule or None if unrecognized.
    """
    actual_tz = tz or get_timezone()
    now = datetime.now(actual_tz)
    trimmed = when_str.strip()

    # 1. Relative duration (in 30 mins, 2 hours, 7d)
    rel_res = try_relative_duration(trimmed, now)
    if rel_res:
        target_date, time_tuple = rel_res
        time_str = f"{time_tuple[0]:02d}:{time_tuple[1]:02d}" if time_tuple else None
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=True
        )

    # 2. Keyword (today, tonight, tomorrow, tmrw)
    kw_res = try_keyword(trimmed, now)
    if kw_res:
        target_date, time_tuple, has_time = kw_res
        time_str = (
            f"{time_tuple[0]:02d}:{time_tuple[1]:02d}"
            if time_tuple and has_time
            else None
        )
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=has_time
        )

    # 3. Next-relative (next day, next week, next month, next year)
    next_res = try_next_relative(trimmed, now)
    if next_res:
        target_date, time_tuple, has_time = next_res
        time_str = (
            f"{time_tuple[0]:02d}:{time_tuple[1]:02d}"
            if time_tuple and has_time
            else None
        )
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=has_time
        )

    # 4. Weekday (this friday, next monday, mon 10am)
    w_res = try_weekday(trimmed, now)
    if w_res:
        target_date, time_tuple, has_time = w_res
        time_str = (
            f"{time_tuple[0]:02d}:{time_tuple[1]:02d}"
            if time_tuple and has_time
            else None
        )
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=has_time
        )

    # 5. Named date (25 sep, 25 sep 2026, 25 sep at 14:30)
    nd_res = try_named_date(trimmed, now)
    if nd_res:
        target_date, time_tuple, has_time = nd_res
        time_str = (
            f"{time_tuple[0]:02d}:{time_tuple[1]:02d}"
            if time_tuple and has_time
            else None
        )
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=has_time
        )

    # 6. Numeric date (25/09, 25/09/2026, 2026-09-25)
    num_res = try_numeric_date(trimmed, now)
    if num_res:
        target_date, time_tuple, has_time = num_res
        time_str = (
            f"{time_tuple[0]:02d}:{time_tuple[1]:02d}"
            if time_tuple and has_time
            else None
        )
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=has_time
        )

    # 7. Bare time (10am, 1:30pm, 13:30, 10.12)
    bt_res = try_bare_time(trimmed, now)
    if bt_res:
        target_date, time_tuple, has_time = bt_res
        time_str = (
            f"{time_tuple[0]:02d}:{time_tuple[1]:02d}"
            if time_tuple and has_time
            else None
        )
        return ParsedSchedule(
            due_date=target_date, due_time=time_str, has_explicit_time=has_time
        )

    return None


def parse_add_input(
    raw_input: str, tz: tzinfo | None = None
) -> tuple[ParsedSchedule, str]:
    """
    Parses input for the /add command or plain-text task creation.
    - If `raw_input` starts with a recognized `<when>` pattern and is followed by text:
      extracts `<when>` and `<task_title>`, returning (schedule, task_title).
    - If no `<when>` pattern is matched (or if there is no task title after it):
      defaults to today with due_time=None and returns (today_schedule, raw_input.strip()).
    """
    actual_tz = tz or get_timezone()
    cleaned = raw_input.strip()
    if cleaned.lower().startswith("/add"):
        cleaned = cleaned[4:].strip()

    match = ADD_COMMAND_RE.match(cleaned)

    if match:
        when_str = match.group(1).strip()
        task_title = match.group(2).strip()

        if task_title:
            schedule = parse_when(when_str, actual_tz)
            if schedule:
                return schedule, task_title

    # Fallback: No recognized <when>, so add for today with due_time=None
    now = datetime.now(actual_tz)
    default_schedule = ParsedSchedule(
        due_date=now.date(), due_time=None, has_explicit_time=False
    )
    return default_schedule, cleaned


def format_confirmation_message(
    title: str, schedule: ParsedSchedule, tz: tzinfo | None = None
) -> str:
    """
    Builds a clean user-facing confirmation message:
    - If timed: '✅ Added: *<title>* for tomorrow at 5:00 PM'
    - If date-only: '✅ Added: *<title>* for tomorrow' or '✅ Added: *<title>* for Mon, 20 Oct'
    - If today (default): '✅ Added: *<title>*'
    """
    actual_tz = tz or get_timezone()
    now = datetime.now(actual_tz)
    today = now.date()
    tomorrow = today + timedelta(days=1)

    time_str = ""
    if schedule.due_time:
        try:
            t = datetime.strptime(schedule.due_time, "%H:%M")
            # e.g., '5:00 PM'
            time_str = t.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            time_str = schedule.due_time

    if schedule.due_date == today:
        if schedule.has_explicit_time and time_str:
            return f"✅ Added: *{title}* for today at {time_str}"
        return f"✅ Added: *{title}*"

    if schedule.due_date == tomorrow:
        if schedule.has_explicit_time and time_str:
            return f"✅ Added: *{title}* for tomorrow at {time_str}"
        return f"✅ Added: *{title}* for tomorrow"

    # Other future date
    date_display = schedule.due_date.strftime("%a, %d %b")
    if schedule.has_explicit_time and time_str:
        return f"✅ Added: *{title}* for {date_display} at {time_str}"
    return f"✅ Added: *{title}* for {date_display}"
