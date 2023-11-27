from icalendar import Calendar
from datetime import datetime, date, timedelta
from dateutil.rrule import rrulestr

MAX_YEAR = 2023
CURRENT_YEAR = datetime.now().year

# Read the user's calendar file and parse it into an icalendar object
with open('calendar.ics', 'r') as f:
    gcal = Calendar.from_ical(f.read())

# holds data in the format {'2023-11-06': [Event]} of the user's calendar
calendar_events = {}

# We only to get the events from the current year to the max year
def is_within_limit(dt):
    return CURRENT_YEAR <= dt.year <= MAX_YEAR

for component in gcal.walk():
    if component.name == "VEVENT":
        # Extract information about the event
        summary = str(component.get('summary'))
        start_dt = component.get('dtstart').dt
        end_dt = component.get('dtend').dt
        duration = int((end_dt - start_dt).total_seconds() / 60)  # duration in minutes

        # Builds up the missing events that are defined by the recurring rules
        # Ex: Meetings that happen every M, W, F
        if 'rrule' in component:
            # rr is a generator
            rr = rrulestr(component.get('rrule').to_ical().decode('utf-8'), dtstart=start_dt)
        for dt in rr:
            if not is_within_limit(dt): # Year Out of bounds
                break
            dt_str = dt.strftime('%Y-%m-%d')
            if dt_str not in calendar_events:
                calendar_events[dt_str] = []
            calendar_events[dt_str].append({'name': summary, 'duration': duration})
        else:
            dt_str = start_dt.strftime('%Y-%m-%d')
            if not is_within_limit(start_dt):
                continue
            if dt_str not in calendar_events:
                calendar_events[dt_str] = []
            calendar_events[dt_str].append({'name': summary, 'duration': duration})

for date, events in sorted(calendar_events.items()):
    print(f"Date: {date}")
    for event in events:
        print(f"  Event: {event['name']}")
        print(f"  Duration: {event['duration']} minutes")
    print()