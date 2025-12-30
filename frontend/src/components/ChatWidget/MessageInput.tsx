import { useState, FormEvent, KeyboardEvent, useRef, useEffect } from "react";
import "./MessageInput.css";

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  "Create in-depth analysis",
  "Identify actionable tasks",
  "Summarize key points",
  "Write an email to the team"
];

export function MessageInput({ onSendMessage, disabled }: MessageInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input);
      setInput("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (!disabled) {
      onSendMessage(suggestion);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="message-input">
      <div className="message-input__suggestions">
        {SUGGESTIONS.slice(0, 2).map((suggestion, index) => (
          <button
            key={index}
            type="button"
            className="message-input__suggestion-button"
            onClick={() => handleSuggestionClick(suggestion)}
            disabled={disabled}
          >
            {suggestion}
          </button>
        ))}
      </div>
      <form className="message-input__form" onSubmit={handleSubmit}>
        <div className="message-input__field-wrapper">
          <textarea
            ref={textareaRef}
            className="message-input__field"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask, write or search for anything..."
            disabled={disabled}
            rows={1}
            maxLength={2000}
            data-has-icon="true"
          />
        </div>
        <button
          type="submit"
          className="message-input__button"
          disabled={!input.trim() || disabled}
          aria-label="Send message"
        />
      </form>
    </div>
  );
}

