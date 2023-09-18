# Description

SurveyGPT is a chat application that asks the user dynamic survey questions using the OpenAI API. SurveyGPT builds off of [SpeechGPT](https://github.com/facebookresearch/labgraph/tree/main/extensions/speechgpt), which set up a speech-to-text feature, to serve as an interface for experiments for researchers at Meta Reality Labs.

# Tech Stack

- React for the front-end user interface
- Tailwind CSS for styling
- OpenAI API for chat application API
- Firebase Firestore for the database
- Google for authentication

# Setup

1. Navigate to /tree/main/extensions/surveygpt.
2. Install the dependencies by running `npm i`.
3. Create a .env.local file in the root folder of SurveyGPT with the following API keys:

```
// OPENAI
OPENAI_API_KEY =...

// NEXTAUTH
NEXTAUTH_URL=...
NEXTAUTH_SECRET=...

// GOOGLE
GOOGLE_APP_ID=...
GOOGLE_APP_SECRET=...

// FIREBASE
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_STORAGE_BUCKET=...
FIREBASE_MESSAGE_SENDER_ID=...
FIREBASE_APP_ID=...
FIREBASE_MEASUREMENT_ID=...
FIREBASE_SERVICE_ACCOUNT_KEY= ...
```

# Script for Testing

When run, the custom script located at /tree/main/extensions/surveygpt/scripts/openai.js generates multiple responses to an user response using the OpenAI API. This can assist in testing API settings for generating accurate dynamic responses.

Within /tree/main/extensions/surveygpt, run `node scripts/openai.js`.
