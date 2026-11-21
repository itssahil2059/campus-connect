// Shapes of the API responses, after client.ts converts keys to camelCase.

export interface User {
  id: number;
  username: string;
  schoolEmail: string;
  collegeName: string;
  graduationYear: number | null;
  isEduVerified: boolean;
}

export type Gender = "woman" | "man" | "non_binary" | "other" | "prefer_not_to_say";

/** Same values and labels as Profile.Gender on the backend. */
export const GENDER_OPTIONS: { value: Gender; label: string }[] = [
  { value: "woman", label: "Woman" },
  { value: "man", label: "Man" },
  { value: "non_binary", label: "Non-binary" },
  { value: "other", label: "Other" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

export interface MyProfile {
  id: number;
  bio: string;
  /** "YYYY-MM-DD". Private: other students only see `age`. */
  dateOfBirth: string | null;
  gender: Gender | "";
  city: string;
  interests: string[];
  likes: string[];
  dislikes: string[];
  links: string[];
  /** Processed photo (<= 1080 px JPEG) and 200 px thumbnail; null without a photo. Pass through mediaUrl(). */
  photoUrl: string | null;
  thumbnailUrl: string | null;
}

export interface PublicProfile {
  id: number;
  /** Send connection requests / open chats with this id (not the profile id). */
  userId: number;
  username: string;
  collegeName: string;
  graduationYear: number | null;
  age: number | null;
  gender: Gender | "";
  city: string;
  bio: string;
  interests: string[];
  likes: string[];
  dislikes: string[];
  links: string[];
  photoUrl: string | null;
  thumbnailUrl: string | null;
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
  /** Their 200 px photo thumbnail, or null (show initials). */
  thumbnailUrl: string | null;
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
