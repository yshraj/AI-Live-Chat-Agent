import { useChat } from "../../hooks/useChat";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { TypingIndicator } from "../TypingIndicator";
import "./ChatWidget.css";

export function ChatWidget() {
  const { messages, isLoading, isLoadingHistory, error, sendMessage, clearChat } = useChat();

  return (
    <div className="chat-widget">
      <div className="chat-widget__header">
        <h2 className="chat-widget__title">
          <span className="chat-widget__title-icon"></span>
          AI Support Agent
        </h2>
        <button className="chat-widget__clear" onClick={clearChat}>
          Clear
        </button>
      </div>
      
      {isLoadingHistory ? (
        <div className="message-list">
          <div className="message-list__empty">
            <p>Loading conversation history...</p>
          </div>
        </div>
      ) : (
        <MessageList messages={messages} />
      )}
      
      {isLoading && <TypingIndicator />}
      
      {error && (
        <div className="chat-widget__error">
          {error}
        </div>
      )}
      
      <MessageInput onSendMessage={sendMessage} disabled={isLoading || isLoadingHistory} />
    </div>
  );
}

