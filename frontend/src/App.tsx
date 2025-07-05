import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import ChatContainer from './components/ChatContainer';
import DiceRoller from './components/DiceRoller';
import SessionManager from './components/SessionManager';
import './App.css';

interface Message {
  id: string;
  text: string;
  type: 'gm' | 'player' | 'system' | 'error';
  diceRolls?: Array<{
    notation: string;
    result: number;
  }>;
}

interface Session {
  session_id: string;
  summary: string;
  message_count: number;
  first_message: string;
  last_activity: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Welcome to the adventure! Describe your character and let's begin...",
      type: 'gm',
    },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isConnected, setIsConnected] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize Socket.IO connection
    const socket = io();
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('Connected to server');
      setConnectionStatus('Connected');
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnectionStatus('Disconnected');
      setIsConnected(false);
    });

    socket.on('gm_response', (data) => {
      const newMessage: Message = {
        id: Date.now().toString(),
        text: data.response,
        type: 'gm',
        diceRolls: data.dice_rolls,
      };
      setMessages((prev) => [...prev, newMessage]);
    });

    socket.on('error', (data) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        text: data.message,
        type: 'error',
      };
      setMessages((prev) => [...prev, errorMessage]);
    });

    socket.on('session_switched', (data) => {
      setCurrentSessionId(data.session_id);
      const sessionName = data.session_id
        ? `${data.session_id.substring(0, 8)}...`
        : 'New Session';
      const systemMessage: Message = {
        id: Date.now().toString(),
        text: `Switched to: ${sessionName}`,
        type: 'system',
      };
      setMessages((prev) => [...prev, systemMessage]);
    });

    socket.on('dice_result', (data) => {
      const rollText = `${data.notation}: [${data.rolls.join(', ')}]${
        data.modifier !== 0 ? (data.modifier > 0 ? '+' : '') + data.modifier : ''
      } = ${data.total}`;
      const diceMessage: Message = {
        id: Date.now().toString(),
        text: `Rolled ${rollText}`,
        type: 'player',
      };
      setMessages((prev) => [...prev, diceMessage]);
    });

    // Load sessions on mount
    loadSessions();

    return () => {
      socket.disconnect();
    };
  }, []);

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/sessions');
      const data = await response.json();
      if (data.sessions) {
        setSessions(data.sessions);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const sendMessage = (message: string) => {
    if (!message.trim() || !socketRef.current) return;

    // Add player message to chat
    const playerMessage: Message = {
      id: Date.now().toString(),
      text: message,
      type: 'player',
    };
    setMessages((prev) => [...prev, playerMessage]);

    // Send to server
    socketRef.current.emit('send_message', {
      message: message,
      session_id: currentSessionId,
    });
  };

  const rollDice = (notation: string) => {
    if (!socketRef.current) return;
    socketRef.current.emit('roll_dice', { notation });
  };

  const switchSession = (sessionId: string | null) => {
    if (!socketRef.current || sessionId === currentSessionId) return;
    socketRef.current.emit('switch_session', { session_id: sessionId });
  };

  return (
    <div className="container">
      <header>
        <h1>D&D Emulator</h1>
        <p>Claude as your Game Master</p>
      </header>

      <main>
        <div className="game-area">
          <ChatContainer messages={messages} onSendMessage={sendMessage} />

          <div className="sidebar">
            <DiceRoller onRollDice={rollDice} />
            <SessionManager
              sessions={sessions}
              currentSessionId={currentSessionId}
              connectionStatus={connectionStatus}
              isConnected={isConnected}
              onSwitchSession={switchSession}
              onRefreshSessions={loadSessions}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;