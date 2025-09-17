import { Router } from 'express';
import { likePost, laughReact, addComment, getComments } from '../controllers/interactionController';
import { authenticateToken, optionalAuth } from '../middleware/auth';

const router = Router();

router.post('/posts/:postId/like', authenticateToken, likePost);
router.post('/posts/:postId/laugh', authenticateToken, laughReact);
router.post('/posts/:postId/comments', authenticateToken, addComment);
router.get('/posts/:postId/comments', optionalAuth, getComments);

export default router;