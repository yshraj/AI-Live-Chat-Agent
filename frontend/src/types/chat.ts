export type MessageSender = "user" | "ai";

export interface Message {
  sender: MessageSender;
  content: string;
  created_at?: string;
}

export interface ChatMessageRequest {
  message: string;
  sessionId?: string;
}

export interface ChatMessageResponse {
  reply: string;
  sessionId: string;
}

export interface ChatHistoryResponse {
  messages: Message[];
}

