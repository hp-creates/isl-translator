/**
 * CameraFeed — Displays live camera stream with detection overlay.
 */

import { forwardRef } from 'react';

const CameraFeed = forwardRef(function CameraFeed(
  { isActive, currentChar, confidence, handsDetected },
  ref
) {
  return (
    <div className="card camera" id="camera-feed">
      <div className="card__header">
        <h2 className="card__title">
          <span className="card__icon">📹</span>
          Camera Feed
        </h2>
        {isActive && handsDetected > 0 && (
          <span className="status-indicator status-indicator--active">
            {handsDetected} hand{handsDetected > 1 ? 's' : ''} detected
          </span>
        )}
      </div>

      <div className="camera__video-container">
        <video ref={ref} className="camera__video" playsInline muted />

        {!isActive && (
          <div className="camera__placeholder">
            <span className="camera__placeholder-icon">🤟</span>
            <p>Press Start to begin translating</p>
          </div>
        )}

        {isActive && currentChar && (
          <div className="camera__overlay">
            <span className="camera__detected-char" key={currentChar}>
              {currentChar}
            </span>
            <span className="camera__confidence">
              {confidence.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
});

export default CameraFeed;
