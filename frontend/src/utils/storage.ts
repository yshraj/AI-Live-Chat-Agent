/** LocalStorage utilities for session management. */

const SESSION_ID_KEY = "spur_chat_session_id";

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
};

