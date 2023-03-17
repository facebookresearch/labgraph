import React, { useState } from 'react'
import { DocumentData } from "firebase/firestore"
import { signOut, useSession } from "next-auth/react";
import { doc, addDoc, getDocs, collection, serverTimestamp, updateDoc } from "firebase/firestore";
import { db } from "../firebase";

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

      console.log("chatId", chatId);
      console.log("messageId", messageId);

      console.log("thumbsUpClicked");

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
    <div className={`py-5 text-white ${isSpeechGPT && "bg-[#434654]"}`}>
      <div className='flex space-x-5 px-10 max-w-2xl mx-auto'>
        <img src={message.user.avatar} alt="" className='h-8 w-8'></img>
        <p className='pt-1 text-sm'>{message.text}</p>
      </div>
      <div>
        {isSpeechGPT && (
          <div className="flex justify-end px-10 max-w-2xl mx-auto">

            <button className="mx-2 hover:text-blue-500" onClick={handleThumbsUp} disabled={thumbsUpClicked}>
              <svg stroke="currentColor" fill={message.thumbsUp ? "currentColor" : "none"} stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="h-4 w-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg> 
            </button>
            <button className="mx-2 hover:text-blue-500" onClick={handleThumbsDown} disabled={thumbsDownClicked}>
              <svg stroke="currentColor" fill={message.thumbsDown ? "currentColor" : "none"} stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="h-4 w-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path></svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default Message