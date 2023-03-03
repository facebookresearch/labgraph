// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next'
import query from "../../utils/queryApi"
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
            avatar: "https://firebasestorage.googleapis.com/v0/b/speechgpt-77211.appspot.com/o/Avatar%20ChatGPT.png?alt=media&token=4f789405-6cad-483b-8945-0fbda2722bc1",

        },
    }


    await adminDb.collection('users').doc(session?.user?.email).collection('chats').doc(chatId).collection('messages').add(message);



  res.status(200).json({ answer: message.text })
}
