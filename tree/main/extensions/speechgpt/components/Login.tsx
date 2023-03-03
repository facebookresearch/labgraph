'use client'

import {signIn} from "next-auth/react"

import Image from "next/image"

import React from 'react'

const Login = () => {
  // TODO change the image to a custom one
  return (
    <div className="bg-[#11A37F] h-screen flex flex-col items-center justify-center text-center">
    <Image
    width={300}
    height={300}
    alt="logo"
    src="https://firebasestorage.googleapis.com/v0/b/speechgpt-77211.appspot.com/o/ChatGPT-Icon-Logo-PNG.png?alt=media&token=8257842a-efd3-45b6-bb16-1d8126068dff"></Image>
    <button onClick={() => signIn('facebook')} className="text-3xl font-bold text-white animate-pulse">Sign in via Facebook to use SpeechGPT</button>
    <button onClick={() => signIn('google')} className="text-3xl font-bold text-white animate-pulse">Sign in via Google to use SpeechGPT</button>
    </div>
  )
}

export default Login