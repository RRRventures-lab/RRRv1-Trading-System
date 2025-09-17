import { Request, Response } from 'express';
import { query } from '../utils/database';
import { hashPassword, comparePassword, generateToken, validateEmail, validateUsername, validatePassword } from '../utils/auth';
import { CreateUserData, AuthPayload } from '../types';

export const register = async (req: Request, res: Response) => {
  try {
    const { username, email, password, displayName, bio }: CreateUserData = req.body;

    // Validation
    if (!username || !email || !password || !displayName) {
      return res.status(400).json({ error: 'All required fields must be provided' });
    }

    if (!validateEmail(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    if (!validateUsername(username)) {
      return res.status(400).json({ error: 'Username must be 3-30 characters, alphanumeric and underscores only' });
    }

    if (!validatePassword(password)) {
      return res.status(400).json({ error: 'Password must be at least 8 characters long' });
    }

    // Check if user already exists
    const existingUser = await query(
      'SELECT id FROM users WHERE username = $1 OR email = $2',
      [username, email]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({ error: 'Username or email already exists' });
    }

    // Hash password and create user
    const passwordHash = await hashPassword(password);

    const result = await query(
      `INSERT INTO users (username, email, password_hash, display_name, bio)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, username, email, display_name, bio, created_at`,
      [username, email, passwordHash, displayName, bio || null]
    );

    const user = result.rows[0];
    const tokenPayload: AuthPayload = {
      userId: user.id,
      username: user.username,
      email: user.email
    };

    const token = generateToken(tokenPayload);

    res.status(201).json({
      message: 'User created successfully',
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        displayName: user.display_name,
        bio: user.bio,
        createdAt: user.created_at
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const login = async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Find user by username or email
    const result = await query(
      'SELECT id, username, email, password_hash, display_name FROM users WHERE username = $1 OR email = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = result.rows[0];
    const isValidPassword = await comparePassword(password, user.password_hash);

    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const tokenPayload: AuthPayload = {
      userId: user.id,
      username: user.username,
      email: user.email
    };

    const token = generateToken(tokenPayload);

    res.json({
      message: 'Login successful',
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        displayName: user.display_name
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getProfile = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;

    const result = await query(
      `SELECT id, username, email, display_name, bio, profile_picture,
              comedy_preferences, followers, following, posts_count,
              verified, created_at
       FROM users WHERE id = $1`,
      [userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const user = result.rows[0];
    res.json({
      id: user.id,
      username: user.username,
      email: user.email,
      displayName: user.display_name,
      bio: user.bio,
      profilePicture: user.profile_picture,
      comedyPreferences: user.comedy_preferences,
      followers: user.followers,
      following: user.following,
      postsCount: user.posts_count,
      verified: user.verified,
      createdAt: user.created_at
    });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};