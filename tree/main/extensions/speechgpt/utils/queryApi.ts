import openai from './speechgpt'

type ChatCompletionRequestMessage = {
    role: ChatCompletionRequestMessageRoleEnum;
    content: string;
}

enum ChatCompletionRequestMessageRoleEnum {
    User = 'user',
    Assistant = 'assistant', // update the value to 'Assistant'
}

const query = async (prompt: string, chatId: string, model: string, chatHistory: Array<Object>) => {
    console.log("Model is", model)
    console.log("Prompt is", prompt)

    console.log("ChatHistory is", chatHistory)

    const messages = chatHistory.map((message: any) => (
        {
            role: message.user._id === "SpeechGPT" ? ChatCompletionRequestMessageRoleEnum.Assistant : ChatCompletionRequestMessageRoleEnum.User, // use the enum values instead of strings
            content: message.text
        }
    ))

    console.log("Messages is", messages)

    let response = await openai.createChatCompletion({
            model: "gpt-3.5-turbo",
            messages
        }).then(res => {
            const responseData = res.data;
            if (responseData.choices[0].message) {
                console.log("api response:", responseData.choices[0].message.content )
                return responseData.choices[0].message.content;
            } else {
                throw new Error("Response data is undefined");
                return `SpeechGPT was unable to find an answer for that! (Error)`
            }
        }).catch(err => `SpeechGPT was unable to find an answer for that! (Error: ${err.message})`)

    return response
}

export default query
