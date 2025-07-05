import React, { useState, useRef, useEffect } from 'react';
import './ChatContainer.css';

interface Message {
  id: string;
  text: string;
  type: 'gm' | 'player' | 'system' | 'error';
  diceRolls?: Array<{
    notation: string;
    result: number;
  }>;
}

interface ChatContainerProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ messages, onSendMessage }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const formatMessageText = (text: string, type: string) => {
    if (type === 'gm') {
      // Parse dice roll notation in GM messages
      return text.replace(
        /\[(\d+d\d+(?:[+-]\d+)?)\]\s*=\s*(\d+)/g,
        '<span class="dice-roll">[$1 = $2]</span>',
      );
    }
    return text;
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}-message`}>
            <strong>
              {message.type === 'gm'
                ? 'GM:'
                : message.type === 'player'
                  ? 'You:'
                  : message.type === 'system'
                    ? 'System:'
                    : 'Error:'}
            </strong>
            {message.type === 'gm' ? (
              <span
                dangerouslySetInnerHTML={{
                  __html: formatMessageText(message.text, message.type),
                }}
              />
            ) : (
              <span>{message.text}</span>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-area">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type your action or message..."
          autoComplete="off"
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatContainer;
