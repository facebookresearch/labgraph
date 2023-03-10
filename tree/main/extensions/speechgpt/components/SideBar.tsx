'use client'

import NewChat from "./NewChat";
import { signOut, useSession } from "next-auth/react";
import {useCollection} from "react-firebase-hooks/firestore";
import {collection, orderBy, query} from "firebase/firestore";
import {db} from "../firebase";
import ChatRow from "./ChatRow";
import ModelSelection from "./ModelSelection";
import { useEffect, useState } from "react";

function SideBar() {

  const [isMobile, setIsMobile] = useState(false);

  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768); // set mobile width
    };
    handleResize(); // initial call
    window.addEventListener('resize', handleResize); // attach event listener
    return () => {
      window.removeEventListener('resize', handleResize); // detach event listener
    };
  }, []);
  
  const {data: session} = useSession();

  const [chats, loading, error] = useCollection(
    session && query(collection(db, "users", session?.user?.email!, "chats"),
    orderBy("createdAt", "asc"))
  );

  const handleMenuClick = () => {

    setIsMenuOpen(!isMenuOpen);
  }


  return  <div>
  {isMobile ? (<div className="flex flex-row">

    {
      isMenuOpen ? (   <div className="bg-[#202123]  h-screen 
      overflow-y-auto w-[35rem] z-10 sidebar">
  <div className="flex flex-col h-screen p-2">
      <div className="flex-1">
        <div>
          
          {/* New Chat */}
          <NewChat />
  
          <div className="hidden sm:inline">
            <ModelSelection></ModelSelection>
          </div>
  
          <div className="flex flex-col my-2 space-y-2">
  
            {loading && (
              <div className="text-center text-white animate-pulse">
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
          <a onClick={() => signOut()} className="flex items-center gap-3 px-3 py-3 text-sm text-white transition-colors duration-200 rounded-md cursor-pointer hover:bg-gray-500/10">
            <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="w-4 h-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>Log out</a>
          
        )
      }
    </div>;     </div>) : null
    }
    <div onClick={handleMenuClick} className="bg-[#343541] h-screen 
              overflow-y-auto md:min-w-[15rem]">
      <svg viewBox="0 0 100 80" width="40" height="40">
        <rect width="100" height="10" rx="8"></rect>
        <rect y="30" width="100" height="10" rx="8"></rect>
        <rect y="60" width="100" height="10" rx="8"></rect>
      </svg>
    </div>
    </div>
  ) : (
    // Render sidebar for desktop view
    <div className="bg-[#202123]  h-screen 
    overflow-y-auto md:min-w-[15rem] sidebar">
<div className="flex flex-col h-screen p-2">
    <div className="flex-1">
      <div>
        
        {/* New Chat */}
        <NewChat />

        <div className="hidden sm:inline">
          <ModelSelection></ModelSelection>
        </div>

        <div className="flex flex-col my-2 space-y-2">

          {loading && (
            <div className="text-center text-white animate-pulse">
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
        <a onClick={() => signOut()} className="flex items-center gap-3 px-3 py-3 text-sm text-white transition-colors duration-200 rounded-md cursor-pointer hover:bg-gray-500/10">
          <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="w-4 h-4" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>Log out</a>
        
      )
    }
  </div>;     </div>
  )}
</div>

}

export default SideBar;