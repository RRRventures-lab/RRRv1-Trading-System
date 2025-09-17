import { Request, Response } from 'express';
import { query } from '../utils/database';
import { AuthRequest } from '../middleware/auth';
import { notificationService } from '../services/notificationService';

export const followUser = async (req: AuthRequest, res: Response) => {
  try {
    const { userId } = req.params;
    const followerId = req.user?.userId;

    if (!followerId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (followerId === userId) {
      return res.status(400).json({ error: 'Cannot follow yourself' });
    }

    // Check if target user exists
    const userCheck = await query('SELECT id FROM users WHERE id = $1', [userId]);
    if (userCheck.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Check if already following
    const existingFollow = await query(
      'SELECT id FROM follows WHERE follower_id = $1 AND following_id = $2',
      [followerId, userId]
    );

    if (existingFollow.rows.length > 0) {
      // Unfollow
      await query(
        'DELETE FROM follows WHERE follower_id = $1 AND following_id = $2',
        [followerId, userId]
      );

      // Update counts
      await query('UPDATE users SET followers = followers - 1 WHERE id = $1', [userId]);
      await query('UPDATE users SET following = following - 1 WHERE id = $1', [followerId]);

      res.json({ following: false, message: 'User unfollowed' });
    } else {
      // Follow
      await query(
        'INSERT INTO follows (follower_id, following_id) VALUES ($1, $2)',
        [followerId, userId]
      );

      // Update counts
      await query('UPDATE users SET followers = followers + 1 WHERE id = $1', [userId]);
      await query('UPDATE users SET following = following + 1 WHERE id = $1', [followerId]);

      // Send notification
      await notificationService.notifyFollow(userId, followerId);

      res.json({ following: true, message: 'User followed' });
    }
  } catch (error) {
    console.error('Follow user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getFollowers = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    const result = await query(
      `SELECT u.id, u.username, u.display_name, u.profile_picture, u.verified, u.bio
       FROM follows f
       JOIN users u ON f.follower_id = u.id
       WHERE f.following_id = $1
       ORDER BY f.created_at DESC
       LIMIT $2 OFFSET $3`,
      [userId, Number(limit), offset]
    );

    const followers = result.rows.map(user => ({
      id: user.id,
      username: user.username,
      displayName: user.display_name,
      profilePicture: user.profile_picture,
      verified: user.verified,
      bio: user.bio
    }));

    res.json(followers);
  } catch (error) {
    console.error('Get followers error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getFollowing = async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const { page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    const result = await query(
      `SELECT u.id, u.username, u.display_name, u.profile_picture, u.verified, u.bio
       FROM follows f
       JOIN users u ON f.following_id = u.id
       WHERE f.follower_id = $1
       ORDER BY f.created_at DESC
       LIMIT $2 OFFSET $3`,
      [userId, Number(limit), offset]
    );

    const following = result.rows.map(user => ({
      id: user.id,
      username: user.username,
      displayName: user.display_name,
      profilePicture: user.profile_picture,
      verified: user.verified,
      bio: user.bio
    }));

    res.json(following);
  } catch (error) {
    console.error('Get following error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const checkFollowStatus = async (req: AuthRequest, res: Response) => {
  try {
    const { userId } = req.params;
    const followerId = req.user?.userId;

    if (!followerId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const result = await query(
      'SELECT id FROM follows WHERE follower_id = $1 AND following_id = $2',
      [followerId, userId]
    );

    res.json({ following: result.rows.length > 0 });
  } catch (error) {
    console.error('Check follow status error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const searchUsers = async (req: Request, res: Response) => {
  try {
    const { q, page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    if (!q || typeof q !== 'string') {
      return res.status(400).json({ error: 'Search query is required' });
    }

    const searchTerm = `%${q.toLowerCase()}%`;

    const result = await query(
      `SELECT id, username, display_name, profile_picture, verified, bio, followers
       FROM users
       WHERE LOWER(username) LIKE $1 OR LOWER(display_name) LIKE $1
       ORDER BY followers DESC, display_name ASC
       LIMIT $2 OFFSET $3`,
      [searchTerm, Number(limit), offset]
    );

    const users = result.rows.map(user => ({
      id: user.id,
      username: user.username,
      displayName: user.display_name,
      profilePicture: user.profile_picture,
      verified: user.verified,
      bio: user.bio,
      followers: user.followers
    }));

    res.json(users);
  } catch (error) {
    console.error('Search users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getSuggestedUsers = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user?.userId;
    const { limit = 10 } = req.query;

    let whereClause = '';
    let queryParams: any[] = [Number(limit)];

    if (userId) {
      // Exclude users already being followed and the current user
      whereClause = `WHERE u.id != $2
                     AND u.id NOT IN (
                       SELECT following_id FROM follows WHERE follower_id = $2
                     )`;
      queryParams.push(userId);
    }

    const result = await query(
      `SELECT u.id, u.username, u.display_name, u.profile_picture, u.verified, u.bio, u.followers
       FROM users u
       ${whereClause}
       ORDER BY u.followers DESC, RANDOM()
       LIMIT $1`,
      queryParams
    );

    const suggestedUsers = result.rows.map(user => ({
      id: user.id,
      username: user.username,
      displayName: user.display_name,
      profilePicture: user.profile_picture,
      verified: user.verified,
      bio: user.bio,
      followers: user.followers
    }));

    res.json(suggestedUsers);
  } catch (error) {
    console.error('Get suggested users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};