import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { initializeDatabase } from './utils/database';
import authRoutes from './routes/auth';
import postRoutes from './routes/posts';
import interactionRoutes from './routes/interactions';
import aiRoutes from './routes/ai';
import socialRoutes from './routes/social';
import notificationRoutes from './routes/notifications';
import moderationRoutes from './routes/moderation';
import adminRoutes from './routes/admin';
import { notificationService } from './services/notificationService';

dotenv.config();

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

const PORT = process.env.PORT || 5000;

app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/posts', postRoutes);
app.use('/api', interactionRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api', socialRoutes);
app.use('/api', notificationRoutes);
app.use('/api', moderationRoutes);
app.use('/api/admin', adminRoutes);

// Serve uploaded files
app.use('/uploads', express.static('uploads'));

app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'Comedy Social Platform API is running!' });
});

io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

const startServer = async () => {
  try {
    await initializeDatabase();

    // Initialize notification service with Socket.IO
    notificationService.setSocketIO(io);

    server.listen(PORT, () => {
      console.log(`🚀 Server running on port ${PORT}`);
      console.log(`🎭 Comedy Social Platform Backend is ready!`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();