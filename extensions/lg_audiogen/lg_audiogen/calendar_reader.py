from icalendar import Calendar
from datetime import datetime, date, timedelta, timezone
from dateutil.rrule import rrulestr

MIN_YEAR = datetime.now().year
MAX_YEAR = MIN_YEAR 

def is_within_limit(dt):
    """
    Checks if the datetime is within the limit.
    
    @param dt: The datetime to check.
    
    @return: True if the datetime is within the limit, False otherwise.
    """
    return MIN_YEAR <= dt.year <= MAX_YEAR

def convert_to_utc(dt):
    """
    Converts a datetime with timezone info to UTC.
    
    @param dt: The datetime to convert.
    
    @return: The datetime converted to UTC.
    """
    if isinstance(dt, datetime) and dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        # Convert offset-aware datetime to UTC
        return dt.astimezone(timezone.utc)
    return dt

def datetime_to_timestamp(dt):
    """
    Converts a datetime or date to a timestamp.
    
    @param dt: The datetime or date to convert.
    
    @return: The timestamp.
    """
    if isinstance(dt, datetime):
        return dt.timestamp()
    elif isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc).timestamp()
    raise TypeError("Expected datetime.datetime or datetime.date")

def populate_events(start_dt, calendar_events, summary, duration):
    """
    Populates the calendar_events dictionary with the events.
    
    @param start_dt: The start datetime.
    @param calendar_events: The dictionary of events.
    @param summary: The title/summary of the event.
    @param duration: The duration of the event.
    
    @return: 1 if the event was added, 0 otherwise.
    """
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
    """
    Populates the calendar_events dictionary with the recurring events.
    
    @param component: The component to populate the events from.
    @param start_dt: The start datetime.
    @param calendar_events: The dictionary of events.
    @param summary: The title/summary of the event.
    @param duration: The duration of the event.
    """
    # rr will give us a generator
    rr = rrulestr(component.get('rrule').to_ical().decode('utf-8'), dtstart=start_dt)
    for dt in rr:
        if populate_events(dt, calendar_events, summary, duration) == 0:
            return # short circuit if we're out of the range


def calendar_to_dictionary(filepath):
    """
    Given a filepath to a calendar file, returns a dictionary of events.
    
    @param filepath: The filepath to the calendar file.
    
    @return: A dictionary of events from the .ics file.
    """
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
                populate_events(start_dt, calendar_events, summary, duration)

    return calendar_events

def get_events_between_dates(calendar_events, start_date_str, end_date_str):
    """
    Given a dictionary of events, returns the events between two dates [start_date, end_date].
    
    @param calendar_events: The dictionary of events.
    @param start_date_str: The start date.
    @param end_date_str: The end date.
    
    @return: The events between the two dates.
    """
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