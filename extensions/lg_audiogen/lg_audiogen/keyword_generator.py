import os
import json

# This is the default keyword dictionary. It is a JSON file that maps keywords to prompts
# The CLI will allow the user to input his own dictionary of keywords
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORD_DICT =  "/static_inputs/prompt_keywords.json"

# First Try to load KEYWORD_DICT, if it doesn't work, try with THIS_DIR + KEYWORD_DICT
try:
    PROMPT_KEYWORDS = json.load(open(KEYWORD_DICT))
except FileNotFoundError:
    PROMPT_KEYWORDS = json.load(open(THIS_DIR + KEYWORD_DICT))
except:
    raise Exception("Could not load keyword dictionary. Please check that the file exists.")

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