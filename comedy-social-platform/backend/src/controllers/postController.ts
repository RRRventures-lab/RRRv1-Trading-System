import { Request, Response } from 'express';
import { query } from '../utils/database';
import { AuthRequest } from '../middleware/auth';
import { HumorStyle, ContentType } from '../types';
import multer from 'multer';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, process.env.UPLOAD_PATH || './uploads');
  },
  filename: (req, file, cb) => {
    const uniqueName = `${uuidv4()}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  }
});

const fileFilter = (req: any, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
  const allowedTypes = /jpeg|jpg|png|gif|mp4|mov|avi|webm/;
  const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
  const mimetype = allowedTypes.test(file.mimetype);

  if (mimetype && extname) {
    return cb(null, true);
  } else {
    cb(new Error('Only image and video files are allowed'));
  }
};

export const upload = multer({
  storage,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE || '10485760') // 10MB default
  },
  fileFilter
});

export const createPost = async (req: AuthRequest, res: Response) => {
  try {
    const { content, humorTags, isAIGenerated } = req.body;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!content && !req.file) {
      return res.status(400).json({ error: 'Post must have content or media' });
    }

    let mediaUrl = null;
    let mediaType = null;

    if (req.file) {
      mediaUrl = `/uploads/${req.file.filename}`;
      mediaType = req.file.mimetype.startsWith('video/') ? ContentType.VIDEO : ContentType.IMAGE;
    }

    const parsedHumorTags = humorTags ? JSON.parse(humorTags) : [];

    const result = await query(
      `INSERT INTO posts (user_id, content, media_url, media_type, humor_tags, is_ai_generated)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, user_id, content, media_url, media_type, humor_tags,
                 likes, laugh_reacts, comments, shares, is_ai_generated, created_at`,
      [userId, content || '', mediaUrl, mediaType, JSON.stringify(parsedHumorTags), isAIGenerated || false]
    );

    // Update user's post count
    await query(
      'UPDATE users SET posts_count = posts_count + 1 WHERE id = $1',
      [userId]
    );

    const post = result.rows[0];
    res.status(201).json({
      id: post.id,
      userId: post.user_id,
      content: post.content,
      mediaUrl: post.media_url,
      mediaType: post.media_type,
      humorTags: post.humor_tags,
      likes: post.likes,
      laughReacts: post.laugh_reacts,
      comments: post.comments,
      shares: post.shares,
      isAIGenerated: post.is_ai_generated,
      createdAt: post.created_at
    });
  } catch (error) {
    console.error('Create post error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getPosts = async (req: AuthRequest, res: Response) => {
  try {
    const { page = 1, limit = 10, userId } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    let whereClause = '';
    let queryParams: any[] = [Number(limit), offset];

    if (userId) {
      whereClause = 'WHERE p.user_id = $3';
      queryParams.push(userId);
    }

    const result = await query(
      `SELECT p.id, p.user_id, p.content, p.media_url, p.media_type, p.humor_tags,
              p.likes, p.laugh_reacts, p.comments, p.shares, p.is_ai_generated, p.created_at,
              u.username, u.display_name, u.profile_picture, u.verified
       FROM posts p
       JOIN users u ON p.user_id = u.id
       ${whereClause}
       ORDER BY p.created_at DESC
       LIMIT $1 OFFSET $2`,
      queryParams
    );

    const posts = result.rows.map(post => ({
      id: post.id,
      userId: post.user_id,
      content: post.content,
      mediaUrl: post.media_url,
      mediaType: post.media_type,
      humorTags: post.humor_tags,
      likes: post.likes,
      laughReacts: post.laugh_reacts,
      comments: post.comments,
      shares: post.shares,
      isAIGenerated: post.is_ai_generated,
      createdAt: post.created_at,
      user: {
        username: post.username,
        displayName: post.display_name,
        profilePicture: post.profile_picture,
        verified: post.verified
      }
    }));

    res.json(posts);
  } catch (error) {
    console.error('Get posts error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getPost = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;

    const result = await query(
      `SELECT p.id, p.user_id, p.content, p.media_url, p.media_type, p.humor_tags,
              p.likes, p.laugh_reacts, p.comments, p.shares, p.is_ai_generated, p.created_at,
              u.username, u.display_name, u.profile_picture, u.verified
       FROM posts p
       JOIN users u ON p.user_id = u.id
       WHERE p.id = $1`,
      [postId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    const post = result.rows[0];
    res.json({
      id: post.id,
      userId: post.user_id,
      content: post.content,
      mediaUrl: post.media_url,
      mediaType: post.media_type,
      humorTags: post.humor_tags,
      likes: post.likes,
      laughReacts: post.laugh_reacts,
      comments: post.comments,
      shares: post.shares,
      isAIGenerated: post.is_ai_generated,
      createdAt: post.created_at,
      user: {
        username: post.username,
        displayName: post.display_name,
        profilePicture: post.profile_picture,
        verified: post.verified
      }
    });
  } catch (error) {
    console.error('Get post error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const deletePost = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const result = await query(
      'DELETE FROM posts WHERE id = $1 AND user_id = $2 RETURNING id',
      [postId, userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found or unauthorized' });
    }

    // Update user's post count
    await query(
      'UPDATE users SET posts_count = posts_count - 1 WHERE id = $1',
      [userId]
    );

    res.json({ message: 'Post deleted successfully' });
  } catch (error) {
    console.error('Delete post error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};