import React, { useEffect, useRef } from 'react';

export function ChatMessages({ messages, assistantTranscript, userTranscript, isListening }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, assistantTranscript, userTranscript]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !userTranscript && !assistantTranscript && (
        <div className="text-center text-gray-500 mt-8">
          <p className="text-lg mb-2">👋 Hey! I'm Stride, your running coach.</p>
          <p className="text-sm">Tap the microphone and tell me about your run, ask for workout suggestions, or check the weather.</p>
        </div>
      )}
      
      {messages.map((msg, idx) => (
        <MessageBubble key={idx} role={msg.role} content={msg.content} />
      ))}
      
      {/* Live user transcript while listening */}
      {isListening && userTranscript && (
        <MessageBubble role="user" content={userTranscript} isLive />
      )}
      
      {/* Live assistant transcript while responding */}
      {assistantTranscript && (
        <MessageBubble role="assistant" content={assistantTranscript} isLive />
      )}
      
      <div ref={bottomRef} />
    </div>
  );
}

function MessageBubble({ role, content, isLive }) {
  const isUser = role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 ${
          isUser
            ? 'bg-stride-500 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-900 rounded-bl-md'
        } ${isLive ? 'opacity-70' : ''}`}
      >
        <p className="text-sm whitespace-pre-wrap">{content}</p>
        {isLive && (
          <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
        )}
      </div>
    </div>
  );
}