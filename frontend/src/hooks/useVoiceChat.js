import { useState, useRef, useCallback, useEffect } from 'react';

const SAMPLE_RATE = 24000;

export function useVoiceChat(userId) {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [userTranscript, setUserTranscript] = useState('');
  const [assistantTranscript, setAssistantTranscript] = useState('');
  const [messages, setMessages] = useState([]);
  const [functionCalls, setFunctionCalls] = useState([]);
  const [error, setError] = useState(null);
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const processorRef = useRef(null);
  const playbackQueueRef = useRef([]);
  const isPlayingRef = useRef(false);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${userId}`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
    
    wsRef.current.onerror = (e) => {
      console.error('WebSocket error:', e);
      setError('Connection error. Please try again.');
    };
    
    wsRef.current.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        // Audio data from assistant
        const arrayBuffer = await event.data.arrayBuffer();
        playbackQueueRef.current.push(arrayBuffer);
        playNextAudio();
      } else {
        // JSON message
        try {
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      }
    };
  }, [userId]);

  // Handle incoming messages
  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'user_transcript':
        setUserTranscript(data.text);
        setMessages(prev => [...prev, { role: 'user', content: data.text }]);
        break;
      
      case 'assistant_transcript_delta':
        setAssistantTranscript(prev => prev + data.text);
        break;
      
      case 'assistant_transcript':
        setAssistantTranscript('');
        setMessages(prev => [...prev, { role: 'assistant', content: data.text }]);
        break;
      
      case 'function_call':
        setFunctionCalls(prev => [...prev, {
          name: data.name,
          arguments: data.arguments,
          result: data.result,
          timestamp: new Date()
        }]);
        break;
      
      case 'error':
        setError(data.message);
        break;
    }
  }, []);

  // Play audio from queue
  const playNextAudio = useCallback(async () => {
    if (isPlayingRef.current || playbackQueueRef.current.length === 0) return;
    
    isPlayingRef.current = true;
    setIsSpeaking(true);
    
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: SAMPLE_RATE
      });
    }
    
    while (playbackQueueRef.current.length > 0) {
      const arrayBuffer = playbackQueueRef.current.shift();
      
      // Convert PCM16 to Float32
      const int16Array = new Int16Array(arrayBuffer);
      const float32Array = new Float32Array(int16Array.length);
      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768;
      }
      
      // Create and play audio buffer
      const audioBuffer = audioContextRef.current.createBuffer(1, float32Array.length, SAMPLE_RATE);
      audioBuffer.getChannelData(0).set(float32Array);
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      
      await new Promise(resolve => {
        source.onended = resolve;
        source.start();
      });
    }
    
    isPlayingRef.current = false;
    setIsSpeaking(false);
  }, []);

  // Start listening
  const startListening = useCallback(async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected. Please wait...');
      return;
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      });
      
      mediaStreamRef.current = stream;
      
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: SAMPLE_RATE
      });
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      processorRef.current.onaudioprocess = (e) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          
          // Convert Float32 to PCM16
          const pcm16 = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
          }
          
          wsRef.current.send(pcm16.buffer);
        }
      };
      
      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
      
      setIsListening(true);
      setUserTranscript('');
      
    } catch (err) {
      console.error('Error starting audio:', err);
      setError('Could not access microphone. Please check permissions.');
    }
  }, []);

  // Stop listening
  const stopListening = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    // Signal to commit audio buffer
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'commit_audio' }));
    }
    
    setIsListening(false);
  }, []);

  // Send text message
  const sendTextMessage = useCallback((text) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ 
        type: 'text_message', 
        text 
      }));
      setMessages(prev => [...prev, { role: 'user', content: text }]);
    }
  }, []);

  // Disconnect
  const disconnect = useCallback(() => {
    stopListening();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, [stopListening]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
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
    sendTextMessage,
  };
}