import { Router } from 'express';
import {
  reportPost,
  reportUser,
  getReports,
  reviewReport,
  moderateContent,
  blockUser
} from '../controllers/moderationController';
import { authenticateToken } from '../middleware/auth';

const router = Router();

router.post('/posts/:postId/report', authenticateToken, reportPost);
router.post('/users/:userId/report', authenticateToken, reportUser);
router.post('/users/:userId/block', authenticateToken, blockUser);
router.get('/reports', authenticateToken, getReports);
router.put('/reports/:reportId/review', authenticateToken, reviewReport);
router.post('/moderate-content', moderateContent);

export default router;