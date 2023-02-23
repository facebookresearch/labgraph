'use client'

import NewChat from "./NewChat";
import { signOut, useSession } from "next-auth/react";

function SideBar() {

  const {data: session} = useSession();
  return <div className="flex flex-col h-screen p-2">
    <div className="flex-1">
      <div>
        
        {/* New Chat */}
        <NewChat />

        <div>
          {/* Model Selection */}
        </div>

        {/* Map through the ChatRows */}
      
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