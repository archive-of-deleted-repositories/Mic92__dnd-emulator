import React, { useState, useRef, useEffect } from 'react';

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
        '<span class="inline-block bg-dnd-gold text-dnd-dark px-2 py-0.5 rounded-sm font-bold mx-1">[$1 = $2]</span>',
      );
    }
    return text;
  };

  return (
    <div className="bg-dnd-dark-secondary rounded-lg p-5 flex flex-col shadow-lg h-full">
      <div className="flex-1 overflow-y-auto p-4 bg-dnd-dark-tertiary rounded mb-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-4 p-3 rounded animate-fadeIn ${
              message.type === 'player'
                ? 'bg-dnd-player border-l-4 border-dnd-blue'
                : message.type === 'gm'
                  ? 'bg-dnd-gm border-l-4 border-dnd-gold'
                  : message.type === 'system'
                    ? 'bg-gray-800/30 border-l-4 border-gray-500 text-gray-400 italic'
                    : 'bg-red-900/30 border-l-4 border-red-500 text-red-300'
            }`}
          >
            <strong className="text-white inline-block mr-2">
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

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type your action or message..."
          autoComplete="off"
          className="flex-1 px-3 py-3 bg-dnd-dark-tertiary border border-gray-700 rounded focus:outline-none focus:border-dnd-gold text-dnd-text text-base"
        />
        <button
          type="submit"
          className="px-6 py-3 bg-dnd-gold text-dnd-dark font-bold rounded hover:bg-yellow-600 transition-colors cursor-pointer"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatContainer;
