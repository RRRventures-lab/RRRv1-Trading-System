import { Request, Response } from 'express';
import { query } from '../utils/database';
import { AuthRequest } from '../middleware/auth';
import { aiService } from '../services/aiService';

export enum ReportReason {
  SPAM = 'spam',
  HARASSMENT = 'harassment',
  HATE_SPEECH = 'hate_speech',
  INAPPROPRIATE_CONTENT = 'inappropriate_content',
  FAKE_ACCOUNT = 'fake_account',
  COPYRIGHT = 'copyright',
  OTHER = 'other'
}

export const reportPost = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;
    const { reason, description } = req.body;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!reason || !Object.values(ReportReason).includes(reason)) {
      return res.status(400).json({ error: 'Valid report reason is required' });
    }

    // Check if post exists
    const postCheck = await query('SELECT id FROM posts WHERE id = $1', [postId]);
    if (postCheck.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    // Create reports table if it doesn't exist
    await query(`
      CREATE TABLE IF NOT EXISTS reports (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        reporter_id UUID REFERENCES users(id) ON DELETE CASCADE,
        reported_post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
        reported_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        reason VARCHAR(50) NOT NULL,
        description TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        reviewed_by UUID REFERENCES users(id),
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Check if user already reported this post
    const existingReport = await query(
      'SELECT id FROM reports WHERE reporter_id = $1 AND reported_post_id = $2',
      [userId, postId]
    );

    if (existingReport.rows.length > 0) {
      return res.status(409).json({ error: 'You have already reported this post' });
    }

    // Get post owner
    const postOwnerResult = await query('SELECT user_id FROM posts WHERE id = $1', [postId]);
    const reportedUserId = postOwnerResult.rows[0].user_id;

    const result = await query(
      `INSERT INTO reports (reporter_id, reported_post_id, reported_user_id, reason, description)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, reason, description, status, created_at`,
      [userId, postId, reportedUserId, reason, description || null]
    );

    const report = result.rows[0];
    res.status(201).json({
      id: report.id,
      reason: report.reason,
      description: report.description,
      status: report.status,
      createdAt: report.created_at,
      message: 'Report submitted successfully'
    });
  } catch (error) {
    console.error('Report post error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const reportUser = async (req: AuthRequest, res: Response) => {
  try {
    const { userId: reportedUserId } = req.params;
    const { reason, description } = req.body;
    const reporterId = req.user?.userId;

    if (!reporterId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (reporterId === reportedUserId) {
      return res.status(400).json({ error: 'Cannot report yourself' });
    }

    if (!reason || !Object.values(ReportReason).includes(reason)) {
      return res.status(400).json({ error: 'Valid report reason is required' });
    }

    // Check if user exists
    const userCheck = await query('SELECT id FROM users WHERE id = $1', [reportedUserId]);
    if (userCheck.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Check if user already reported this user
    const existingReport = await query(
      'SELECT id FROM reports WHERE reporter_id = $1 AND reported_user_id = $2 AND reported_post_id IS NULL',
      [reporterId, reportedUserId]
    );

    if (existingReport.rows.length > 0) {
      return res.status(409).json({ error: 'You have already reported this user' });
    }

    const result = await query(
      `INSERT INTO reports (reporter_id, reported_user_id, reason, description)
       VALUES ($1, $2, $3, $4)
       RETURNING id, reason, description, status, created_at`,
      [reporterId, reportedUserId, reason, description || null]
    );

    const report = result.rows[0];
    res.status(201).json({
      id: report.id,
      reason: report.reason,
      description: report.description,
      status: report.status,
      createdAt: report.created_at,
      message: 'Report submitted successfully'
    });
  } catch (error) {
    console.error('Report user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getReports = async (req: AuthRequest, res: Response) => {
  try {
    const { status = 'pending', page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    // This endpoint should be protected for admins only
    // For now, we'll implement basic functionality

    const result = await query(
      `SELECT r.id, r.reason, r.description, r.status, r.created_at,
              r.reported_post_id, r.reported_user_id,
              reporter.username as reporter_username,
              reported_user.username as reported_username,
              p.content as post_content
       FROM reports r
       JOIN users reporter ON r.reporter_id = reporter.id
       LEFT JOIN users reported_user ON r.reported_user_id = reported_user.id
       LEFT JOIN posts p ON r.reported_post_id = p.id
       WHERE r.status = $1
       ORDER BY r.created_at DESC
       LIMIT $2 OFFSET $3`,
      [status, Number(limit), offset]
    );

    const reports = result.rows.map(report => ({
      id: report.id,
      reason: report.reason,
      description: report.description,
      status: report.status,
      createdAt: report.created_at,
      reportedPostId: report.reported_post_id,
      reportedUserId: report.reported_user_id,
      reporter: {
        username: report.reporter_username
      },
      reportedUser: report.reported_username ? {
        username: report.reported_username
      } : null,
      postContent: report.post_content
    }));

    res.json(reports);
  } catch (error) {
    console.error('Get reports error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const reviewReport = async (req: AuthRequest, res: Response) => {
  try {
    const { reportId } = req.params;
    const { action, notes } = req.body; // action: 'approve', 'reject', 'escalate'
    const reviewerId = req.user?.userId;

    if (!reviewerId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!action || !['approve', 'reject', 'escalate'].includes(action)) {
      return res.status(400).json({ error: 'Valid action is required' });
    }

    const result = await query(
      `UPDATE reports
       SET status = $1, reviewed_by = $2, reviewed_at = CURRENT_TIMESTAMP
       WHERE id = $3
       RETURNING id, status`,
      [action === 'approve' ? 'resolved' : action === 'reject' ? 'dismissed' : 'escalated', reviewerId, reportId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Report not found' });
    }

    res.json({
      id: result.rows[0].id,
      status: result.rows[0].status,
      message: `Report ${action}d successfully`
    });
  } catch (error) {
    console.error('Review report error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const moderateContent = async (req: Request, res: Response) => {
  try {
    const { content } = req.body;

    if (!content || !content.trim()) {
      return res.status(400).json({ error: 'Content is required' });
    }

    const moderation = await aiService.moderateContent(content.trim());

    res.json(moderation);
  } catch (error) {
    console.error('Moderate content error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const blockUser = async (req: AuthRequest, res: Response) => {
  try {
    const { userId: blockedUserId } = req.params;
    const blockerId = req.user?.userId;

    if (!blockerId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (blockerId === blockedUserId) {
      return res.status(400).json({ error: 'Cannot block yourself' });
    }

    // Create blocks table if it doesn't exist
    await query(`
      CREATE TABLE IF NOT EXISTS user_blocks (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        blocker_id UUID REFERENCES users(id) ON DELETE CASCADE,
        blocked_id UUID REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(blocker_id, blocked_id)
      )
    `);

    // Check if user exists
    const userCheck = await query('SELECT id FROM users WHERE id = $1', [blockedUserId]);
    if (userCheck.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Check if already blocked
    const existingBlock = await query(
      'SELECT id FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2',
      [blockerId, blockedUserId]
    );

    if (existingBlock.rows.length > 0) {
      return res.status(409).json({ error: 'User already blocked' });
    }

    await query(
      'INSERT INTO user_blocks (blocker_id, blocked_id) VALUES ($1, $2)',
      [blockerId, blockedUserId]
    );

    // Remove any existing follow relationships
    await query(
      'DELETE FROM follows WHERE (follower_id = $1 AND following_id = $2) OR (follower_id = $2 AND following_id = $1)',
      [blockerId, blockedUserId]
    );

    res.json({ message: 'User blocked successfully' });
  } catch (error) {
    console.error('Block user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};