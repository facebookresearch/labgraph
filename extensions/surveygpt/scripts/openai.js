require('dotenv').config({ path: '.env.local' });
const axios = require('axios');

const API_KEY = process.env.OPENAI_API_KEY;
const API_URL = 'https://api.openai.com/v1/chat/completions';

const surveyQuestion = 'What is your favorite hobby?';
const incompleteAnswer = 'My favorite hobby';
const completeAnswer = 'My favorite hobby is reading.';

const headers = {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${API_KEY}`,
};

async function makeApiCall(userInput) {
  try {
    const response = await axios.post(
      API_URL,
      {
        model: 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content:
              "You are conducting a survey. Check that the user's answer is a complete sentence. If it is a complete answer, ask another relevant survey question.",
          },
          { role: 'assistant', content: surveyQuestion },
          { role: 'user', content: userInput },
        ],
        temperature: 1,
        n: 10, // Specify number of generated responses
      },
      { headers }
    );
    return response;
  } catch (error) {
    console.error('Error making API call:', error.message);
    throw error;
  }
}

async function makeMultipleApiCalls(userInput) {
  try {
    const response = await makeApiCall(userInput);

    // Display original messages
    console.log('\nSurveyGPT: ', surveyQuestion);
    console.log('User: ', userInput);
    console.log('\n----------------------------\n');

    // Display generated responses
    console.log('Responses\n');
    response.data.choices.forEach((choice, index) => {
      console.log(`${index + 1}: ${choice.message.content}\n`);
    });

    console.log(
      '-----------------------------------------------------------------------'
    );
  } catch (error) {
    console.error('An error occurred:', error.message);
  }
}

makeMultipleApiCalls(incompleteAnswer);
makeMultipleApiCalls(completeAnswer);
