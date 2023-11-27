from icalendar import Calendar

# Read the user's calendar file and parse it into an icalendar object
with open('calendar.ics', 'r') as f:
    gcal = Calendar.from_ical(f.read())

print(gcal)