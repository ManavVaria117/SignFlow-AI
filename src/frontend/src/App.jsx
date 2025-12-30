import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Zap, Mic, Globe, Cpu } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// Dynamic WebSocket URL based on API_URL
const WS_URL = API_URL.replace(/^http/, 'ws') + '/ws';

function App() {
  const [data, setData] = useState({ sentence: '', prediction: -1, confidence: 0 });
  const [connected, setConnected] = useState(false);
  const actions = ['Hello', 'ThankYou', 'Help', 'Please'];

  /* -- Integrated Client-Side TTS -- */
  const lastSpokenWordRef = useRef("");

  useEffect(() => {
    if (!data.sentence) return;

    // Extract the very last word from the sentence
    const words = data.sentence.split(" ").filter(Boolean);
    const currentLastWord = words[words.length - 1];

    // Speak if it's a new word we haven't spoken yet
    if (currentLastWord && currentLastWord !== lastSpokenWordRef.current) {
      console.log("Speaking:", currentLastWord);

      // Browser Speech API
      const utterance = new SpeechSynthesisUtterance(currentLastWord);
      utterance.rate = 1.1; // Zap Quick speed
      utterance.pitch = 1.0;

      // Optional: Select a better voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.lang.includes('en') && v.name.includes('Google')) || voices[0];
      if (preferredVoice) utterance.voice = preferredVoice;

      window.speechSynthesis.speak(utterance);

      lastSpokenWordRef.current = currentLastWord;
    }
  }, [data.sentence]);

  /* -- Camera Logic -- */
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Start Camera
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Camera Error:", err);
      }
    };
    startCamera();
  }, []);

  /* -- Robust WebSocket Connection with Streaming -- */
  useEffect(() => {
    let reconnectTimer;

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Connected to Brain');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          setData(msg);
        } catch (e) {
          console.error("Parse Error", e);
        }
      };

      ws.onclose = () => {
        console.log("Brain disconnected, retrying...");
        setConnected(false);
        reconnectTimer = setTimeout(connect, 3000); // Auto-reconnect
      };
    };

    connect();

    return () => {
      if (wsRef.current) wsRef.current.close();
      clearTimeout(reconnectTimer);
    };
  }, []);

  // Frame Loop
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && videoRef.current && canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0, 640, 480);
        const image = canvasRef.current.toDataURL('image/jpeg', 0.5); // Quality 0.5

        wsRef.current.send(JSON.stringify({ image: image }));
      }
    }, 50); // 20 FPS

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-cyan-50 font-sans p-6 flex flex-col items-center justify-start relative overflow-y-auto">

      {/* Hidden processing canvas */}
      <canvas ref={canvasRef} width="640" height="480" className="hidden" />

      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20 z-0">
        <div className="absolute top-[10%] left-[20%] w-96 h-96 bg-cyan-600 rounded-full blur-[128px]" />
        <div className="absolute bottom-[10%] right-[20%] w-96 h-96 bg-purple-600 rounded-full blur-[128px]" />
      </div>

      <div className="z-10 w-full max-w-5xl flex flex-col items-center w-full">

        {/* Header */}
        <motion.div
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="w-full flex justify-between items-center mb-4 lg:mb-8 bg-slate-900/50 backdrop-blur-md p-4 rounded-2xl border border-slate-700/50"
        >
          <div className="flex items-center gap-3">
            <Zap className="text-yellow-400 fill-current" size={28} />
            <h1 className="text-2xl font-bold tracking-wider bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              ZAP QUICK <span className="text-slate-500 text-sm font-medium ml-2">CLOUD</span>
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold ${connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              {connected ? 'ONLINE' : 'OFFLINE'}
            </div>
            <Cpu size={20} className="text-cyan-400" />
          </div>
        </motion.div>

        {/* Mobile LAYOUT WRAPPER */}
        <div className="w-full flex flex-col lg:grid lg:grid-cols-3 gap-6">

          {/* Footer: Sentence Bar (MOVED UP FOR MOBILE) */}
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="order-1 lg:order-3 lg:col-span-3 sticky top-2 z-50 lg:relative lg:top-auto mb-4 lg:mb-0 lg:mt-6 w-full bg-slate-900/95 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-4 lg:p-6 flex items-center justify-between shadow-2xl lg:shadow-none bg-opacity-100"
          >
            <div className="flex items-center gap-4 text-slate-400">
              <Mic size={24} />
              <span className="text-xs lg:text-sm font-bold uppercase tracking-widest hidden sm:block">Constructed Sentence</span>
            </div>
            <div className="flex-1 text-right">
              <span className="text-2xl lg:text-3xl font-mono text-cyan-300 break-words leading-tight">
                {data.sentence || "..."}
                <span className="animate-pulse">_</span>
              </span>
            </div>
          </motion.div>

          {/* Left Panel: Statistics */}
          <div className="order-3 lg:order-1 col-span-1 flex flex-col gap-6">
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 flex-1 relative overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-slate-900/90 pointer-events-none" />
              <h2 className="text-slate-400 text-sm uppercase tracking-widest font-bold mb-4 flex items-center gap-2">
                <Activity size={16} /> Live Feed
              </h2>

              <div className="space-y-4 font-mono">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span>Status</span>
                  <span className="text-green-400">ACTIVE</span>
                </div>
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span>Latency</span>
                  <span className="text-cyan-400">~80ms</span>
                </div>
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span>Mode</span>
                  <span className="text-purple-400">CLOUD</span>
                </div>
              </div>

              <div className="mt-8">
                <h3 className="text-slate-400 text-xs uppercase mb-2">Confidence Level</h3>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                    animate={{ width: `${(data.confidence || 0) * 100}%` }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                </div>
              </div>
            </motion.div>
          </div>

          {/* Center Panel: Main Video Feed / Camera */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="order-2 lg:order-2 lg:col-span-2 relative bg-black rounded-3xl overflow-hidden shadow-2xl border border-slate-700/50 shadow-cyan-900/20 aspect-video lg:aspect-auto h-auto lg:h-[500px]"
          >
            {/* Real Webcam feed (mirrored) */}
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="w-full h-full object-cover scale-x-[-1]"
            />

            {/* HUD Overlay */}
            <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/90 to-transparent p-4 lg:p-8 pt-20">
              <AnimatePresence mode="wait">
                {data.prediction !== -1 && (
                  <motion.div
                    key={data.prediction}
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: -20, opacity: 0 }}
                    className="text-4xl lg:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-slate-400 drop-shadow-2xl"
                  >
                    {actions[data.prediction]}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Live Indicator */}
            <div className="absolute top-6 right-6 flex items-center gap-2 bg-red-500/10 backdrop-blur-md px-3 py-1 rounded-full border border-red-500/20">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce" />
              <span className="text-red-500 text-xs font-bold tracking-widest">LIVE</span>
            </div>
          </motion.div>

        </div>
      </div>

      {/* interaction Overlay */}
      <Overlay setConnected={setConnected} />

    </div>
  );
}

function Overlay({ setConnected }) {
  const [dismissed, setDismissed] = useState(false);

  const enableAudio = () => {
    // Unlock Audio Context
    const synth = window.speechSynthesis;
    const u = new SpeechSynthesisUtterance("Audio System Online");
    synth.speak(u);
    setDismissed(true);
  };

  if (dismissed) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={enableAudio}
        className="bg-cyan-600 hover:bg-cyan-500 text-white px-8 py-4 rounded-full text-xl font-bold shadow-lg shadow-cyan-500/50 flex items-center gap-3"
      >
        <Zap className="fill-current" />
        START CAMERA & AUDIO
      </motion.button>
    </div>
  );
}

export default App;
