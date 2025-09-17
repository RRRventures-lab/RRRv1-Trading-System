import { Request, Response } from 'express';
import { AuthRequest } from '../middleware/auth';
import { aiService } from '../services/aiService';
import { HumorStyle } from '../types';
import { query } from '../utils/database';

export const generateJoke = async (req: AuthRequest, res: Response) => {
  try {
    const { humorStyle, topic } = req.body;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!humorStyle || !Object.values(HumorStyle).includes(humorStyle)) {
      return res.status(400).json({ error: 'Valid humor style is required' });
    }

    const joke = await aiService.generateJoke(humorStyle, topic);

    res.json({
      content: joke,
      humorStyle,
      topic,
      isAIGenerated: true
    });
  } catch (error) {
    console.error('Generate joke error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const analyzeContent = async (req: AuthRequest, res: Response) => {
  try {
    const { content } = req.body;
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!content || !content.trim()) {
      return res.status(400).json({ error: 'Content is required' });
    }

    const analysis = await aiService.analyzeHumor(content.trim());

    res.json(analysis);
  } catch (error) {
    console.error('Analyze content error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getPersonalizedContent = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Get user preferences
    const userResult = await query(
      'SELECT comedy_preferences FROM users WHERE id = $1',
      [userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const preferences = userResult.rows[0].comedy_preferences;
    const content = await aiService.generatePersonalizedContent(preferences);

    res.json({
      content,
      isPersonalized: true,
      basedOnPreferences: preferences
    });
  } catch (error) {
    console.error('Get personalized content error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const moderateContent = async (req: AuthRequest, res: Response) => {
  try {
    const { content } = req.body;

    if (!content || !content.trim()) {
      return res.status(400).json({ error: 'Content is required' });
    }

    const moderation = await aiService.moderateContent(content.trim());

    res.json(moderation);
  } catch (error) {
    console.error('Moderate content error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};