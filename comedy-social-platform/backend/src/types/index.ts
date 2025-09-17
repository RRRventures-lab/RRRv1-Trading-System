export interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  bio?: string;
  profilePicture?: string;
  comedyPreferences: ComedyPreferences;
  followers: number;
  following: number;
  postsCount: number;
  verified: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface ComedyPreferences {
  humorStyles: HumorStyle[];
  topics: string[];
  preferredContentTypes: ContentType[];
}

export enum HumorStyle {
  DARK = 'dark',
  WHOLESOME = 'wholesome',
  SATIRICAL = 'satirical',
  OBSERVATIONAL = 'observational',
  SURREAL = 'surreal',
  WORDPLAY = 'wordplay',
  PHYSICAL = 'physical',
  SELF_DEPRECATING = 'self_deprecating'
}

export enum ContentType {
  IMAGE = 'image',
  VIDEO = 'video',
  TEXT = 'text',
  GIF = 'gif'
}

export interface Post {
  id: string;
  userId: string;
  content: string;
  mediaUrl?: string;
  mediaType?: ContentType;
  humorTags: HumorStyle[];
  likes: number;
  laughReacts: number;
  comments: number;
  shares: number;
  isAIGenerated: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface AuthPayload {
  userId: string;
  username: string;
  email: string;
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  displayName: string;
  bio?: string;
}