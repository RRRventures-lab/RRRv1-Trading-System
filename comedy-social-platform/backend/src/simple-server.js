const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 5001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('uploads'));

// Mock data
const mockPosts = [
  {
    id: '1',
    userId: 'user1',
    content: "Why don't scientists trust atoms? Because they make up everything! 😂",
    mediaUrl: null,
    mediaType: null,
    humorTags: ['wordplay'],
    likes: 42,
    laughReacts: 28,
    comments: 5,
    shares: 3,
    isAIGenerated: false,
    createdAt: new Date().toISOString(),
    user: {
      username: 'comedyking',
      displayName: 'Comedy King',
      profilePicture: null,
      verified: true
    }
  },
  {
    id: '2',
    userId: 'user2',
    content: "I told my wife she was drawing her eyebrows too high. She looked surprised. 🤔",
    mediaUrl: null,
    mediaType: null,
    humorTags: ['observational'],
    likes: 35,
    laughReacts: 41,
    comments: 8,
    shares: 2,
    isAIGenerated: false,
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    user: {
      username: 'laughmaster',
      displayName: 'Laugh Master',
      profilePicture: null,
      verified: false
    }
  },
  {
    id: '3',
    userId: 'user3',
    content: "My therapist says I have a preoccupation with vengeance. We'll see about that... 😈",
    mediaUrl: null,
    mediaType: null,
    humorTags: ['dark'],
    likes: 67,
    laughReacts: 52,
    comments: 12,
    shares: 8,
    isAIGenerated: true,
    createdAt: new Date(Date.now() - 7200000).toISOString(),
    user: {
      username: 'darkhumor_ai',
      displayName: 'Dark Humor AI',
      profilePicture: null,
      verified: false
    }
  }
];

const mockUser = {
  id: 'user1',
  username: 'comedyking',
  email: 'comedy@example.com',
  displayName: 'Comedy King',
  bio: 'Making the world laugh, one joke at a time! 🎭',
  profilePicture: null,
  comedyPreferences: {
    humorStyles: ['wordplay', 'observational', 'wholesome'],
    topics: ['tech', 'daily life', 'animals'],
    preferredContentTypes: ['text', 'image']
  },
  followers: 1234,
  following: 567,
  postsCount: 89,
  verified: true,
  createdAt: new Date(Date.now() - 86400000 * 30).toISOString()
};

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'ComedyGram API is running!' });
});

// Mock auth
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;

  if (username && password) {
    res.json({
      message: 'Login successful',
      token: 'mock-jwt-token-' + Date.now(),
      user: mockUser
    });
  } else {
    res.status(400).json({ error: 'Username and password required' });
  }
});

app.post('/api/auth/register', (req, res) => {
  const { username, email, password, displayName } = req.body;

  if (username && email && password && displayName) {
    res.status(201).json({
      message: 'User created successfully',
      token: 'mock-jwt-token-' + Date.now(),
      user: {
        ...mockUser,
        username,
        email,
        displayName
      }
    });
  } else {
    res.status(400).json({ error: 'All fields are required' });
  }
});

// Mock posts
app.get('/api/posts', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 10;
  const start = (page - 1) * limit;
  const end = start + limit;

  const paginatedPosts = mockPosts.slice(start, end);
  res.json(paginatedPosts);
});

app.post('/api/posts', (req, res) => {
  const { content, humorTags } = req.body;

  const newPost = {
    id: Date.now().toString(),
    userId: 'user1',
    content: content || '',
    mediaUrl: null,
    mediaType: null,
    humorTags: humorTags || [],
    likes: 0,
    laughReacts: 0,
    comments: 0,
    shares: 0,
    isAIGenerated: false,
    createdAt: new Date().toISOString(),
    user: mockUser
  };

  mockPosts.unshift(newPost);
  res.status(201).json(newPost);
});

// Mock interactions
app.post('/api/posts/:postId/like', (req, res) => {
  const postId = req.params.postId;
  const post = mockPosts.find(p => p.id === postId);

  if (post) {
    post.likes += 1;
    res.json({ liked: true, message: 'Post liked' });
  } else {
    res.status(404).json({ error: 'Post not found' });
  }
});

app.post('/api/posts/:postId/laugh', (req, res) => {
  const postId = req.params.postId;
  const post = mockPosts.find(p => p.id === postId);

  if (post) {
    post.laughReacts += 1;
    res.json({ laughed: true, message: 'Laugh reaction added' });
  } else {
    res.status(404).json({ error: 'Post not found' });
  }
});

// Mock AI features
app.post('/api/ai/generate-joke', (req, res) => {
  const { humorStyle } = req.body;

  const jokes = {
    dark: "My therapist says I have a preoccupation with vengeance. We'll see about that.",
    wholesome: "Why don't scientists trust atoms? Because they make up everything!",
    wordplay: "I wondered why the baseball kept getting bigger. Then it hit me.",
    observational: "Ever notice how 'abbreviated' is such a long word?"
  };

  res.json({
    content: jokes[humorStyle] || jokes.wholesome,
    humorStyle,
    isAIGenerated: true
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🎭 ComedyGram Mock API is ready!`);
  console.log(`📝 Health check: http://localhost:${PORT}/health`);
});