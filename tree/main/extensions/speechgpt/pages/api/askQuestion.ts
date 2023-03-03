// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next'
import query from "../../lib/queryApi"
import admin from 'firebase-admin'
import adminDb  from '../../firebaseAdmin'

type Data = {
  answer: string
}


export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<Data>
) {

    const {prompt, chatId, model, session} = req.body
    
    if ( !prompt) { 
        res.status(400).json({ answer: 'Please provide a prompt' })
        return
    }
        
    if ( !chatId) { 
        res.status(400).json({ answer: 'Please provide a valid Chat ID' })
        return
    }

    const response = await query(prompt, chatId, model)

    const message: Message = {

        text: response || "SpeechGPT was unable to find an answer for that!",
        createdAt: admin.firestore.Timestamp.now(),
        user: {
            _id: "SpeechGPT",
            name: "SpeechGPT",
            avatar: "https://firebasestorage.googleapis.com/v0/b/speechgpt-77211.appspot.com/o/ChatGPT-Icon-Logo-PNG.png?alt=media&token=538d7259-afbd-4af3-b590-44e7a8ef2a3d",

        },
    }


    await adminDb.collection('users').doc(session?.user?.email).collection('chats').doc(chatId).collection('messages').add(message);



  res.status(200).json({ answer: message.text })
}
