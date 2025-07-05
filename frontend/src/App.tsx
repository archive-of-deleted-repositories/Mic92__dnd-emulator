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
      text: 'Please create or select a session to begin your adventure.',
      type: 'system',
    },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isConnected, setIsConnected] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const socketRef = useRef<Socket | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  // Keep sessionIdRef in sync with currentSessionId
  useEffect(() => {
    sessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

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

      // Refresh sessions to update message counts
      loadSessions();
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
      const sessionName = data.session_id ? `${data.session_id.substring(0, 8)}...` : 'New Session';
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

      // Also send the dice roll to the GM
      socketRef.current?.emit('send_message', {
        message: `I rolled ${rollText}`,
        session_id: sessionIdRef.current,
      });
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
    socketRef.current.emit('roll_dice', {
      notation,
      session_id: currentSessionId,
    });
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/messages`);
      const data = await response.json();
      if (data.messages) {
        // Convert Claude messages to our message format
        const loadedMessages: Message[] = data.messages.map(
          (msg: { content: string; role: string }, index: number) => ({
            id: `loaded-${index}`,
            text: msg.content,
            type: msg.role === 'user' ? 'player' : 'gm',
          }),
        );

        // Add a system message to indicate messages were loaded
        const systemMessage: Message = {
          id: Date.now().toString(),
          text: `Loaded ${loadedMessages.length} messages from session history`,
          type: 'system',
        };

        setMessages([...loadedMessages, systemMessage]);
      }
    } catch (error) {
      console.error('Failed to load session messages:', error);
    }
  };

  const switchSession = async (sessionId: string | null) => {
    if (!socketRef.current || sessionId === currentSessionId) return;

    // Clear current messages when switching sessions
    setMessages([]);

    // Load session messages if switching to an existing session
    if (sessionId) {
      // Check if this is an existing session
      const existingSession = sessions.find((s) => s.session_id === sessionId);
      if (existingSession) {
        await loadSessionMessages(sessionId);
      } else {
        // New named session - show welcome message
        setMessages([
          {
            id: '1',
            text: "Welcome to the adventure! Describe your character and let's begin...",
            type: 'gm',
          },
        ]);
      }
    } else {
      // No session selected
      setMessages([
        {
          id: '1',
          text: 'Please create or select a session to begin your adventure.',
          type: 'system',
        },
      ]);
    }

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
