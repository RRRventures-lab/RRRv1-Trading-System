import { Router } from 'express';
import { generateJoke, analyzeContent, getPersonalizedContent, moderateContent } from '../controllers/aiController';
import { authenticateToken } from '../middleware/auth';

const router = Router();

router.post('/generate-joke', authenticateToken, generateJoke);
router.post('/analyze-content', authenticateToken, analyzeContent);
router.get('/personalized-content', authenticateToken, getPersonalizedContent);
router.post('/moderate-content', moderateContent);

export default router;