import { Request, Response } from 'express';
import { query } from '../utils/database';
import { AuthRequest } from '../middleware/auth';

export const getDashboardStats = async (req: AuthRequest, res: Response) => {
  try {
    // This should be protected for admin users only
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Get basic platform statistics
    const [
      userCountResult,
      postCountResult,
      reportCountResult,
      activeUsersResult
    ] = await Promise.all([
      query('SELECT COUNT(*) as count FROM users'),
      query('SELECT COUNT(*) as count FROM posts'),
      query('SELECT COUNT(*) as count FROM reports WHERE status = $1', ['pending']),
      query(`SELECT COUNT(DISTINCT user_id) as count FROM posts
             WHERE created_at >= NOW() - INTERVAL '30 days'`)
    ]);

    // Get user growth data (last 30 days)
    const userGrowthResult = await query(`
      SELECT DATE(created_at) as date, COUNT(*) as new_users
      FROM users
      WHERE created_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(created_at)
      ORDER BY date DESC
    `);

    // Get post activity data (last 7 days)
    const postActivityResult = await query(`
      SELECT DATE(created_at) as date, COUNT(*) as posts_count
      FROM posts
      WHERE created_at >= NOW() - INTERVAL '7 days'
      GROUP BY DATE(created_at)
      ORDER BY date DESC
    `);

    // Get top humor styles
    const humorStylesResult = await query(`
      SELECT
        json_array_elements_text(humor_tags) as humor_style,
        COUNT(*) as usage_count
      FROM posts
      WHERE humor_tags != '[]'
      GROUP BY humor_style
      ORDER BY usage_count DESC
      LIMIT 10
    `);

    res.json({
      totalUsers: parseInt(userCountResult.rows[0].count),
      totalPosts: parseInt(postCountResult.rows[0].count),
      pendingReports: parseInt(reportCountResult.rows[0].count),
      activeUsers: parseInt(activeUsersResult.rows[0].count),
      userGrowth: userGrowthResult.rows,
      postActivity: postActivityResult.rows,
      topHumorStyles: humorStylesResult.rows
    });
  } catch (error) {
    console.error('Get dashboard stats error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getUsers = async (req: AuthRequest, res: Response) => {
  try {
    const { page = 1, limit = 20, search = '' } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    let searchClause = '';
    let queryParams: any[] = [Number(limit), offset];

    if (search) {
      searchClause = 'WHERE LOWER(username) LIKE $3 OR LOWER(display_name) LIKE $3';
      queryParams.push(`%${search.toString().toLowerCase()}%`);
    }

    const result = await query(
      `SELECT id, username, display_name, email, verified, followers, following,
              posts_count, created_at
       FROM users
       ${searchClause}
       ORDER BY created_at DESC
       LIMIT $1 OFFSET $2`,
      queryParams
    );

    const users = result.rows.map(user => ({
      id: user.id,
      username: user.username,
      displayName: user.display_name,
      email: user.email,
      verified: user.verified,
      followers: user.followers,
      following: user.following,
      postsCount: user.posts_count,
      createdAt: user.created_at
    }));

    res.json(users);
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateUserStatus = async (req: AuthRequest, res: Response) => {
  try {
    const { userId } = req.params;
    const { verified, suspended } = req.body;
    const adminId = req.user?.userId;

    if (!adminId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Create user_status table if it doesn't exist
    await query(`
      CREATE TABLE IF NOT EXISTS user_status (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
        suspended BOOLEAN DEFAULT FALSE,
        suspended_reason TEXT,
        suspended_by UUID REFERENCES users(id),
        suspended_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    let updateFields = [];
    let queryParams = [];
    let paramIndex = 1;

    if (typeof verified === 'boolean') {
      updateFields.push(`verified = $${paramIndex}`);
      queryParams.push(verified);
      paramIndex++;
    }

    if (updateFields.length > 0) {
      updateFields.push(`updated_at = CURRENT_TIMESTAMP`);
      queryParams.push(userId);

      await query(
        `UPDATE users SET ${updateFields.join(', ')} WHERE id = $${paramIndex}`,
        queryParams
      );
    }

    // Handle suspension status
    if (typeof suspended === 'boolean') {
      const existingStatus = await query(
        'SELECT id FROM user_status WHERE user_id = $1',
        [userId]
      );

      if (existingStatus.rows.length > 0) {
        await query(
          `UPDATE user_status
           SET suspended = $1, suspended_by = $2, suspended_at = $3, updated_at = CURRENT_TIMESTAMP
           WHERE user_id = $4`,
          [suspended, adminId, suspended ? new Date() : null, userId]
        );
      } else {
        await query(
          'INSERT INTO user_status (user_id, suspended, suspended_by, suspended_at) VALUES ($1, $2, $3, $4)',
          [userId, suspended, adminId, suspended ? new Date() : null]
        );
      }
    }

    res.json({ message: 'User status updated successfully' });
  } catch (error) {
    console.error('Update user status error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const deletePost = async (req: AuthRequest, res: Response) => {
  try {
    const { postId } = req.params;
    const { reason } = req.body;
    const adminId = req.user?.userId;

    if (!adminId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Create admin_actions table if it doesn't exist
    await query(`
      CREATE TABLE IF NOT EXISTS admin_actions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        admin_id UUID REFERENCES users(id) ON DELETE SET NULL,
        action_type VARCHAR(50) NOT NULL,
        target_type VARCHAR(50) NOT NULL,
        target_id UUID NOT NULL,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    const result = await query(
      'DELETE FROM posts WHERE id = $1 RETURNING id, user_id',
      [postId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    const deletedPost = result.rows[0];

    // Update user's post count
    await query(
      'UPDATE users SET posts_count = posts_count - 1 WHERE id = $1',
      [deletedPost.user_id]
    );

    // Log admin action
    await query(
      'INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, reason) VALUES ($1, $2, $3, $4, $5)',
      [adminId, 'delete', 'post', postId, reason || 'Admin deletion']
    );

    res.json({ message: 'Post deleted successfully' });
  } catch (error) {
    console.error('Delete post error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getAdminActions = async (req: AuthRequest, res: Response) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const offset = (Number(page) - 1) * Number(limit);

    const result = await query(
      `SELECT aa.id, aa.action_type, aa.target_type, aa.target_id, aa.reason, aa.created_at,
              u.username as admin_username, u.display_name as admin_display_name
       FROM admin_actions aa
       LEFT JOIN users u ON aa.admin_id = u.id
       ORDER BY aa.created_at DESC
       LIMIT $1 OFFSET $2`,
      [Number(limit), offset]
    );

    const actions = result.rows.map(action => ({
      id: action.id,
      actionType: action.action_type,
      targetType: action.target_type,
      targetId: action.target_id,
      reason: action.reason,
      createdAt: action.created_at,
      admin: {
        username: action.admin_username,
        displayName: action.admin_display_name
      }
    }));

    res.json(actions);
  } catch (error) {
    console.error('Get admin actions error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};