# ComedyGram - Comedy Social Platform

A complete Instagram-like social platform tailored specifically for comedy content, featuring AI-powered humor recommendations, real-time interactions, and comprehensive content moderation.

## Features

### 🎭 Core Social Features
- **User Authentication & Profiles** - Secure JWT-based auth with customizable profiles
- **Post Creation & Media Upload** - Support for images, videos, and text posts
- **Infinite Scroll Feed** - Optimized feed with pagination and real-time updates
- **Social Interactions** - Likes, laugh reactions, comments, and follows
- **Real-time Notifications** - Socket.io powered instant notifications

### 😂 Comedy-Specific Features
- **Humor Style Tags** - 8 different comedy categories (dark, wholesome, satirical, etc.)
- **Laugh Reactions** - Special reaction type beyond traditional likes
- **AI Content Analysis** - Automatic humor style detection
- **Personalized Recommendations** - AI-powered content based on user preferences

### 🤖 AI-Powered Features
- **Content Generation** - AI joke generation based on humor preferences
- **Content Moderation** - Automated inappropriate content detection
- **Humor Analysis** - ML-powered categorization of posts
- **Personalized Feed** - Algorithm-driven content recommendations

### 🛡️ Moderation & Safety
- **Content Reporting** - User-driven content flagging system
- **User Blocking** - Comprehensive user blocking functionality
- **Admin Dashboard** - Complete moderation tools and analytics
- **Automated Moderation** - AI-powered content filtering

## Tech Stack

### Backend
- **Node.js** with **Express** - REST API server
- **TypeScript** - Type-safe development
- **PostgreSQL** - Primary database
- **Redis** - Session management and caching
- **Socket.io** - Real-time communications
- **JWT** - Authentication and authorization
- **Multer** - File upload handling
- **bcryptjs** - Password hashing

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe frontend development
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **React Query** - State management and data fetching
- **Axios** - HTTP client
- **Socket.io Client** - Real-time connectivity

### Infrastructure
- **Docker** - Containerization for development
- **AWS S3** - Media storage (production)
- **CloudFront CDN** - Content delivery

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- PostgreSQL 15+
- Redis 7+
- Docker (optional, for easy setup)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd comedy-social-platform
```

### 2. Setup with Docker (Recommended)
```bash
# Start PostgreSQL and Redis
docker-compose up -d

# The services will be available at:
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### 3. Backend Setup
```bash
cd backend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Edit .env with your settings (database credentials, JWT secret, etc.)
# Default database: postgresql://postgres:password@localhost:5432/comedy_platform

# Start development server
npm run dev
```

The backend will be available at `http://localhost:5000`

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:5000/api" > .env.local

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)
```bash
PORT=5000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/comedy_platform
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRE=7d

# File Upload
UPLOAD_PATH=./uploads
MAX_FILE_SIZE=10485760

# OpenAI (Optional - for real AI features)
OPENAI_API_KEY=your-openai-api-key

# AWS (Production)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket
AWS_REGION=us-east-1
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile/:userId` - Get user profile

### Posts
- `GET /api/posts` - Get posts feed
- `POST /api/posts` - Create new post
- `GET /api/posts/:postId` - Get specific post
- `DELETE /api/posts/:postId` - Delete post

### Interactions
- `POST /api/posts/:postId/like` - Like/unlike post
- `POST /api/posts/:postId/laugh` - Laugh react to post
- `POST /api/posts/:postId/comments` - Add comment
- `GET /api/posts/:postId/comments` - Get comments

### Social Features
- `POST /api/users/:userId/follow` - Follow/unfollow user
- `GET /api/users/:userId/followers` - Get followers
- `GET /api/users/:userId/following` - Get following
- `GET /api/users/search` - Search users
- `GET /api/users/suggested` - Get suggested users

### AI Features
- `POST /api/ai/generate-joke` - Generate AI joke
- `POST /api/ai/analyze-content` - Analyze humor style
- `GET /api/ai/personalized-content` - Get personalized content

### Notifications
- `GET /api/notifications` - Get notifications
- `PUT /api/notifications/:id/read` - Mark as read
- `PUT /api/notifications/read-all` - Mark all as read

### Moderation
- `POST /api/posts/:postId/report` - Report post
- `POST /api/users/:userId/report` - Report user
- `POST /api/users/:userId/block` - Block user
- `GET /api/reports` - Get reports (admin)

## Database Schema

The platform uses PostgreSQL with the following main tables:

- **users** - User profiles and authentication
- **posts** - User posts with content and metadata
- **likes** - Post likes tracking
- **laugh_reactions** - Comedy-specific reactions
- **comments** - Post comments
- **follows** - User following relationships
- **notifications** - Real-time notifications
- **reports** - Content and user reports
- **admin_actions** - Admin action logging

## Development

### Building for Production

#### Backend
```bash
cd backend
npm run build
npm start
```

#### Frontend
```bash
cd frontend
npm run build
npm start
```

### Code Structure

```
comedy-social-platform/
├── backend/
│   ├── src/
│   │   ├── controllers/     # Route handlers
│   │   ├── middleware/      # Auth and validation
│   │   ├── models/          # Database models
│   │   ├── routes/          # API routes
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Helper functions
│   │   └── types/           # TypeScript types
│   └── uploads/             # Media uploads
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app directory
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
└── docker-compose.yml       # Development services
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Deployment

### Backend Deployment
- Deploy to platforms like Railway, Render, or AWS
- Set up PostgreSQL and Redis instances
- Configure environment variables
- Set up file storage (AWS S3)

### Frontend Deployment
- Deploy to Vercel, Netlify, or similar
- Configure API URL environment variable
- Set up CDN for optimal performance

## Future Enhancements

- **Mobile App** - React Native implementation
- **Advanced AI** - Integration with GPT-4 for better content generation
- **Video Processing** - Automatic video optimization and thumbnails
- **Analytics Dashboard** - Comprehensive user and content analytics
- **Live Streaming** - Real-time comedy performances
- **Monetization** - Creator economy features
- **Multi-language Support** - Internationalization
- **Voice Posts** - Audio content support

---

Made with ❤️ for the comedy community