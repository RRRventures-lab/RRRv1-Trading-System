import { Request, Response } from 'express';
import { AuthRequest } from '../middleware/auth';
import { notificationService } from '../services/notificationService';

export const getNotifications = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user?.userId;
    const { page = 1, limit = 20 } = req.query;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const notifications = await notificationService.getNotifications(
      userId,
      Number(page),
      Number(limit)
    );

    res.json(notifications);
  } catch (error) {
    console.error('Get notifications error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const markNotificationAsRead = async (req: AuthRequest, res: Response) => {
  try {
    const { notificationId } = req.params;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const success = await notificationService.markAsRead(notificationId, userId);

    if (success) {
      res.json({ message: 'Notification marked as read' });
    } else {
      res.status(404).json({ error: 'Notification not found' });
    }
  } catch (error) {
    console.error('Mark notification as read error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const markAllNotificationsAsRead = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const success = await notificationService.markAllAsRead(userId);

    if (success) {
      res.json({ message: 'All notifications marked as read' });
    } else {
      res.status(500).json({ error: 'Failed to mark notifications as read' });
    }
  } catch (error) {
    console.error('Mark all notifications as read error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getUnreadCount = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const count = await notificationService.getUnreadCount(userId);
    res.json({ count });
  } catch (error) {
    console.error('Get unread count error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};