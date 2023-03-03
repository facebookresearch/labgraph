"use client"

import { useSession } from "next-auth/react";
import { useCollection } from "react-firebase-hooks/firestore";
import {collection, orderBy, query} from "firebase/firestore"
import {db} from "../firebase"
import Message from "./Message";
import { ArrowDownCircleIcon } from "@heroicons/react/24/solid";

type Props = {
  chatId: string;
};

function Chat({ chatId }: Props) {

  const {data: session} = useSession()

  const [messages] = useCollection(session && query(collection(db, "users", session?.user?.email!, "chats", chatId, "messages"), orderBy("createdAt", "asc")))
  return <div className="flex-1 overflow-y-scroll-auto overflow-x-hidden">

    {messages?.empty && (
      <>
      <p className="mt-10 text-center text-white">
        Type a prompt below to get started!
      </p>
      <ArrowDownCircleIcon className="h-10 w-10 mx-auto mt-5 text-white animate-bounce"></ArrowDownCircleIcon>
      </>
    )}
{messages?.docs.map((message) => (
  <Message key={message.id} message={message.data()} />
))}
  </div>
}

export default Chat;