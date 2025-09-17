import { Router } from 'express';
import { createPost, getPosts, getPost, deletePost, upload } from '../controllers/postController';
import { authenticateToken, optionalAuth } from '../middleware/auth';

const router = Router();

router.post('/', authenticateToken, upload.single('media'), createPost);
router.get('/', optionalAuth, getPosts);
router.get('/:postId', optionalAuth, getPost);
router.delete('/:postId', authenticateToken, deletePost);

export default router;