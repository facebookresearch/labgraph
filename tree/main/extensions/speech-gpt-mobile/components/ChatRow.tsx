import Link from 'next/link';
import React from 'react'
import {ChatBubbleLeftIcon, TrashIcon} from "@heroicons/react/24/outline"

type Props = {
    id: string;
  }
  

const ChatRow = ({id} : Props) => {
  return (
    <Link className={`chatRow justify-center`} href={`/chat/${id}`}><ChatBubbleLeftIcon className='w-5 h-5'></ChatBubbleLeftIcon>
    <p className='flex-1 hidden truncate md:inline-flex'>New Chat</p>
    <TrashIcon className='w-5 h-5 text-gray-700 hover:text-red-700'></TrashIcon></Link>
  )
}

export default ChatRow