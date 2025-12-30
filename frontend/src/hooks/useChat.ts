import { useState, useCallback, useEffect } from "react";
import { Message } from "../types/chat";
import { api, ApiError } from "../services/api";
import { storage } from "../utils/storage";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Load conversation history from backend
  const loadHistory = useCallback(async (sessionIdToLoad: string) => {
    if (!sessionIdToLoad) return;
    
    setIsLoadingHistory(true);
    setError(null);
    
    try {
      const response = await api.getHistory(sessionIdToLoad);
      
      // Map backend messages to frontend Message format
      const loadedMessages: Message[] = response.messages.map((msg: any) => ({
        sender: msg.sender as "user" | "ai",
        content: msg.content,
        created_at: msg.created_at,
      }));
      
      setMessages(loadedMessages);
    } catch (err) {
      // Don't show error for empty history (404 or no messages)
      // Only log for debugging
      if (err instanceof ApiError && err.status !== 404) {
        console.warn("Failed to load chat history:", err);
      }
      // Start with empty messages if history load fails
      setMessages([]);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  // Load session ID from storage on mount and fetch history
  useEffect(() => {
    const savedSessionId = storage.getSessionId();
    if (savedSessionId) {
      setSessionId(savedSessionId);
      // Load conversation history
      loadHistory(savedSessionId);
    }
  }, [loadHistory]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      const userMessage: Message = {
        sender: "user",
        content: content.trim(),
      };

      // Add user message immediately
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.sendMessage(content.trim(), sessionId || undefined);
        
        // Update session ID
        if (response.sessionId) {
          setSessionId(response.sessionId);
          storage.setSessionId(response.sessionId);
        }

        // Add AI response
        const aiMessage: Message = {
          sender: "ai",
          content: response.reply,
        };
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof ApiError
            ? err.message
            : "Failed to send message. Please try again.";
        setError(errorMessage);
        
        // Remove user message on error (optional - you might want to keep it)
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    storage.clearSessionId();
    setSessionId(null);
  }, []);

  return {
    messages,
    isLoading,
    isLoadingHistory,
    error,
    sessionId,
    sendMessage,
    clearChat,
  };
}

