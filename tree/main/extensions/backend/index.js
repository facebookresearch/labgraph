

const { Configuration, OpenAIApi } = require("openai");
require("dotenv").config();
const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const configuration = new Configuration({
    organization: process.env.OPENAI_API_ORG,
    apiKey: process.env.OPENAI_API_KEY,
  });
const openai = new OpenAIApi(configuration);




const app = express()
app.use(bodyParser.json());
app.use(cors());

const port = 5000

app.post('/', async (req, res) => {
  const { message } = req.body;
  console.log(message);
  const response = await openai.createCompletion({
      model: "text-davinci-003",
      prompt: `${message}`,
      max_tokens: 100,
      temperature: 0.5,
  });


  res.json({
      message: response.data.choices[0].text,
  })
})

// listen on port dotenv
app.listen(process.env.PORT, () => {
  console.log(`Example app listening at http://localhost:${process.env.PORT}`)
})
