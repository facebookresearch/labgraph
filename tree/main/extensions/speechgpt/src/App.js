import logo from './logo.svg';
import './App.css';
import { useEffect, useState } from 'react'
import './normal.css'
import ChatMessage from './components/ChatMessage';

// function App() {
//   // add state for input and chat log
//   const [input, setInput] = useState("");
//   const [chatLog, setChatLog] = useState([
//     {
//       user: "gpt",
//       message: "How can I help you today?"
//     }
//   ]);

//   const handleSubmit = async (e) => {
//     e.preventDefault();

//     setChatLog([...chatLog, { user: "me", message: `${input}` }, {
//       user: "me",
//       message: "I'm sorry, I don't understand"
//     }]);
//     setInput("")

//     console.log("hello");
//   }
//   return (

//     <div className="App">
//       <aside className="sidemenu">
//         <div className="sidemenu-button">
//           <span>+</span>
//           New Chat
//         </div>
//       </aside>

//       <section className="chatbox">
//         <div className="chat-log">
//           {chatLog.map((chat, index) => (
//             <ChatMessage key={index} user={chat.user} message={chat.message} />
//           ))}
//         </div>
//         <div className="chat-input-holder">
//           <form onSubmit={handleSubmit}>
//             <textarea onChange={(e) => setInput(e.target.value)} rows="1" className="chat-input-textarea" placeholder="Type your message here">
//             </textarea>
//           </form>
//         </div>
//       </section>
//     </div>
//   );
// }

function App() {
  // add state for input and chat log
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState([
    {
      user: "gpt",
      message: "How can I help you today?"
    }
  ]);

  async function handleSubmit(e) {
    e.preventDefault();
    console.log('submit')
    let chatLogNew = [...chatLog, {user: "me", message: `${input}`} ]
    setInput("");
    // fetch to the API combining chatlog array of message and sending it as a message to localhost:5000
    const messages = chatLogNew.map((message)=> message.message).join("\n")
    const response = await fetch("http://localhost:5000/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: messages
      })
    });
    const data = await response.json();
    setChatLog([...chatLogNew, {user: "gpt", message: `${data.message}`}])
    console.log(data.message);

  }
  return (

    <div className="App">
      <aside className="sidemenu">
        <div className="sidemenu-button">
          <span>+</span>
          New Chat
        </div>
      </aside>

      <section className="chatbox">
        <div className="chat-log">
          {chatLog.map((chat, index) => (
            <ChatMessage key={index} user={chat.user} message={chat.message} />
          ))}
        </div>
        <div className="chat-input-holder">
            <form onSubmit={handleSubmit}>
            <input
            rows = "1"
            value = {input}
            onChange={(e)=>setInput(e.target.value)}
            className = "chat-input-textarea">
            </input>
            </form>
        </div>
      </section>
    </div>
  );
}

export default App;
