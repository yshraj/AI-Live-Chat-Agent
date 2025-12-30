import { useState, FormEvent, KeyboardEvent, useRef, useEffect } from "react";
import { storage } from "../../utils/storage";
import "./MessageInput.css";

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  sessionId?: string | null;
}

// Pool of 12 support-focused suggestions
const SUGGESTION_POOL = [
  "What is your return policy?",
  "How can you help me?",
  "What are your shipping options?",
  "Tell me about your products",
  "What is your refund policy?",
  "How do I track my order?",
  "What are your delivery times?",
  "Do you offer international shipping?",
  "How do I exchange an item?",
  "What payment methods do you accept?",
  "What is your customer service hours?",
  "Can I cancel my order?"
];

// Helper function to shuffle array
const shuffleArray = <T,>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

export function MessageInput({ onSendMessage, disabled, sessionId }: MessageInputProps) {
  const [input, setInput] = useState("");
  const [availableSuggestions, setAvailableSuggestions] = useState<string[]>([]);
  const [displayedSuggestions, setDisplayedSuggestions] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize suggestions on mount and when sessionId changes (cleared)
  useEffect(() => {
    initializeSuggestions();
  }, [sessionId]);

  const initializeSuggestions = () => {
    // Get used suggestions from storage
    const usedSuggestions = storage.getUsedSuggestions();
    
    // Filter out used suggestions from pool
    const available = SUGGESTION_POOL.filter(s => !usedSuggestions.includes(s));
    
    setAvailableSuggestions(available);
    
    // Display 2 random available suggestions
    if (available.length > 0) {
      const shuffled = shuffleArray(available);
      setDisplayedSuggestions(shuffled.slice(0, 2));
    } else {
      setDisplayedSuggestions([]);
    }
  };

  const markSuggestionAsUsed = (suggestion: string) => {
    // Get current used suggestions
    const usedSuggestions = storage.getUsedSuggestions();
    
    // Add this suggestion to used list
    const updatedUsed = [...usedSuggestions, suggestion];
    storage.setUsedSuggestions(updatedUsed);
    
    // Remove from available
    const updatedAvailable = availableSuggestions.filter(s => s !== suggestion);
    setAvailableSuggestions(updatedAvailable);
    
    // Update displayed suggestions - remove the used one and add a random replacement
    if (updatedAvailable.length > 0) {
      // Remove the used suggestion from displayed
      const remainingDisplayed = displayedSuggestions.filter(s => s !== suggestion);
      
      // If we need to fill a slot, pick a random one from available
      if (remainingDisplayed.length < 2 && updatedAvailable.length > 0) {
        const notDisplayed = updatedAvailable.filter(s => !remainingDisplayed.includes(s));
        if (notDisplayed.length > 0) {
          const randomIndex = Math.floor(Math.random() * notDisplayed.length);
          remainingDisplayed.push(notDisplayed[randomIndex]);
        }
      }
      
      setDisplayedSuggestions(remainingDisplayed);
    } else {
      // No more suggestions available
      setDisplayedSuggestions([]);
    }
  };

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
      // Mark suggestion as used
      markSuggestionAsUsed(suggestion);
      // Send the message
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
      {displayedSuggestions.length > 0 && (
        <div className="message-input__suggestions">
          {displayedSuggestions.map((suggestion, index) => (
            <button
              key={`${suggestion}-${index}`}
              type="button"
              className="message-input__suggestion-button"
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={disabled}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
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

