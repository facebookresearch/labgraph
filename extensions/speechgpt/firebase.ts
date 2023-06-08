
// initialize firebase firestore
import {getApp, getApps, initializeApp} from 'firebase/app';
import {getFirestore, collection, getDocs, doc, setDoc, getDoc, query, where, orderBy, limit, startAfter, Timestamp} from 'firebase/firestore';


// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
// console.log(process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID)
// console.log(process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN)
// console.log(process.env.NEXT_PUBLIC_FIREBASE_API_KEY)
// console.log(process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET)
// console.log(process.env.NEXT_PUBLIC_FIREBASE_MESSAGE_SENDER_ID)
// console.log(process.env.NEXT_PUBLIC_FIREBASE_APP_ID)
// console.log(process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID)

// const firebaseConfig = {
//   apiKey: process.env.FIREBASE_API_KEY,
//   authDomain: process.env.FIREBASE_AUTH_DOMAIN,
//   projectId: process.env.FIREBASE_PROJECT_ID,
//   storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
//   messagingSenderId: process.env.FIREBASE_MESSAGE_SENDER_ID,
//   appId: process.env.FIREBASE_APP_ID,
//   measurementId: process.env.FIREBASE_MEASUREMENT_ID
// };



// const firebaseConfig = {
//   apiKey: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
//   authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
//   projectId: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
//   storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
//   messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGE_SENDER_ID,
//   appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
//   measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID
// };



const firebaseConfig = {
  apiKey: "AIzaSyBMd0Wn2-XGBbr0ADEStYAVUF2jo0Z5KE4",
  authDomain: "speechgpt-77211.firebaseapp.com",
  projectId: "speechgpt-77211",
  storageBucket: "speechgpt-77211.appspot.com",
  messagingSenderId: "496610468789",
  appId: "1:496610468789:web:0606b7afd67e001792effc",
  measurementId: "G-DDG6GC0FEF"
};


// this is especially for next.js
// singleton pattern encoding
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const db = getFirestore(app);
// const analytics = getAnalytics(app);

export {db};