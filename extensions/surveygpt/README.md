## Description 

SpeechGPT is a voice-based chat application that enables interaction with powerful large language models. SpeechGPT offers an improved user interface for specific types of queries, allowing users to leverage multiple models from OpenAI, including Ada, Babbage, and GPT-4. Within the context of LabGraph, SpeechGPT is expected to serve as an interface for internal experiments conducted at Meta Reality Labs.

SpeechGPT offers all the features of other chat-based AI application and allows the user to use voice via Speech-to-text to interface with OpenAI models.  

Figma design Mockup of the application: https://www.figma.com/file/TCRbyQtfImnXFtnUWqD1dw/SpeechGPT-main?type=design&node-id=1%3A19&t=S3UEHKEKJcURzWKn-1

Project deployed: https://speechgpt-labgraph.vercel.app/

The following project tackles issues #99, #100, #101 and #102. We have set up the SpeechGPT UI with authentication, New chat, delete chat, and chat history functionalities. We have also created the styling theme for this project including the colors, fonts, and common styles using Tailwind CSS. We are using Firebase Firestore as our database and Google authentication.

This is part of a larger project aiming to integrate speech recognition using microphone with chatGPT.

Dependencies

You will have to create a .env.local in the root folder of /tree/main/extensions/speechgpt with the following API keys and credentials:

```
// FACEBOOK
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...

// NEXTAUTH
NEXTAUTH_URL=...
NEXTAUTH_SECRET=...

// OPENAI
OPENAI_API_KEY =...

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

NEXT_PUBLIC_FIREBASE_API_KEY= ...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN= ...
NEXT_PUBLIC_FIREBASE_PROJECT_ID= ...
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET= ...
NEXT_PUBLIC_FIREBASE_MESSAGE_SENDER_ID= ...
NEXT_PUBLIC_FIREBASE_APP_ID= ...
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID= ...
NEXT_PUBLIC_FIREBASE_SERVICE_ACCOUNT_KEY= ...

```

Next, you will have to install all the dependencies for the UI project. This can be done by running ```npm i``` in the root folder of speechgpt. Here are the dependencies found in speechgpt/package.json

```
  "dependencies": {
    "@heroicons/react": "^2.0.16",
    "classnames": "^2.3.2",
    "firebase-admin": "^11.5.0",
    "heroicons": "^2.0.16",
    "highlight.js": "^11.7.0",
    "next": "latest",
    "next-auth": "^4.19.2",
    "openai": "^3.2.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-firebase-hooks": "^5.1.1",
    "react-hot-toast": "^2.4.0",
    "react-markdown": "^8.0.5",
    "react-select": "^5.7.0",
    "react-speech-recognition": "^3.10.0",
    "react-syntax-highlighter": "^15.5.0",
    "swr": "^2.0.4"
  },
  "devDependencies": {
    "@types/node": "18.11.3",
    "@types/react": "18.0.21",
    "@types/react-dom": "18.0.6",
    "@types/react-speech-recognition": "^3.9.1",
    "@types/react-syntax-highlighter": "^15.5.6",
    "autoprefixer": "^10.4.12",
    "postcss": "^8.4.18",
    "tailwindcss": "^3.2.4",
    "typescript": "4.9.4"
  }
```
