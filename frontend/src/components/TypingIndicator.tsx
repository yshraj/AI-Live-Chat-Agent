import "./TypingIndicator.css";

export function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-indicator__avatar"></div>
      <div className="typing-indicator__container">
        <div className="typing-indicator__dot"></div>
        <div className="typing-indicator__dot"></div>
        <div className="typing-indicator__dot"></div>
        <span className="typing-indicator__text">Analyzing data, please wait...</span>
      </div>
    </div>
  );
}

