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
def get_prompts(event_names, deterministic=False):
    if PROMPT_KEYWORDS and len(PROMPT_KEYWORDS) == 0:
        raise Exception("Keyword dictionary is empty. Please check that the file is not empty.")
    full_prompt = []
    for event in event_names:
        event_name = event.lower()
        prompt = []
        random.seed(DEFAULT_SEED if deterministic else None)
        for word in event.split():
            if word in PROMPT_KEYWORDS:
                prompt.append(random.choice(PROMPT_KEYWORDS[word]))
        if len(prompt) > 1:
            prompt = ' combined with '.join(prompt)
            full_prompt.append(prompt)
        elif len(prompt) == 1:
            full_prompt.append(prompt[0])
        else:
            full_prompt.append(event_name) # if no prompt is found, just use the event name
    return full_prompt