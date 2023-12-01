import os
import json
import random

# This is the default keyword dictionary. It is a JSON file that maps keywords to prompts
# The CLI will allow the user to input his own dictionary of keywords
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORD_DICT =  "/static_inputs/prompt_keywords.json"

# SEED for Deterministic Randomness
DEFAULT_SEED = 42

# First Try to load KEYWORD_DICT, if it doesn't work, try with THIS_DIR + KEYWORD_DICT
try:
    PROMPT_KEYWORDS = json.load(open(KEYWORD_DICT))
except FileNotFoundError:
    PROMPT_KEYWORDS = json.load(open(THIS_DIR + KEYWORD_DICT))
except:
    raise Exception("Could not load keyword dictionary. Please check that the file exists.")

# for each word in the event name, check if it matches a keyword
# if it does, add one of the random prompt to the list to return
# deterministic=True will make the random choice deterministic
def get_prompts(event_name, deterministic=False):
    event_name = event_name.lower()
    prompt = []
    random.seed(DEFAULT_SEED if deterministic else None)
    for word in event_name.split():
        if word in PROMPT_KEYWORDS:
            prompt.append(random.choice(PROMPT_KEYWORDS[word]))
    return prompt


events = [
    {"name": "Commute to work", "duration": 30},
    {"name": "Going to the beach", "duration": 120},
]

for event in events:
    prompts = get_prompts(event["name"])
    if prompts:
        print(f"Event {event['name']} matches:")
        for p in prompts:
            print(f"{p}\n")
    else:
        print(f"Event {event['name']} does not match any keywords.")