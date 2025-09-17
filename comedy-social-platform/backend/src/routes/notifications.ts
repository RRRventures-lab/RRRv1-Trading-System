import { Router } from 'express';
import {
  getNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  getUnreadCount
} from '../controllers/notificationController';
import { authenticateToken } from '../middleware/auth';

const router = Router();

router.get('/notifications', authenticateToken, getNotifications);
router.put('/notifications/:notificationId/read', authenticateToken, markNotificationAsRead);
router.put('/notifications/read-all', authenticateToken, markAllNotificationsAsRead);
router.get('/notifications/unread-count', authenticateToken, getUnreadCount);

export default router;