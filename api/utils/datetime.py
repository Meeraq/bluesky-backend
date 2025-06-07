from django.utils import timezone
from datetime import timedelta, time, datetime, date
import calendar
import pytz


def get_start_and_end_of_current_month():
    current_date = timezone.now()
    start_of_month = current_date.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    if start_of_month.month == 12:
        next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
    else:
        next_month = start_of_month.replace(month=start_of_month.month + 1)
    end_of_month = next_month - timezone.timedelta(microseconds=1)
    start_timestamp = int(start_of_month.timestamp()) * 1000
    end_timestamp = int(end_of_month.timestamp()) * 1000
    return start_timestamp, end_timestamp


#  this returns in dd-mm-yyyy hh:mm a
def format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
    return dt.strftime("%d-%m-%Y %I:%M %p")


def get_date(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%d-%m-%Y")


def get_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%I:%M %p")


def get_current_date_timestamps():
    now = timezone.now()
    current_date = now.date()
    start_timestamp = str(
        int(datetime.combine(current_date, datetime.min.time()).timestamp() * 1000)
    )
    end_timestamp = str(
        int(datetime.combine(current_date, datetime.max.time()).timestamp() * 1000)
    )
    return start_timestamp, end_timestamp


def get_weeks_for_current_month():
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_date = datetime.now()
    first_day_of_current_month = current_date.replace(day=1)
    cal = calendar.monthcalendar(current_year, current_month)
    weeks = []

    for week in cal:
        days_in_week = [day for day in week if day != 0]
        if days_in_week:
            start_day = min(days_in_week)
            end_day = max(days_in_week)

            # Check if Saturday is the last day of the week
            if (
                calendar.weekday(current_year, current_month, end_day)
                == calendar.SATURDAY
            ):
                end_day += 1

            start_date = datetime(current_year, current_month, start_day)
            end_date = datetime(current_year, current_month, end_day)

            weeks.append(
                {
                    "start_day": start_day,
                    "end_day": end_day,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

    return weeks


def format_time_in_timezone(timestamp_ms, timezone_obj, include_timezone=False):
    """
    Format a timestamp in milliseconds to a human-readable time in a specific timezone.
    Args:
        timestamp_ms: Timestamp in milliseconds
        timezone_obj: pytz timezone object
        include_timezone: Whether to include timezone abbreviation
    Returns:
        str: Formatted time string (e.g. "09:30 AM" or "09:30 AM EDT")
    """
    # Convert milliseconds to seconds
    timestamp_sec = int(timestamp_ms) / 1000
    # Create UTC datetime and convert to target timezone
    utc_time = datetime.fromtimestamp(timestamp_sec, pytz.UTC)
    local_time = utc_time.astimezone(timezone_obj)
    # Format the time
    formatted_time = local_time.strftime("%I:%M %p")
    # Add timezone abbreviation if requested
    if include_timezone:
        timezone_abbr = local_time.strftime("%Z")
        return f"{formatted_time} {timezone_abbr}"
    return formatted_time


def is_local_hour(timezone_obj, hour, current_utc=None):
    """
    Check if it's a specific hour in the given timezone.
    Args:
        timezone_obj: pytz timezone object
        hour: Hour to check (0-23)
        current_utc: Optional UTC datetime to use (defaults to now)
    Returns:
        bool: True if it's the specified hour in the given timezone
    """
    # Get current UTC time if not provided
    if current_utc is None:
        current_utc = datetime.now(pytz.UTC)
    # Convert to local timezone
    local_time = current_utc.astimezone(timezone_obj)
    # Check if it's the specified hour
    return local_time.hour == hour


def get_local_day_timestamps(timezone_obj, day_offset=0):
    """
    Get start and end timestamps for a specific day in a given timezone.

    Args:
        timezone_obj: pytz timezone object
        day_offset: Number of days to offset from today (0=today, 1=tomorrow, -1=yesterday)

    Returns:
        tuple: (start_timestamp_ms, end_timestamp_ms) in milliseconds
    """
    # Get the day in the local timezone
    local_now = datetime.now(timezone_obj)
    target_date = local_now.date() + timedelta(days=day_offset)

    # Get start and end of the day in local timezone
    day_start = datetime.combine(target_date, time.min).replace(tzinfo=timezone_obj)
    day_end = datetime.combine(target_date, time.max).replace(tzinfo=timezone_obj)

    # Convert to UTC for database query
    utc_day_start = day_start.astimezone(pytz.UTC)
    utc_day_end = day_end.astimezone(pytz.UTC)

    # Convert to millisecond timestamps
    start_timestamp_ms = int(utc_day_start.timestamp() * 1000)
    end_timestamp_ms = int(utc_day_end.timestamp() * 1000)

    return start_timestamp_ms, end_timestamp_ms


def get_formatted_time_with_timezone_name(timestamp_ms, timezone_name):
    timezone_obj = pytz.timezone(timezone_name)
    formatted_time = format_time_in_timezone(timestamp_ms, timezone_obj)
    return formatted_time


def get_formatted_date_with_timezone_name(timestamp_ms, timezone_name):
    timezone_obj = pytz.timezone(timezone_name)
    timestamp_sec = int(timestamp_ms) / 1000
    # Create UTC datetime and convert to target timezone
    utc_time = datetime.fromtimestamp(timestamp_sec, pytz.UTC)
    local_time = utc_time.astimezone(timezone_obj)
    # Format the time
    formatted_date = local_time.strftime("%d-%m-%Y")
    return formatted_date