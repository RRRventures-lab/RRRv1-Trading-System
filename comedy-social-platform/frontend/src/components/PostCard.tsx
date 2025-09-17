'use client';

import { useState } from 'react';
import { Post, HumorStyle } from '@/types';
import { Heart, MessageCircle, Share, Laugh, MoreHorizontal } from 'lucide-react';
import { motion } from 'framer-motion';

interface PostCardProps {
  post: Post;
  onLike?: (postId: string) => void;
  onComment?: (postId: string) => void;
  onShare?: (postId: string) => void;
  onLaugh?: (postId: string) => void;
}

const humorStyleColors: Record<HumorStyle, string> = {
  [HumorStyle.DARK]: 'bg-gray-800 text-white',
  [HumorStyle.WHOLESOME]: 'bg-green-100 text-green-800',
  [HumorStyle.SATIRICAL]: 'bg-red-100 text-red-800',
  [HumorStyle.OBSERVATIONAL]: 'bg-blue-100 text-blue-800',
  [HumorStyle.SURREAL]: 'bg-purple-100 text-purple-800',
  [HumorStyle.WORDPLAY]: 'bg-yellow-100 text-yellow-800',
  [HumorStyle.PHYSICAL]: 'bg-orange-100 text-orange-800',
  [HumorStyle.SELF_DEPRECATING]: 'bg-pink-100 text-pink-800',
};

export default function PostCard({ post, onLike, onComment, onShare, onLaugh }: PostCardProps) {
  const [isLiked, setIsLiked] = useState(false);
  const [isLaughed, setIsLaughed] = useState(false);

  const handleLike = () => {
    setIsLiked(!isLiked);
    onLike?.(post.id);
  };

  const handleLaugh = () => {
    setIsLaughed(!isLaughed);
    onLaugh?.(post.id);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 pb-2">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">
              {post.user.displayName.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <div className="flex items-center space-x-1">
              <h3 className="font-semibold text-gray-900">{post.user.displayName}</h3>
              {post.user.verified && (
                <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
              )}
              {post.isAIGenerated && (
                <span className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-1 rounded-full">
                  AI
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">@{post.user.username}</p>
          </div>
        </div>
        <button className="p-2 hover:bg-gray-100 rounded-full">
          <MoreHorizontal className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Content */}
      <div className="px-4 pb-2">
        {post.content && (
          <p className="text-gray-900 mb-3 whitespace-pre-wrap">{post.content}</p>
        )}

        {/* Humor Tags */}
        {post.humorTags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {post.humorTags.map((tag) => (
              <span
                key={tag}
                className={`px-2 py-1 rounded-full text-xs font-medium ${humorStyleColors[tag]}`}
              >
                {tag.replace('_', ' ')}
              </span>
            ))}
          </div>
        )}

        {/* Media */}
        {post.mediaUrl && (
          <div className="mb-3 rounded-lg overflow-hidden">
            {post.mediaType === 'video' ? (
              <video
                controls
                className="w-full max-h-96 object-cover"
                src={`http://localhost:5000${post.mediaUrl}`}
              />
            ) : (
              <img
                src={`http://localhost:5000${post.mediaUrl}`}
                alt="Post media"
                className="w-full max-h-96 object-cover"
              />
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-4 py-3 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleLike}
              className={`flex items-center space-x-2 ${
                isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
              }`}
            >
              <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
              <span className="text-sm">{post.likes + (isLiked ? 1 : 0)}</span>
            </motion.button>

            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleLaugh}
              className={`flex items-center space-x-2 ${
                isLaughed ? 'text-yellow-500' : 'text-gray-500 hover:text-yellow-500'
              }`}
            >
              <Laugh className={`w-5 h-5 ${isLaughed ? 'fill-current' : ''}`} />
              <span className="text-sm">{post.laughReacts + (isLaughed ? 1 : 0)}</span>
            </motion.button>

            <button
              onClick={() => onComment?.(post.id)}
              className="flex items-center space-x-2 text-gray-500 hover:text-blue-500"
            >
              <MessageCircle className="w-5 h-5" />
              <span className="text-sm">{post.comments}</span>
            </button>

            <button
              onClick={() => onShare?.(post.id)}
              className="flex items-center space-x-2 text-gray-500 hover:text-green-500"
            >
              <Share className="w-5 h-5" />
              <span className="text-sm">{post.shares}</span>
            </button>
          </div>

          <span className="text-xs text-gray-400">
            {new Date(post.createdAt).toLocaleDateString()}
          </span>
        </div>
      </div>
    </motion.div>
  );
}