from icalendar import Calendar
from datetime import datetime, date, timedelta
from dateutil.rrule import rrulestr

# Inclusive [2021, 2021]
MIN_YEAR = datetime.now().year
MAX_YEAR = MIN_YEAR 

# We only to get the events from the minimum year to the max year
def is_within_limit(dt):
    return MIN_YEAR <= dt.year <= MAX_YEAR

def populate_events(component, start_dt, calendar_events, summary, duration):
    if not is_within_limit(start_dt):
        return 0 
    dt_str = start_dt.strftime('%Y-%m-%d')
    if dt_str not in calendar_events:
        calendar_events[dt_str] = []
    calendar_events[dt_str].append({'name': summary, 'duration': duration})
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
    
calendar_events = calendar_to_dictionary('calendar.ics')
for date, events in sorted(calendar_events.items()):
    print(f"Date: {date}")
    for event in events:
        print(f"  Event: {event['name']}")
        print(f"  Duration: {event['duration']} minutes")
    print()