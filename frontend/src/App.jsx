/**
 * App — Main application component.
 *
 * Composes all components and manages the global session state.
 * Connects camera frames to WebSocket and routes server responses
 * to the appropriate UI components.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useCamera } from './hooks/useCamera';
import { useWebSocket } from './hooks/useWebSocket';

import CameraFeed from './components/CameraFeed';
import ControlPanel from './components/ControlPanel';
import LiveBuffer from './components/LiveBuffer';
import WordHistory from './components/WordHistory';
import SentenceDisplay from './components/SentenceDisplay';
import StatusIndicator from './components/StatusIndicator';

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `ws://${window.location.hostname}:8000/ws/translate`;

export default function App() {
  // Hooks
  const camera = useCamera(5);
  const ws = useWebSocket(WS_URL);

  // Session state
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [currentChar, setCurrentChar] = useState(null);
  const [confidence, setConfidence] = useState(0);
  const [buffer, setBuffer] = useState('');
  const [stabilityProgress, setStabilityProgress] = useState(0);
  const [stabilityRequired, setStabilityRequired] = useState(5);
  const [words, setWords] = useState([]);
  const [wordEvents, setWordEvents] = useState([]);
  const [sentence, setSentence] = useState('');
  const [isRefined, setIsRefined] = useState(false);
  const [handsDetected, setHandsDetected] = useState(0);

  // Ref for frame loop cleanup
  const frameLoopCleanup = useRef(null);

  // --- Connect to WebSocket on mount ---
  useEffect(() => {
    ws.connect();
    return () => ws.disconnect();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // --- Process incoming WebSocket messages ---
  useEffect(() => {
    if (!ws.lastMessage) return;

    const msg = ws.lastMessage;

    // Update detection state
    if (msg.current_char !== undefined) setCurrentChar(msg.current_char);
    if (msg.confidence !== undefined) setConfidence(msg.confidence);
    if (msg.buffer !== undefined) setBuffer(msg.buffer);
    if (msg.stability_progress !== undefined)
      setStabilityProgress(msg.stability_progress);
    if (msg.stability_required !== undefined)
      setStabilityRequired(msg.stability_required);
    if (msg.words !== undefined) setWords(msg.words);
    if (msg.sentence !== undefined) setSentence(msg.sentence);
    if (msg.is_active !== undefined) setIsSessionActive(msg.is_active);
    if (msg.hands_detected !== undefined) setHandsDetected(msg.hands_detected);

    // Handle events
    if (msg.event === 'word_ready') {
      setWordEvents((prev) => [
        ...prev,
        {
          original_chars: msg.original_chars,
          corrected_word: msg.corrected_word,
        },
      ]);
    }

    if (msg.event === 'sentence_finished') {
      setIsRefined(true);
    }

    if (msg.event === 'cleared') {
      setWordEvents([]);
      setIsRefined(false);
    }
  }, [ws.lastMessage]);

  // --- Start frame capture when session is active ---
  useEffect(() => {
    if (isSessionActive && camera.isActive && ws.isConnected) {
      frameLoopCleanup.current = camera.startFrameLoop((frame) => {
        ws.sendFrame(frame);
      });
    }

    return () => {
      if (frameLoopCleanup.current) {
        frameLoopCleanup.current();
        frameLoopCleanup.current = null;
      }
    };
  }, [isSessionActive, camera.isActive, ws.isConnected]); // eslint-disable-line react-hooks/exhaustive-deps

  // --- Handlers ---
  const handleStart = useCallback(async () => {
    await camera.startCamera();
    ws.sendControl('start');
    setIsRefined(false);
  }, [camera, ws]);

  const handleStop = useCallback(() => {
    ws.sendControl('stop');
    camera.stopCamera();
    setCurrentChar(null);
    setHandsDetected(0);
  }, [camera, ws]);

  const handleNextWord = useCallback(() => {
    ws.sendControl('next_word');
  }, [ws]);

  const handleFinish = useCallback(() => {
    ws.sendControl('finish');
  }, [ws]);

  const handleClear = useCallback(() => {
    ws.sendControl('clear');
    setWords([]);
    setWordEvents([]);
    setSentence('');
    setBuffer('');
    setIsRefined(false);
    setCurrentChar(null);
  }, [ws]);

  return (
    <div className="app">
      {/* Header */}
      <header className="header" id="app-header">
        <h1 className="header__title">🤟 ISL Translator</h1>
        <p className="header__subtitle">
          Indian Sign Language → Text → Sentences
        </p>
        <StatusIndicator
          isConnected={ws.isConnected}
          isActive={isSessionActive}
        />
      </header>

      {/* Main Content Grid */}
      <main className="main-grid">
        {/* Camera + Controls (Left Column) */}
        <CameraFeed
          ref={camera.videoRef}
          isActive={camera.isActive}
          currentChar={currentChar}
          confidence={confidence}
          handsDetected={handsDetected}
        />

        {/* Live Buffer (Right Column, Top) */}
        <LiveBuffer
          buffer={buffer}
          stabilityProgress={stabilityProgress}
          stabilityRequired={stabilityRequired}
          currentChar={currentChar}
        />

        {/* Word History (Right Column, Bottom) */}
        <WordHistory words={words} wordEvents={wordEvents} />

        {/* Sentence (Full Width, Bottom) */}
        <SentenceDisplay sentence={sentence} isRefined={isRefined} />
      </main>

      {/* Controls (Fixed position feel) */}
      <ControlPanel
        isActive={isSessionActive}
        isConnected={ws.isConnected}
        hasWords={words.length > 0}
        hasBuffer={buffer.length > 0}
        onStart={handleStart}
        onStop={handleStop}
        onNextWord={handleNextWord}
        onFinish={handleFinish}
        onClear={handleClear}
      />

      {/* Error display */}
      {(camera.error || ws.error) && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '12px 20px',
            background: 'rgba(255, 107, 107, 0.15)',
            border: '1px solid rgba(255, 107, 107, 0.3)',
            borderRadius: '12px',
            color: '#ff6b6b',
            fontSize: '0.875rem',
            maxWidth: '400px',
            backdropFilter: 'blur(10px)',
            zIndex: 100,
          }}
        >
          ⚠️ {camera.error || ws.error}
        </div>
      )}
    </div>
  );
}
