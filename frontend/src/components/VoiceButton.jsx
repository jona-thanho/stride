import React from 'react';

export function VoiceButton({ isListening, isSpeaking, isConnected, onStart, onStop }) {
  const handleClick = () => {
    if (isListening) {
      onStop();
    } else {
      onStart();
    }
  };

  // Determine button state and styling
  let buttonClass = "relative w-24 h-24 rounded-full transition-all duration-300 ";
  let innerClass = "absolute inset-0 rounded-full flex items-center justify-center ";
  let icon;

  if (!isConnected) {
    buttonClass += "bg-gray-300 cursor-not-allowed";
    innerClass += "bg-gray-400";
    icon = (
      <svg className="w-10 h-10 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    );
  } else if (isListening) {
    buttonClass += "bg-red-100";
    innerClass += "bg-red-500 animate-pulse";
    icon = (
      <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
        <rect x="6" y="6" width="12" height="12" rx="2" />
      </svg>
    );
  } else if (isSpeaking) {
    buttonClass += "bg-stride-100";
    innerClass += "bg-stride-500";
    icon = (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="w-1 bg-white rounded-full sound-bar"
            style={{ height: '16px' }}
          />
        ))}
      </div>
    );
  } else {
    buttonClass += "bg-stride-100 hover:bg-stride-200 cursor-pointer";
    innerClass += "bg-stride-500 hover:bg-stride-600";
    icon = (
      <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    );
  }

  return (
    <button
      onClick={handleClick}
      disabled={!isConnected || isSpeaking}
      className={buttonClass}
    >
      {/* Pulse rings when listening */}
      {isListening && (
        <>
          <span className="absolute inset-0 rounded-full bg-red-400 animate-pulse-ring opacity-50" />
          <span className="absolute inset-0 rounded-full bg-red-400 animate-pulse-ring opacity-30" style={{ animationDelay: '0.5s' }} />
        </>
      )}
      
      <span className={innerClass}>
        {icon}
      </span>
    </button>
  );
}