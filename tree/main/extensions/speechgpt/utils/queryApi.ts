import openai from './speechgpt'


const query = async (prompt: string, chatId: string, model: string) => {
    console.log("Model is", model)
    console.log("Prompt is", prompt)
    const response = await openai.createCompletion({

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

    return response
}

export default query