// Shapes of the API responses, after client.ts converts keys to camelCase.

export interface User {
  id: number;
  username: string;
  schoolEmail: string;
  collegeName: string;
  graduationYear: number | null;
  isEduVerified: boolean;
}

export interface MyProfile {
  id: number;
  bio: string;
  interests: string[];
  likes: string[];
  dislikes: string[];
}

export interface PublicProfile {
  id: number;
  /** Send connection requests / open chats with this id (not the profile id). */
  userId: number;
  username: string;
  collegeName: string;
  graduationYear: number | null;
  bio: string;
  interests: string[];
  likes: string[];
  dislikes: string[];
}

export interface Question {
  id: number;
  text: string;
  choices: string[];
}

export interface Answer {
  question: number;
  choice: string;
}

// --- Connections (see docs/api.md "Contract: connections") ---

/** How a connection looks from my side. */
export type ConnectionStatus = "connected" | "incoming" | "outgoing";

/** The other person in a connection or chat. */
export interface OtherUser {
  id: number;
  username: string;
  collegeName: string;
  graduationYear: number | null;
  /** Null until they set up a profile. */
  profileId: number | null;
}

export interface Connection {
  id: number;
  status: ConnectionStatus;
  user: OtherUser;
  createdAt: string;
  respondedAt: string | null;
}

export interface ConnectionWith {
  status: ConnectionStatus | "none";
  connection: Connection | null;
}

// --- Chat (see docs/api.md "Contract: chat") ---

export interface Message {
  id: number;
  conversationId: number;
  senderId: number;
  body: string;
  createdAt: string;
  readAt: string | null;
}

export interface Conversation {
  id: number;
  otherUser: OtherUser;
  lastMessage: Message | null;
  unreadCount: number;
  /** False after disconnecting: history is readable but sending is blocked. */
  isConnected: boolean;
  updatedAt: string;
}

export interface MessagePage {
  results: Message[];
  hasMore: boolean;
}
