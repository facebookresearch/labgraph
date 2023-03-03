import React from 'react'
import {DocumentData} from "firebase/firestore"

type Props = {
    message: DocumentData
}

const Message = ({
    message
}: Props) => {

    const isSpeechGPT = message.user.name === "SpeechGPT"
  return (
    <div className={`py-5 text-white ${isSpeechGPT && "bg-[#434654]"}`}>
    <div className='flex space-x-5 px-10 max-w-2xl mx-auto'>
        <img src={message.user.avatar} alt="" className='h-8 w-8'></img>
        <p className='pt-1 text-sm'>{message.text}</p>
    </div>
    </div>
  )
}

export default Message