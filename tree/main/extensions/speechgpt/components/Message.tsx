import { useState } from 'react'
import { DocumentData } from "firebase/firestore"
import { signOut, useSession } from "next-auth/react";
import { doc, addDoc, getDocs, collection, serverTimestamp, updateDoc } from "firebase/firestore";
import { db } from "../firebase";



import React from 'react';
import ReactMarkdown from 'react-markdown';
import Renderers from 'react-markdown';

import hljs from 'highlight.js';

interface CodeBlockProps {
  language: string;
  value: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, value }) => {
  const highlightedCode = hljs.highlight(value, { language }).value;

  return (
    <pre className="px-4 py-2 overflow-x-auto bg-gray-200 rounded-md"
      style={{
        backgroundColor: 'black',
        color: 'white',
        padding: '1em',
        borderRadius: '0.5em',
        overflowX: 'auto',
      }}
    >
      <code className="font-mono"
        style={{
          fontFamily: 'monospace',
          fontSize: '1em',
          lineHeight: 1.5,
        }}
        dangerouslySetInnerHTML={{ __html: highlightedCode }}
      />
    </pre>
  );
};

// function CodeBlock({ language, value }: CodeBlockProps) {
//   const highlightedCode = hljs.highlight(value, { language }).value;

//   return (
//     <pre className={`hljs ${language}`}>
//       <code dangerouslySetInnerHTML={{ __html: highlightedCode }} />
//     </pre>
//   );
// }
const markdown = `
# My Markdown Document

Here's some code:

\`\`\`javascript
const greeting = "Hello, world!";
console.log(greeting);
\`\`\`
`;

type Props = {
  message: DocumentData
  messageId: string
  chatId: string
}

const Message = ({
  message,
  messageId,
  chatId
}: Props) => {

  const renderers = { code: CodeBlock };

  const isSpeechGPT = message.user.name === "SpeechGPT"
  const [thumbsUpClicked, setThumbsUpClicked] = useState(false);
  const [thumbsDownClicked, setThumbsDownClicked] = useState(false);
  const [thumbsUpCount, setThumbsUpCount] = useState(0);
  const [thumbsDownCount, setThumbsDownCount] = useState(0);

  const { data: session } = useSession();

  const handleThumbsUp = async () => {
    if (!thumbsUpClicked) {
      setThumbsUpClicked(true);
      setThumbsUpCount(thumbsUpCount + 1);
      setThumbsDownClicked(true);


      // Get a reference to the specific message you want to update
      const messageRef = doc(db, 'users', session?.user?.email!, 'chats', chatId, 'messages', messageId);

      // Update the 'thumbsUp' field for the message
      await updateDoc(messageRef, { thumbsUp: true });

    }

  };


  const handleThumbsDown = async () => {
    if (!thumbsDownClicked) {
      setThumbsDownClicked(true);
      setThumbsDownCount(thumbsDownCount + 1);
      setThumbsUpClicked(true);
      // Get a reference to the specific message you want to update
      const messageRef = doc(db, 'users', session?.user?.email!, 'chats', chatId, 'messages', messageId);

      // Update the 'thumbsUp' field for the message
      await updateDoc(messageRef, { thumbsDown: true });
    }

  };

  return (
    <div className={`py-5 text-color-gray ${isSpeechGPT && "bg-[#E8EAEC]"}`}>
      <div className='flex max-w-2xl px-10 mx-auto space-x-5'>
        <img src={message.user.avatar} alt="" className='w-8 h-8'></img>

        {/* <ReactMarkdown className='pt-1 text-sm' renderers={renderers} >{message.text}</ReactMarkdown> */}
        <ReactMarkdown className={`pt-1 text-sm ${isSpeechGPT ? "" : "text-slate-200"}`} >{message.text}</ReactMarkdown>
        <div style={{ width: '60%', overflowX: 'auto' }}>
          <ReactMarkdown className='w-40 pt-1 text-sm' >{message.text}</ReactMarkdown>
        </div>
      </div>
      <div>
        {isSpeechGPT && (
          <div className="flex justify-end max-w-2xl px-10 mx-auto">

            <button className="mx-2 hover:text-blue-500" onClick={handleThumbsUp} disabled={thumbsUpClicked || message.thumbsDown}>
              <svg stroke="currentColor" fill={message.thumbsUp ? "currentColor" : "none"} stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="w-4 h-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
            </button>
            <button className="mx-2 hover:text-blue-500" onClick={handleThumbsDown} disabled={thumbsDownClicked || message.thumbsUp}>
              <svg stroke="currentColor" fill={message.thumbsDown ? "currentColor" : "none"} stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="w-4 h-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path></svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default Message