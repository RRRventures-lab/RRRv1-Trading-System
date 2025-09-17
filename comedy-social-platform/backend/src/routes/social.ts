import { Router } from 'express';
import {
  followUser,
  getFollowers,
  getFollowing,
  checkFollowStatus,
  searchUsers,
  getSuggestedUsers
} from '../controllers/socialController';
import { authenticateToken, optionalAuth } from '../middleware/auth';

const router = Router();

router.post('/users/:userId/follow', authenticateToken, followUser);
router.get('/users/:userId/followers', optionalAuth, getFollowers);
router.get('/users/:userId/following', optionalAuth, getFollowing);
router.get('/users/:userId/follow-status', authenticateToken, checkFollowStatus);
router.get('/users/search', optionalAuth, searchUsers);
router.get('/users/suggested', optionalAuth, getSuggestedUsers);

export default router;