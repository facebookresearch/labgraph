// write next.js auth code here for facebook login

import NextAuth from "next-auth"
import FacebookProvider from "next-auth/providers/facebook";
import GoogleProvider from "next-auth/providers/google";

export const authOptions = {
    providers: [
        FacebookProvider({
            clientId: process.env.FACEBOOK_APP_ID!,
            clientSecret: process.env.FACEBOOK_APP_SECRET!,
        }),
        GoogleProvider({
            clientId: process.env.GOOGLE_APP_ID!,
            clientSecret: process.env.GOOGLE_APP_SECRET!,
        }),
    ],
}

export default NextAuth(authOptions)
