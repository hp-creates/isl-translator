/**
 * StatusIndicator — Connection and model status display.
 */

export default function StatusIndicator({ isConnected, isActive }) {
  return (
    <div className="header__badge" id="status-indicator">
      <span
        className={`header__status-dot ${isConnected ? 'header__status-dot--connected' : ''}`}
      />
      <span>
        {isConnected
          ? isActive
            ? 'Translating...'
            : 'Connected — Ready'
          : 'Disconnected'}
      </span>
    </div>
  );
}
