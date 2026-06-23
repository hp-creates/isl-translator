/**
 * ControlPanel — Start/Stop/NextWord/Finish/Clear buttons.
 */

export default function ControlPanel({
  isActive,
  isConnected,
  hasWords,
  hasBuffer,
  onStart,
  onStop,
  onNextWord,
  onFinish,
  onClear,
}) {
  return (
    <div className="controls" id="control-panel">
      {!isActive ? (
        <button
          className="btn btn--success"
          onClick={onStart}
          disabled={!isConnected}
          id="btn-start"
        >
          ▶ Start
        </button>
      ) : (
        <button className="btn btn--danger" onClick={onStop} id="btn-stop">
          ⏹ Stop
        </button>
      )}

      <button
        className="btn btn--primary"
        onClick={onNextWord}
        disabled={!isActive || !hasBuffer}
        id="btn-next-word"
      >
        ➡ Next Word
      </button>

      <button
        className="btn btn--primary"
        onClick={onFinish}
        disabled={!hasWords}
        id="btn-finish"
      >
        ✨ Finish Sentence
      </button>

      <button
        className="btn btn--ghost"
        onClick={onClear}
        disabled={!hasWords && !hasBuffer}
        id="btn-clear"
      >
        🗑 Clear
      </button>
    </div>
  );
}
