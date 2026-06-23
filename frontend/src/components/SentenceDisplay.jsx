/**
 * SentenceDisplay — Shows the growing sentence with refinement support.
 */

export default function SentenceDisplay({ sentence, isRefined }) {
  return (
    <div className="card sentence" id="sentence-display">
      <div className="card__header">
        <h2 className="card__title">
          <span className="card__icon">💬</span>
          Sentence
        </h2>
        {isRefined && (
          <span className="sentence__refined-badge">✨ AI Refined</span>
        )}
      </div>

      <div
        className={`sentence__text ${isRefined ? 'sentence__text--refined' : ''}`}
      >
        {sentence ? (
          <span>{sentence}</span>
        ) : (
          <span className="sentence__empty">
            Your translated sentence will appear here...
          </span>
        )}
      </div>
    </div>
  );
}
