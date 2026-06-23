/**
 * LiveBuffer — Shows current character buffer and stability progress.
 */

export default function LiveBuffer({
  buffer,
  stabilityProgress,
  stabilityRequired,
  currentChar,
}) {
  const progressPercent =
    stabilityRequired > 0
      ? Math.min((stabilityProgress / stabilityRequired) * 100, 100)
      : 0;

  return (
    <div className="card live-buffer" id="live-buffer">
      <div className="card__header">
        <h2 className="card__title">
          <span className="card__icon">🔤</span>
          Character Buffer
        </h2>
        {currentChar && (
          <span className="status-indicator status-indicator--active">
            Detecting: {currentChar}
          </span>
        )}
      </div>

      <div className="buffer__chars">
        {buffer.length > 0 ? (
          buffer.split('').map((char, index) => (
            <span className="buffer__char" key={`${index}-${char}`}>
              {char}
            </span>
          ))
        ) : (
          <span className="buffer__empty">
            Sign letters to build a word...
          </span>
        )}
      </div>

      <div className="stability">
        <div className="stability__label">
          <span>Stability</span>
          <span>
            {stabilityProgress} / {stabilityRequired} frames
          </span>
        </div>
        <div className="stability__bar">
          <div
            className="stability__fill"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}
