import React, { useState, useEffect } from 'react';

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
    <div className="bg-dnd-dark-secondary rounded-lg p-5 shadow-lg">
      <h3 className="text-dnd-gold mb-4 text-lg font-bold">Session Info</h3>
      <div className="flex gap-2 items-center mb-2">
        <label htmlFor="session-select" className="font-bold">
          Session:
        </label>
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
          className="flex-1 p-1 bg-dnd-dark-tertiary border border-gray-700 rounded text-dnd-text text-sm overflow-hidden text-ellipsis"
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
        <button
          className="p-1 px-2 bg-dnd-player border border-gray-700 rounded text-dnd-text cursor-pointer text-base transition-colors hover:bg-blue-800"
          onClick={handleRefresh}
          title="Refresh sessions"
        >
          {isRefreshing ? '✓' : '↻'}
        </button>
      </div>
      {showNewSessionInput && (
        <div className="flex flex-col gap-2 mt-2 mb-2">
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
            className="w-full p-1 bg-dnd-dark-tertiary border border-gray-700 rounded text-dnd-text text-sm"
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={handleCreateSession}
              className="px-4 py-1 bg-dnd-player border border-gray-700 rounded text-dnd-text cursor-pointer text-sm transition-colors hover:bg-blue-800 whitespace-nowrap"
            >
              Create
            </button>
            <button
              onClick={() => {
                setShowNewSessionInput(false);
                setNewSessionName('');
              }}
              className="px-4 py-1 bg-dnd-player border border-gray-700 rounded text-dnd-text cursor-pointer text-sm transition-colors hover:bg-blue-800 whitespace-nowrap"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      <p className="mb-2 overflow-hidden text-ellipsis whitespace-nowrap">
        Session:{' '}
        <span className="text-dnd-blue font-bold text-xs font-mono">
          {currentSessionId ? `${currentSessionId.substring(0, 8)}...` : 'New'}
        </span>
      </p>
      <p className="mb-2 overflow-hidden text-ellipsis whitespace-nowrap">
        Status:{' '}
        <span className={`font-bold ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
          {connectionStatus}
        </span>
      </p>
    </div>
  );
};

export default SessionManager;
