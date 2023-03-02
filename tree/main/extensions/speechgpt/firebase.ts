// initialize firebase firestore
import {getApp, getApps, initializeApp} from 'firebase/app';
import {getFirestore, collection, getDocs, doc, setDoc, getDoc, query, where, orderBy, limit, startAfter, Timestamp} from 'firebase/firestore';


// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
//console.log(process.env.FIREBASE_PROJECT_ID)
const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_AUTH_DOMAIN,
  projectId: process.env.FIREBASE_PROJECT_ID,
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.FIREBASE_MESSAGE_SENDER_ID,
  appId: process.env.FIREBASE_APP_ID,
  measurementId: process.env.FIREBASE_MEASUREMENT_ID
};

// this is especially for next.js
// singleton pattern encoding
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const db = getFirestore(app);
// const analytics = getAnalytics(app);

export {db};