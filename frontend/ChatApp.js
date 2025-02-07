import React, { useState } from "react";

const ChatApp = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim()) return;
        
        const userMessage = { text: input, sender: "user" };
        setMessages([...messages, userMessage]);
        setInput("");
        setIsLoading(true);
        
        const eventSource = new EventSource("http://localhost:5000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message: input }),
        });

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.text) {
                setMessages((prev) => [...prev, { text: data.text, sender: "bot" }]);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            setIsLoading(false);
        };
    };

    return (
        <div>
            <div className="chat-box">
                {messages.map((msg, index) => (
                    <div key={index} className={msg.sender}>{msg.text}</div>
                ))}
            </div>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type a message..." />
            <button onClick={handleSend} disabled={isLoading}>Send</button>
        </div>
    );
};

export default ChatApp;
