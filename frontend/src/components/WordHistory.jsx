/**
 * WordHistory — Scrollable list of recognised words with corrections shown.
 */

export default function WordHistory({ words, wordEvents }) {
  return (
    <div className="card word-history" id="word-history">
      <div className="card__header">
        <h2 className="card__title">
          <span className="card__icon">📝</span>
          Word History
        </h2>
        {words.length > 0 && (
          <span className="status-indicator status-indicator--connected">
            {words.length} word{words.length > 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="word-history__list">
        {words.length > 0 ? (
          words.map((word, index) => {
            const event = wordEvents[index];
            return (
              <div className="word-history__item" key={index}>
                <span className="word-history__number">#{index + 1}</span>
                <span className="word-history__word">{word}</span>
                {event?.original_chars && event.original_chars !== word && (
                  <span className="word-history__original">
                    signed: {event.original_chars}
                  </span>
                )}
              </div>
            );
          })
        ) : (
          <div className="word-history__empty">
            Words will appear here as you sign them
          </div>
        )}
      </div>
    </div>
  );
}
