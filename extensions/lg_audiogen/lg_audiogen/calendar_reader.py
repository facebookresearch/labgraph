from icalendar import Calendar
from datetime import datetime, date, timedelta, timezone
from dateutil.rrule import rrulestr

# Inclusive [2021, 2021]
MIN_YEAR = datetime.now().year
MAX_YEAR = MIN_YEAR 

# We only to get the events from the minimum year to the max year
def is_within_limit(dt):
    return MIN_YEAR <= dt.year <= MAX_YEAR

def convert_to_utc(dt):
    if isinstance(dt, datetime) and dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        # Convert offset-aware datetime to UTC
        return dt.astimezone(timezone.utc)
    return dt

def datetime_to_timestamp(dt):
    if isinstance(dt, datetime):
        return dt.timestamp()
    elif isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc).timestamp()
    raise TypeError("Expected datetime.datetime or datetime.date")

def populate_events(component, start_dt, calendar_events, summary, duration):
    if not is_within_limit(start_dt):
        return 0

    # Ensure dt is converted to UTC if it's a datetime with timezone info.
    utc_start_dt = convert_to_utc(start_dt)
    # Create timestamp from datetime or date (for sorting later)
    timestamp = datetime_to_timestamp(utc_start_dt)

    dt_str = start_dt.strftime('%Y-%m-%d') if isinstance(start_dt, date) \
        else utc_start_dt.strftime('%Y-%m-%d')

    if dt_str not in calendar_events:
        calendar_events[dt_str] = []

    event = {'name': summary, 'duration': duration, 'ts': timestamp}
    calendar_events[dt_str].append(event)
    return 1

def populate_recurring_events(component, start_dt, calendar_events, summary, duration):
    # rr will give us a generator
    rr = rrulestr(component.get('rrule').to_ical().decode('utf-8'), dtstart=start_dt)
    for dt in rr:
        if populate_events(component, dt, calendar_events, summary, duration) == 0:
            return # short circuit if we're out of the range


def calendar_to_dictionary(filepath):
    # Read the user's calendar file and parse it into an icalendar object
    with open(filepath, 'r', encoding='utf-8') as f:
        gcal = Calendar.from_ical(f.read())

    # holds data in the format {'2023-11-06': [Event]} of the user's calendar
    calendar_events = {}

    for component in gcal.walk():
        if component.name == "VEVENT":
            # Extract information about the event
            summary = str(component.get('summary'))
            start_dt = component.get('dtstart').dt
            end_dt = component.get('dtend').dt
            duration = int((end_dt - start_dt).total_seconds() / 60)  # duration in minutes

            # rrule Builds up the missing events that are defined by the recurring rules
            # Ex: Meetings that happen every M, W, F
            if 'rrule' in component:
                populate_recurring_events(component, start_dt, calendar_events, summary, duration)
            else:
                populate_events(component, start_dt, calendar_events, summary, duration)

    return calendar_events

def get_events_for_specific_date(calendar_events, specific_date_str):
    # Assumes specific_date_str is in YYYY-MM-DD format
    day_events = calendar_events.get(specific_date_str, [])
    # Sort events by timestamp key 'ts' in ascending order
    return sorted(day_events, key=lambda event: event['ts'])

def get_events_between_dates(calendar_events, start_date_str, end_date_str):
    # Assumes start_date_str and end_date_str are in YYYY-MM-DD format and start_date <= end_date
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    events_between_dates = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str in calendar_events:
            # Sort events for the current date by timestamp key 'ts' in ascending order
            events_between_dates[date_str] = sorted(calendar_events[date_str], key=lambda event: event['ts'])
        current_date += timedelta(days=1)
    return events_between_dates