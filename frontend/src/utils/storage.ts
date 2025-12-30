/** LocalStorage utilities for session management. */

const SESSION_ID_KEY = "spur_chat_session_id";
const USED_SUGGESTIONS_KEY = "spur_chat_used_suggestions";

export const storage = {
  getSessionId(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(SESSION_ID_KEY);
  },

  setSessionId(sessionId: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  },

  clearSessionId(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(SESSION_ID_KEY);
  },

  getUsedSuggestions(): string[] {
    if (typeof window === "undefined") return [];
    const stored = localStorage.getItem(USED_SUGGESTIONS_KEY);
    if (!stored) return [];
    try {
      return JSON.parse(stored);
    } catch {
      return [];
    }
  },

  setUsedSuggestions(suggestions: string[]): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(USED_SUGGESTIONS_KEY, JSON.stringify(suggestions));
  },

  clearUsedSuggestions(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(USED_SUGGESTIONS_KEY);
  },
};

