const { Configuration, OpenAIApi } = require("openai");
require('dotenv').config()
const express = require('express')

// console.log(process.env.OPENAI_API_KEY)

const configuration = new Configuration({
    organization: "org-5Ibmla6Cpz4hc0msulYQxwiB",
    apiKey: process.env.OPENAI_API_KEY,
});
// const response = await openai.listEngines();


const openai = new OpenAIApi(configuration);


// create a simple express api that calls the function above
const app = express()

app.post('/', async (req, res) => {
    const response = await openai.createCompletion({
        model: "text-davinci-003",
        prompt: "Say this is a test",
        max_tokens: 7,
        temperature: 0,
    });

    console.log(response.data.choices[0].text);

    res.json({
        data: response.data
    })
})

// listen on port dotenv
app.listen(process.env.PORT, () => {
    console.log(`Example app listening at http://localhost:${process.env.PORT}`)
})
