require('dotenv').config({ path: '.env.local' });
const axios = require('axios');

const API_KEY = process.env.OPENAI_API_KEY;
const API_URL = 'https://api.openai.com/v1/chat/completions';

const data = {
  model: 'gpt-3.5-turbo',
  messages: [
    {
      role: 'system',
      content:
        "You are conducting a survey. Check that the user's answer is a complete sentence. If it is a complete answer, ask another relevant survey question.",
    },
    { role: 'assistant', content: 'What is your favorite hobby?' },
    { role: 'user', content: 'My favorite hobby' },
  ],
  temperature: 1,
  n: 10, // Specify number of generated responses
};

const headers = {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${API_KEY}`,
};

async function makeApiCall() {
  try {
    const response = await axios.post(API_URL, data, { headers });
    return response;
  } catch (error) {
    console.error('Error making API call:', error.message);
    throw error;
  }
}

async function makeMultipleApiCalls() {
  try {
    const response = await makeApiCall();

    console.log(`\nOriginal Messages:`);
    data.messages.forEach((message) => {
      console.log(`${message.role}: ${message.content}`);
    });
    console.log(`\n--------------------------\n`);

    // Display generated responses
    response.data.choices.forEach((choice, index) => {
      console.log(`Response ${index + 1}:`);
      console.log(`${choice.message.content}\n`);
    });
  } catch (error) {
    console.error('An error occurred:', error.message);
  }
}

makeMultipleApiCalls();
