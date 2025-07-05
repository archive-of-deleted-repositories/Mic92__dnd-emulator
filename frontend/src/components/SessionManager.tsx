import React, { useState, useEffect } from 'react';
import './SessionManager.css';

interface Session {
  session_id: string;
  summary: string;
  message_count: number;
  first_message: string;
  last_activity: string;
}

interface SessionManagerProps {
  sessions: Session[];
  currentSessionId: string | null;
  connectionStatus: string;
  isConnected: boolean;
  onSwitchSession: (sessionId: string | null) => void;
  onRefreshSessions: () => void;
}

const SessionManager: React.FC<SessionManagerProps> = ({
  sessions,
  currentSessionId,
  connectionStatus,
  isConnected,
  onSwitchSession,
  onRefreshSessions,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showNewSessionInput, setShowNewSessionInput] = useState(!currentSessionId);
  const [newSessionName, setNewSessionName] = useState('');

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefreshSessions();
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  // Update showNewSessionInput when currentSessionId changes
  useEffect(() => {
    setShowNewSessionInput(!currentSessionId);
  }, [currentSessionId]);

  const handleCreateSession = () => {
    if (newSessionName.trim()) {
      onSwitchSession(newSessionName.trim());
      setNewSessionName('');
      setShowNewSessionInput(false);
    }
  };

  const truncateSummary = (summary: string, maxLength: number = 30) => {
    return summary.length > maxLength ? summary.substring(0, maxLength) + '...' : summary;
  };

  return (
    <div className="game-info">
      <h3>Session Info</h3>
      <div className="session-selector">
        <label htmlFor="session-select">Session:</label>
        <select
          id="session-select"
          value={currentSessionId || ''}
          onChange={(e) => {
            if (e.target.value === '') {
              setShowNewSessionInput(true);
            } else {
              onSwitchSession(e.target.value);
            }
          }}
        >
          <option value="">New Session</option>
          {sessions.map((session) => (
            <option
              key={session.session_id}
              value={session.session_id}
              title={`${session.summary}\n${session.first_message}`}
            >
              {truncateSummary(session.summary)} ({session.message_count} msgs)
            </option>
          ))}
        </select>
        <button className="refresh-button" onClick={handleRefresh} title="Refresh sessions">
          {isRefreshing ? '✓' : '↻'}
        </button>
      </div>
      {showNewSessionInput && (
        <div className="new-session-input">
          <input
            type="text"
            placeholder="Enter session name..."
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleCreateSession();
              }
            }}
            autoFocus
          />
          <div className="button-group">
            <button onClick={handleCreateSession}>Create</button>
            <button
              onClick={() => {
                setShowNewSessionInput(false);
                setNewSessionName('');
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      <p>
        Session:{' '}
        <span id="session-id">
          {currentSessionId ? `${currentSessionId.substring(0, 8)}...` : 'New'}
        </span>
      </p>
      <p>
        Status:{' '}
        <span id="connection-status" className={isConnected ? 'connected' : 'disconnected'}>
          {connectionStatus}
        </span>
      </p>
    </div>
  );
};

export default SessionManager;
