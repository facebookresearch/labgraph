"use client"

import { useSession } from "next-auth/react";
import { useCollection } from "react-firebase-hooks/firestore";
import { collection, orderBy, query } from "firebase/firestore"
import { db } from "../firebase"
import Message from "./Message";
import { ArrowDownCircleIcon } from "@heroicons/react/24/solid";

type Props = {
  chatId: string;
};

function Chat({ chatId }: Props) {

  const { data: session } = useSession()

  const [messages] = useCollection(session && query(collection(db, "users", session?.user?.email!, "chats", chatId, "messages"), orderBy("createdAt", "asc")))
  return <div className="flex-1 overflow-x-hidden overflow-y-scroll-auto">

    {messages?.empty && (
      <>
        <p className="mt-10 text-center text-custom-gray">
          Type a prompt below to get started!
        </p>
        <ArrowDownCircleIcon className="w-10 h-10 mx-auto mt-5 text-custom-gray animate-bounce"></ArrowDownCircleIcon>
      </>
    )}
    {messages?.docs.map((message) => {
      return <Message messageId={message.id} chatId={chatId} message={message.data()} />
    })}
  </div>
}

export default Chat;