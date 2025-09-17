import { Request, Response } from 'express';
import { query } from '../utils/database';
import { AuthRequest } from '../middleware/auth';
import { notificationService } from '../services/notificationService';

export const likePost = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Check if post exists
    const postCheck = await query('SELECT id FROM posts WHERE id = $1', [postId]);
    if (postCheck.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    // Check if already liked
    const existingLike = await query(
      'SELECT id FROM likes WHERE user_id = $1 AND post_id = $2',
      [userId, postId]
    );

    if (existingLike.rows.length > 0) {
      // Unlike
      await query('DELETE FROM likes WHERE user_id = $1 AND post_id = $2', [userId, postId]);
      await query('UPDATE posts SET likes = likes - 1 WHERE id = $1', [postId]);
      res.json({ liked: false, message: 'Post unliked' });
    } else {
      // Like
      await query(
        'INSERT INTO likes (user_id, post_id) VALUES ($1, $2)',
        [userId, postId]
      );
      await query('UPDATE posts SET likes = likes + 1 WHERE id = $1', [postId]);

      // Get post owner for notification
      const postOwnerResult = await query('SELECT user_id FROM posts WHERE id = $1', [postId]);
      if (postOwnerResult.rows.length > 0) {
        const postOwnerId = postOwnerResult.rows[0].user_id;
        await notificationService.notifyLike(postOwnerId, userId, postId);
      }

      res.json({ liked: true, message: 'Post liked' });
    }
  } catch (error) {
    console.error('Like post error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const laughReact = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Check if post exists
    const postCheck = await query('SELECT id FROM posts WHERE id = $1', [postId]);
    if (postCheck.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    // Create laugh_reactions table if it doesn't exist (for this endpoint)
    await query(`
      CREATE TABLE IF NOT EXISTS laugh_reactions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, post_id)
      )
    `);

    // Check if already reacted
    const existingReaction = await query(
      'SELECT id FROM laugh_reactions WHERE user_id = $1 AND post_id = $2',
      [userId, postId]
    );

    if (existingReaction.rows.length > 0) {
      // Remove reaction
      await query('DELETE FROM laugh_reactions WHERE user_id = $1 AND post_id = $2', [userId, postId]);
      await query('UPDATE posts SET laugh_reacts = laugh_reacts - 1 WHERE id = $1', [postId]);
      res.json({ laughed: false, message: 'Laugh reaction removed' });
    } else {
      // Add reaction
      await query(
        'INSERT INTO laugh_reactions (user_id, post_id) VALUES ($1, $2)',
        [userId, postId]
      );
      await query('UPDATE posts SET laugh_reacts = laugh_reacts + 1 WHERE id = $1', [postId]);

      // Get post owner for notification
      const postOwnerResult = await query('SELECT user_id FROM posts WHERE id = $1', [postId]);
      if (postOwnerResult.rows.length > 0) {
        const postOwnerId = postOwnerResult.rows[0].user_id;
        await notificationService.notifyLaugh(postOwnerId, userId, postId);
      }

      res.json({ laughed: true, message: 'Laugh reaction added' });
    }
  } catch (error) {
    console.error('Laugh react error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const addComment = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;
    const { content } = req.body;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!content || !content.trim()) {
      return res.status(400).json({ error: 'Comment content is required' });
    }

    // Check if post exists
    const postCheck = await query('SELECT id FROM posts WHERE id = $1', [postId]);
    if (postCheck.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    const result = await query(
      `INSERT INTO comments (user_id, post_id, content)
       VALUES ($1, $2, $3)
       RETURNING id, user_id, post_id, content, created_at`,
      [userId, postId, content.trim()]
    );

    // Update post comment count
    await query('UPDATE posts SET comments = comments + 1 WHERE id = $1', [postId]);

    // Get post owner for notification
    const postOwnerResult = await query('SELECT user_id FROM posts WHERE id = $1', [postId]);
    if (postOwnerResult.rows.length > 0) {
      const postOwnerId = postOwnerResult.rows[0].user_id;
      await notificationService.notifyComment(postOwnerId, userId, postId);
    }

    const comment = result.rows[0];
    res.status(201).json({
      id: comment.id,
      userId: comment.user_id,
      postId: comment.post_id,
      content: comment.content,
      createdAt: comment.created_at
    });
  } catch (error) {
    console.error('Add comment error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getComments = async (req: Request, res: Response) => {
  try {
    const { postId } = req.params;
    const { page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    const result = await query(
      `SELECT c.id, c.user_id, c.content, c.created_at,
              u.username, u.display_name, u.profile_picture, u.verified
       FROM comments c
       JOIN users u ON c.user_id = u.id
       WHERE c.post_id = $1
       ORDER BY c.created_at ASC
       LIMIT $2 OFFSET $3`,
      [postId, Number(limit), offset]
    );

    const comments = result.rows.map(comment => ({
      id: comment.id,
      userId: comment.user_id,
      content: comment.content,
      createdAt: comment.created_at,
      user: {
        username: comment.username,
        displayName: comment.display_name,
        profilePicture: comment.profile_picture,
        verified: comment.verified
      }
    }));

    res.json(comments);
  } catch (error) {
    console.error('Get comments error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};