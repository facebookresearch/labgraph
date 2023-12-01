
PROMPT_KEYWORDS = {
    "commute": ["Sounds of cars honking", "Buzz of a busy metro", "Rhythmic chime of train tracks"],
    "beach": ["Sounds of waves hitting rocks", "Seagulls in the background", "Children playing in the sand"],
    "workout": ["Beats of high-energy music", "Grunts and clanks of gym equipment", "Breathless intensity of a sprint"],
    "dinner": ["Clatter of cutlery on plates", "Murmur of dinner conversation", "Sizzle of food cooking"],
}

def match_keyword(event_name):
    keywords = PROMPT_KEYWORDS.keys()
    for keyword in keywords:
        if keyword.lower() in event_name.lower():
            return keyword
    return None


events = [
    {"name": "Commute to work", "duration": 30},
    {"name": "Going to the beach", "duration": 120},
]

for event in events:
    keyword = match_keyword(event["name"])
    if keyword:
        print(f"Event {event['name']} matches keyword {keyword}.")
    else:
        print(f"Event {event['name']} does not match any keywords.")