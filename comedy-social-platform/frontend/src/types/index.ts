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
  createdAt: string;
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
  createdAt: string;
  user: {
    username: string;
    displayName: string;
    profilePicture?: string;
    verified: boolean;
  };
}

export interface AuthResponse {
  token: string;
  user: Partial<User>;
  message: string;
}

export interface CreatePostData {
  content: string;
  humorTags: HumorStyle[];
  isAIGenerated?: boolean;
  media?: File;
}