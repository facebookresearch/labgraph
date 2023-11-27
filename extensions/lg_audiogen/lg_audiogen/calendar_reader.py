from icalendar import Calendar
from datetime import datetime, date, timedelta

# Read the user's calendar file and parse it into an icalendar object
with open('calendar.ics', 'r') as f:
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
        
        dt_str = start_dt.strftime('%Y-%m-%d') # Dict key is the date in the format YYYY-MM-DD
        if dt_str not in calendar_events:
          calendar_events[dt_str] = []
        
        calendar_events[dt_str].append({'name': summary, 'duration': duration})

print(calendar_events)