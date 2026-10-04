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
