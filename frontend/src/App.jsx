import React, { useState, useEffect } from 'react';
import { useVoiceChat } from './hooks/useVoiceChat';
import { VoiceButton } from './components/VoiceButton';
import { ChatMessages } from './components/ChatMessages';
import { TrainingLog } from './components/TrainingLog';

const USER_ID = 1; // For demo, using a single user

function App() {
  const [showSidebar, setShowSidebar] = useState(true);
  
  const {
    isConnected,
    isListening,
    isSpeaking,
    userTranscript,
    assistantTranscript,
    messages,
    functionCalls,
    error,
    connect,
    disconnect,
    startListening,
    stopListening,
  } = useVoiceChat(USER_ID);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-stride-500 rounded-full flex items-center justify-center">
            <span className="text-white text-xl">🏃</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Stride</h1>
            <p className="text-xs text-gray-500">Voice Running Coach</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Connection status */}
          <div className="flex items-center space-x-2">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {/* Toggle sidebar */}
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <ChatMessages
            messages={messages}
            assistantTranscript={assistantTranscript}
            userTranscript={userTranscript}
            isListening={isListening}
          />

          {/* Error display */}
          {error && (
            <div className="mx-4 mb-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Voice input area */}
          <div className="p-6 bg-white border-t border-gray-200">
            <div className="flex flex-col items-center space-y-4">
              <VoiceButton
                isConnected={isConnected}
                isListening={isListening}
                isSpeaking={isSpeaking}
                onStart={startListening}
                onStop={stopListening}
              />
              
              <p className="text-sm text-gray-500">
                {!isConnected ? 'Connecting...' :
                isSpeaking ? 'Stride is speaking...' :
                isListening ? 'Listening... tap to send' :
                'Tap to talk'}
              </p>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <div className="w-80 border-l border-gray-200 bg-white overflow-y-auto">
            <div className="p-4 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Training Log</h2>
            </div>
            <TrainingLog userId={USER_ID} functionCalls={functionCalls} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;