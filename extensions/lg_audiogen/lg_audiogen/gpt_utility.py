import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_gpt(event_list, deterministic=False):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Creative and deterministic assistant in generating sound prompts from a given list of events. Ignore proper names and focus on defined sounds."
            },
            {
                "role": "user",
                "content": "[\"Commute to work\", \"Walk by the beach\"]"
            },
            {
                "role": "assistant",
                "content": "[\"Cars honking in traffic\", \"Footsteps tapping on the sand with waves in the background\"]"
            },
            {
                "role": "user",
                "content": "[\"Virtual Meeting with Nathan\", \"Beer and Chips with Friends\"]"
            },
            {
                "role": "assistant",
                "content": "[\"Keyboard typing and mouse clicks\", \"Laughter and the clinking of glasses, crunching of chips\"]"
            },
        ],
        temperature=0 if deterministic else 1,
        max_tokens=1101,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response = json.loads(response.choices[0].message.content)
    return response

event_list = ["Commute to work", "Walk by the beach"]
response = query_gpt(event_list)
print(response)