"use client";

import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import { addDoc, getDocs, collection, serverTimestamp } from "firebase/firestore";
import { useSession } from "next-auth/react";
import { FormEvent, useState } from "react";
import { toast } from "react-hot-toast";
import { db } from "../firebase";
import ModelSelection from "./ModelSelection";
import useSWR from "swr"


type Props = {
  chatId: string;
};

function ChatInput({ chatId }: Props) {
  const [prompt, setPrompt] = useState("");
  const { data: session } = useSession();


  const { data: model, mutate: setModel } = useSWR("model", {
    fallbackData: "text-davinci-003"
  })


  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!prompt) return;

    const input = prompt.trim();
    setPrompt("");

    const message: Message = {
      text: input,
      createdAt: serverTimestamp(),
      user: {
        _id: session?.user?.email!,
        name: session?.user?.name!,
        avatar: session?.user?.image! || `https://ui-avatars.com/api/?name=${session?.user?.name}`,
      },
      thumbsUp: false,
      thumbsDown: false
    }

    await addDoc(
      collection(db, 'users', session?.user?.email!, 'chats', chatId, 'messages'),
      message
    )



    // Query the Firebase database to get all messages for this chat
    const querySnapshot = await (await getDocs(collection(db, 'users', session?.user?.email!, 'chats', chatId, 'messages')))

    const chatHistory = querySnapshot.docs.map(doc => doc.data());
    console.log("Snapshot", querySnapshot)

    const notification = toast.loading('SpeechGPT is thinking...');

    await fetch("/api/askQuestion", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: input,
        chatId,
        model,
        chatHistory,
        session,
      }),
    }).then(() => {
      // Toast notification to say sucessful!
      toast.success("SpeechGPT has responded!", {
        id: notification,
      });
    });
  };

  return (
    <div className="text-sm text-gray-400 rounded-lg bg-gray-700/50">
      <form onSubmit={sendMessage} className="flex p-5 space-x-5">
        <input
          className="flex-1 bg-transparent focus:outline-none disabled:cursor-not-allowed disabled:text-gray-300"
          disabled={!session}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          type="text" placeholder="Type your message here..."
        />

        <button disabled={!prompt || !session} type="submit"
          className="bg-[#11A37F] hover:opacity-50 text-white font-bold
          px-4 py-2 rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          <PaperAirplaneIcon className="w-4 h-4 -rotate-45" />
        </button>
      </form>

      <div>
        <div className="md:hidden">
          <ModelSelection></ModelSelection>
        </div>
      </div>
    </div>
  )
}

export default ChatInput