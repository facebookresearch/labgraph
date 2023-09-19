'use client';

import { signIn } from 'next-auth/react';

import React from 'react';

const Login = () => {
  return (
    <div className="h-screen flex flex-col items-center justify-center text-center px-2">
      <div className="flex flex-col items-center justify-center h-screen ">
        <div className="mb-5 w-[70px]">
          <img className="drag-none w-full h-full" src="/images/logo.png" />
        </div>

        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold mb-2">Welcome to SurveyGPT</h1>
          <h2 className="text-lg">Personalized survey chat application</h2>
        </div>

        <button
          className="bg-custom-blue hover:bg-custom-blue/80 text-white py-3 px-5 rounded-full"
          onClick={() => signIn('google')}
        >
          <p>Continue with Google</p>
        </button>
      </div>

      <div className="sm:w-11/12 md:w-7/12 mb-3">
        <p className="text-xs">
          Disclaimer: This website is intended for research purposes only. All
          such trademarks, logos, and features are the property of their
          respective owners. Any use of such trademarks, logos, or features on
          this website is for research and informational purposes only.
        </p>
      </div>
    </div>
  );
};

export default Login;
