'use client'

import NewChat from "./NewChat";
import { signOut, useSession } from "next-auth/react";
import {useCollection} from "react-firebase-hooks/firestore";
import {collection, orderBy, query} from "firebase/firestore";
import {db} from "../firebase";
import ChatRow from "./ChatRow";
function SideBar() {


  const {data: session} = useSession();

  const [chats, loading, error] = useCollection(
    session && query(collection(db, "users", session?.user?.email!, "chats"),
    orderBy("createdAt", "asc"))
  );


  return <div className="flex flex-col h-screen p-2">
    <div className="flex-1">
      <div>
        
        {/* New Chat */}
        <NewChat />

        <div>
          {/* Model Selection */}
        </div>

        {
          chats?.docs.map((chat) => (
            <ChatRow key={chat.id} id={chat.id} />
          )
        )
      }
      
      </div>
    </div>

    {
      session && (
        // log out button
        <div className="flex items-center justify-center">
          <button onClick={() => signOut()} className="bg-[#11A37F] text-white p-2 rounded-full hover:bg-[#0F8C6F]">
            Sign out
          </button>
        </div>
        
      )
    }
  </div>; 
}

export default SideBar;