import { Message as MessageType } from "../../types/chat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Message.css";

interface MessageProps {
  message: MessageType;
}

export function Message({ message }: MessageProps) {
  const isUser = message.sender === "user";

  return (
    <div className={`message ${isUser ? "message--user" : "message--ai"}`}>
      {!isUser && (
        <div className="message__avatar">
          <span className="message__avatar-icon">✨</span>
        </div>
      )}
      <div className="message__content">
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="message__paragraph">{children}</p>,
              ul: ({ children }) => <ul className="message__list">{children}</ul>,
              ol: ({ children }) => <ol className="message__list message__list--ordered">{children}</ol>,
              li: ({ children }) => <li className="message__list-item">{children}</li>,
              strong: ({ children }) => <strong className="message__strong">{children}</strong>,
              em: ({ children }) => <em className="message__em">{children}</em>,
              code: ({ children, className }) => {
                const isInline = !className;
                return isInline ? (
                  <code className="message__code-inline">{children}</code>
                ) : (
                  <code className="message__code-block">{children}</code>
                );
              },
              h1: ({ children }) => <h1 className="message__heading message__heading--1">{children}</h1>,
              h2: ({ children }) => <h2 className="message__heading message__heading--2">{children}</h2>,
              h3: ({ children }) => <h3 className="message__heading message__heading--3">{children}</h3>,
              blockquote: ({ children }) => <blockquote className="message__blockquote">{children}</blockquote>,
              a: ({ href, children }) => (
                <a href={href} className="message__link" target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}

