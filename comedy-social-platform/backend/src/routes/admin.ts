import { Router } from 'express';
import {
  getDashboardStats,
  getUsers,
  updateUserStatus,
  deletePost,
  getAdminActions
} from '../controllers/adminController';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// Note: In production, these routes should have additional admin role verification
router.get('/dashboard/stats', authenticateToken, getDashboardStats);
router.get('/users', authenticateToken, getUsers);
router.put('/users/:userId/status', authenticateToken, updateUserStatus);
router.delete('/posts/:postId', authenticateToken, deletePost);
router.get('/actions', authenticateToken, getAdminActions);

export default router;