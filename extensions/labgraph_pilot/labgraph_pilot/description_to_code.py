import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class DescriptionToCode:
    """
    A class that send the request to OpenAI API with a prompt to get back the code
    """
    def __init__(self):
        self.prompt = "Provide well-engineered code for"
        self.model = "text-davinci-003"
        self.max_tokens = 500 # maximum length for the response from the API request
        self.temperature = 0
        self.api_key = os.getenv('OPENAI_API_KEY')

    def get_code_from_description(self, api_name):
        url = "https://api.openai.com/v1/completions"

        payload = json.dumps({
        "model": self.model,
        "prompt": self.prompt + api_name,
        "max_tokens": 500, # handcrafted parameter
        "temperature": 0
        })

        headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + self.api_key
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        json_data = json.loads(response.text)
        generated_code = json_data['choices'][0]['text']

        return generated_code