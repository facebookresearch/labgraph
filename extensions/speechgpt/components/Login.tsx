'use client'

import { signIn } from "next-auth/react"

import React from 'react'

const Login = () => {
  return (
    <div className="bg-[#ffffff] h-screen flex flex-col items-center justify-center text-center">
      <div className="flex flex-col items-center justify-center h-screen px-2 space-y-3 ">
        <div className="pb-2.5 ">
          <img className="drag-none" src='/images/logoupdatedcolor.png' height={200} width={200}></img>
        </div>
        <div className="mb-2 text-center text-custom-gray">Welcome to SpeechGPT</div>
        <div className="mb-4 text-center text-custom-gray">Log in with your account to continue</div>
        <div className="flex mt-2 space-x-3">

          <button className="bg-[#e06c00] hover:bg-[#e06c00]/50 text-white font-bold py-4 px-8 rounded-lg flex items-center" onClick={() => signIn('google')}>
            <div className="bg-[#ffff] w-12 rounded-full flex items-center justify-center mr-4">
              <img src="https://firebasestorage.googleapis.com/v0/b/speechgpt-77211.appspot.com/o/google-logo-9808.png?alt=media&token=eeca53a0-c32a-4546-bbd0-3988d181d10a"></img>
            </div>
            <span className="text-xl">Continue with Google</span>
          </button>

        </div>

      </div>
      <button onClick={() => signIn('facebook')}>Log in with facebook</button>
      <a className="text-sm">Disclaimer: This website is intended for research purposes only. All such trademarks, logos, and features are the property of their respective owners. Any use of such trademarks, logos, or features on this website is for research and informational purposes only. </a>
    </div>
  )
}

export default Login