import openai from './speechgpt'

type ChatCompletionRequestMessage = {
    role: ChatCompletionRequestMessageRoleEnum;
    content: string;
}

enum ChatCompletionRequestMessageRoleEnum {
    User = 'user',
    Assistant = 'assistant', // update the value to 'Assistant'
    System = 'system'
}

const query = async (prompt: string, chatId: string, model: string, chatHistory: Array<Object>) => {
    // console.log("Model is", model)
    // console.log("Prompt is", prompt)

    // console.log("ChatHistory is", chatHistory)
    let messages: ChatCompletionRequestMessage[] = []
    messages.push({
        role: ChatCompletionRequestMessageRoleEnum.System,
        content: "end your sentence with newline character"
    })

    messages.push({
        role: ChatCompletionRequestMessageRoleEnum.System,
        content: "Wrap code blocks in triple backticks"
    })
    messages.push(...chatHistory.map((message: any) => ({ // spread the mapped array elements into the 'messages' array
        role: message.user._id === "SpeechGPT" ? ChatCompletionRequestMessageRoleEnum.Assistant : ChatCompletionRequestMessageRoleEnum.User,
        content: message.text
    })));

    // console.log("Messages is", messages)

    let response
    if (model === "gpt-3.5-turbo"  || model === "gpt-3.5-turbo-0301") {
    response = await openai.createChatCompletion({
            //  model: "gpt-3.5-turbo",
            model,
            messages
        }).then(res => {
            const responseData = res.data;
            if (responseData.choices[0].message) {
                return responseData.choices[0].message.content;

            } else {
                throw new Error("Response data is undefined");
                return `SpeechGPT was unable to find an answer for that! (Error)`
            }
        }).catch(err => `SpeechGPT was unable to find an answer for that! (Error: ${err.message})`)
    
    }

    else {
        response = await openai.createCompletion({

           model,
           prompt,
           temperature: 0.9,
           max_tokens: 1000,
           top_p: 1,
           frequency_penalty: 0,
           presence_penalty: 0,
       }).then(res => res.data.choices[0].text).catch(err => `SpeechGPT was unable to find an answer for that! (Error: ${err.message})`)
   
   }

    return response
}

export default query
