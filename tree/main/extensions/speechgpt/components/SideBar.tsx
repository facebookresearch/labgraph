'use client'

import NewChat from "./NewChat";
import { signOut, useSession } from "next-auth/react";
import {useCollection} from "react-firebase-hooks/firestore";
import {collection, orderBy, query} from "firebase/firestore";
import {db} from "../firebase";
import ChatRow from "./ChatRow";
import ModelSelection from "./ModelSelection";
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

        <div className="hidden sm:inline">
          <ModelSelection></ModelSelection>
        </div>

        <div className="flex flex-col space-y-2 my-2">

          {loading && (
            <div className="animate-pulse text-center text-white">
              <p>Loading Chats...</p>
              </div>
          )}

        {
          chats?.docs.map((chat) => (
            <ChatRow key={chat.id} id={chat.id} />
          )
        )
      }
        </div>


      
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