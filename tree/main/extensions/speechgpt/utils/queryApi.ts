import openai from './speechgpt'


const query = async (prompt: string, chatId: string, model: string, chatHistory: Array<Object>) => {
    console.log("Model is", model)
    console.log("Prompt is", prompt)

    console.log("ChatHistory is", chatHistory)


    const messages = chatHistory.map(message => (
            {
                role: message.user._id === "SpeechGPT" ? "assistant" : "user",
                content: message.text
            }
    ))

    console.log("Messages is", messages)

    let response


    if (model === "gpt-3.5-turbo"  || model === "gpt-3.5-turbo-0301") {
         response = await openai.createChatCompletion({

            model,
            messages
            
        }).then(res => res.data.choices[0].message).catch(err => `SpeechGPT was unable to find an answer for that! (Error: ${err.message})`)
    
    } else {
         response = await openai.createCompletion({

            model,
            prompt,
            // todo: ask manager about creativity level aka temperature
            temperature: 0.9,
            max_tokens: 1000,
            top_p: 1,
            // todo: not sure what this does
            frequency_penalty: 0,
            presence_penalty: 0,
        }).then(res => res.data.choices[0].text).catch(err => `SpeechGPT was unable to find an answer for that! (Error: ${err.message})`)
    
    }

    return response
}

export default query