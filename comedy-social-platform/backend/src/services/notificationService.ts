import { Server } from 'socket.io';
import { query } from '../utils/database';

export enum NotificationType {
  LIKE = 'like',
  LAUGH = 'laugh',
  COMMENT = 'comment',
  FOLLOW = 'follow',
  POST_MENTION = 'post_mention'
}

export interface Notification {
  id: string;
  userId: string;
  type: NotificationType;
  fromUserId: string;
  postId?: string;
  message: string;
  read: boolean;
  createdAt: Date;
}

class NotificationService {
  private io: Server | null = null;
  private connectedUsers = new Map<string, string>(); // userId -> socketId

  setSocketIO(io: Server) {
    this.io = io;

    io.on('connection', (socket) => {
      console.log('User connected:', socket.id);

      socket.on('authenticate', (userId: string) => {
        this.connectedUsers.set(userId, socket.id);
        console.log(`User ${userId} authenticated with socket ${socket.id}`);
      });

      socket.on('disconnect', () => {
        // Remove user from connected users
        for (const [userId, socketId] of this.connectedUsers.entries()) {
          if (socketId === socket.id) {
            this.connectedUsers.delete(userId);
            console.log(`User ${userId} disconnected`);
            break;
          }
        }
      });
    });
  }

  async createNotification(data: {
    userId: string;
    type: NotificationType;
    fromUserId: string;
    postId?: string;
    message: string;
  }) {
    try {
      // Don't create notification for self-actions
      if (data.userId === data.fromUserId) {
        return null;
      }

      // Create notification table if it doesn't exist
      await query(`
        CREATE TABLE IF NOT EXISTS notifications (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id UUID REFERENCES users(id) ON DELETE CASCADE,
          type VARCHAR(50) NOT NULL,
          from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
          post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
          message TEXT NOT NULL,
          read BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);

      const result = await query(
        `INSERT INTO notifications (user_id, type, from_user_id, post_id, message)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING id, user_id, type, from_user_id, post_id, message, read, created_at`,
        [data.userId, data.type, data.fromUserId, data.postId || null, data.message]
      );

      const notification = result.rows[0];

      // Get from user details
      const fromUserResult = await query(
        'SELECT username, display_name, profile_picture FROM users WHERE id = $1',
        [data.fromUserId]
      );

      const notificationWithUser = {
        ...notification,
        fromUser: fromUserResult.rows[0]
      };

      // Send real-time notification if user is connected
      const socketId = this.connectedUsers.get(data.userId);
      if (socketId && this.io) {
        this.io.to(socketId).emit('notification', notificationWithUser);
      }

      return notificationWithUser;
    } catch (error) {
      console.error('Create notification error:', error);
      return null;
    }
  }

  async getNotifications(userId: string, page = 1, limit = 20) {
    try {
      const offset = (page - 1) * limit;

      const result = await query(
        `SELECT n.id, n.type, n.message, n.read, n.created_at, n.post_id,
                u.username, u.display_name, u.profile_picture
         FROM notifications n
         JOIN users u ON n.from_user_id = u.id
         WHERE n.user_id = $1
         ORDER BY n.created_at DESC
         LIMIT $2 OFFSET $3`,
        [userId, limit, offset]
      );

      return result.rows.map(row => ({
        id: row.id,
        type: row.type,
        message: row.message,
        read: row.read,
        createdAt: row.created_at,
        postId: row.post_id,
        fromUser: {
          username: row.username,
          displayName: row.display_name,
          profilePicture: row.profile_picture
        }
      }));
    } catch (error) {
      console.error('Get notifications error:', error);
      return [];
    }
  }

  async markAsRead(notificationId: string, userId: string) {
    try {
      await query(
        'UPDATE notifications SET read = TRUE WHERE id = $1 AND user_id = $2',
        [notificationId, userId]
      );
      return true;
    } catch (error) {
      console.error('Mark notification as read error:', error);
      return false;
    }
  }

  async markAllAsRead(userId: string) {
    try {
      await query(
        'UPDATE notifications SET read = TRUE WHERE user_id = $1',
        [userId]
      );
      return true;
    } catch (error) {
      console.error('Mark all notifications as read error:', error);
      return false;
    }
  }

  async getUnreadCount(userId: string) {
    try {
      const result = await query(
        'SELECT COUNT(*) as count FROM notifications WHERE user_id = $1 AND read = FALSE',
        [userId]
      );
      return parseInt(result.rows[0].count);
    } catch (error) {
      console.error('Get unread count error:', error);
      return 0;
    }
  }

  // Helper methods for specific notification types
  async notifyLike(postUserId: string, fromUserId: string, postId: string) {
    const fromUserResult = await query(
      'SELECT display_name FROM users WHERE id = $1',
      [fromUserId]
    );
    const fromUserName = fromUserResult.rows[0]?.display_name || 'Someone';

    return this.createNotification({
      userId: postUserId,
      type: NotificationType.LIKE,
      fromUserId,
      postId,
      message: `${fromUserName} liked your post`
    });
  }

  async notifyLaugh(postUserId: string, fromUserId: string, postId: string) {
    const fromUserResult = await query(
      'SELECT display_name FROM users WHERE id = $1',
      [fromUserId]
    );
    const fromUserName = fromUserResult.rows[0]?.display_name || 'Someone';

    return this.createNotification({
      userId: postUserId,
      type: NotificationType.LAUGH,
      fromUserId,
      postId,
      message: `${fromUserName} found your post hilarious! 😂`
    });
  }

  async notifyComment(postUserId: string, fromUserId: string, postId: string) {
    const fromUserResult = await query(
      'SELECT display_name FROM users WHERE id = $1',
      [fromUserId]
    );
    const fromUserName = fromUserResult.rows[0]?.display_name || 'Someone';

    return this.createNotification({
      userId: postUserId,
      type: NotificationType.COMMENT,
      fromUserId,
      postId,
      message: `${fromUserName} commented on your post`
    });
  }

  async notifyFollow(userId: string, fromUserId: string) {
    const fromUserResult = await query(
      'SELECT display_name FROM users WHERE id = $1',
      [fromUserId]
    );
    const fromUserName = fromUserResult.rows[0]?.display_name || 'Someone';

    return this.createNotification({
      userId,
      type: NotificationType.FOLLOW,
      fromUserId,
      message: `${fromUserName} started following you`
    });
  }
}

export const notificationService = new NotificationService();