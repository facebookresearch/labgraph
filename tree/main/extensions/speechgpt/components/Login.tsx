'use client'

import { signIn } from "next-auth/react"

import Image from "next/image"

import React from 'react'

const Login = () => {
  // TODO change the image to a custom one
  return (
    <div className="bg-[#ffffff] h-screen flex flex-col items-center justify-center text-center">
      <div className="flex flex-col items-center justify-center h-screen px-2 space-y-3 ">
        <div className="pb-2.5 ">
          <img className="drag-none" src='/images/logoupdatedcolor.png' height={200} width={200}></img>
        </div>
        <div className="mb-2 text-center text-custom-gray">Welcome to SpeechGPT</div>
        <div className="mb-4 text-center text-custom-gray">Log in with your Facebook account to continue</div>
        <div className="flex mt-2 space-x-3">

          {/* <button className="bg-[#1877F2] hover:bg-[#1877F2]/50 text-white font-bold py-4 px-8 rounded-lg flex items-center" onClick={() => signIn('facebook')}>
        <div className="bg-[#ffff] w-12 rounded-full flex items-center justify-center mr-4">
          <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="48" height="48" viewBox="0 0 48 48">
            <path fill="#1877F2" d="M24 5A19 19 0 1 0 24 43A19 19 0 1 0 24 5Z"></path>
            <path fill="#fff" d="M26.572,29.036h4.917l0.772-4.995h-5.69v-2.73c0-2.075,0.678-3.915,2.619-3.915h3.119v-4.359c-0.548-0.074-1.707-0.236-3.897-0.236c-4.573,0-7.254,2.415-7.254,7.917v3.323h-4.701v4.995h4.701v13.729C22.089,42.905,23.032,43,24,43c0.875,0,1.729-0.08,2.572-0.194V29.036z"></path>
          </svg>
        </div>
        <span className="text-xl">Continue with Facebook</span>
      </button> */}

          <button className="bg-[orange] hover:bg-[#1877F2]/50 text-white font-bold py-4 px-8 rounded-lg flex items-center" onClick={() => signIn('google')}>
            <div className="bg-[#ffff] w-12 rounded-full flex items-center justify-center mr-4">
              {/* <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="48" height="48" viewBox="0 0 48 48">
                <path fill="#1877F2" d="M24 5A19 19 0 1 0 24 43A19 19 0 1 0 24 5Z"></path>
                <path fill="#fff" d="M26.572,29.036h4.917l0.772-4.995h-5.69v-2.73c0-2.075,0.678-3.915,2.619-3.915h3.119v-4.359c-0.548-0.074-1.707-0.236-3.897-0.236c-4.573,0-7.254,2.415-7.254,7.917v3.323h-4.701v4.995h4.701v13.729C22.089,42.905,23.032,43,24,43c0.875,0,1.729-0.08,2.572-0.194V29.036z"></path>
              </svg> */}
            </div>
            <span className="text-xl">Continue with Google</span>
          </button>

        </div>

      </div>
      <button onClick={() => signIn('google')}>Log in with google</button>
      <a className="text-sm">Disclaimer: This website is intended for research purposes only. All such trademarks, logos, and features are the property of their respective owners. Any use of such trademarks, logos, or features on this website is for research and informational purposes only. </a>
    </div>
  )
}

export default Login