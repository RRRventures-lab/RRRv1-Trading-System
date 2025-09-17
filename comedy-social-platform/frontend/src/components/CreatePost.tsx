'use client';

import { useState, useRef } from 'react';
import { HumorStyle, CreatePostData } from '@/types';
import { Image, Video, Smile, Send, X } from 'lucide-react';
import { motion } from 'framer-motion';

interface CreatePostProps {
  onSubmit: (data: CreatePostData) => void;
  isLoading?: boolean;
}

const humorStyles = Object.values(HumorStyle);

export default function CreatePost({ onSubmit, isLoading }: CreatePostProps) {
  const [content, setContent] = useState('');
  const [selectedTags, setSelectedTags] = useState<HumorStyle[]>([]);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [mediaPreview, setMediaPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTagToggle = (tag: HumorStyle) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleMediaSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setMediaFile(file);
      const reader = new FileReader();
      reader.onload = () => {
        setMediaPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveMedia = () => {
    setMediaFile(null);
    setMediaPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() && !mediaFile) return;

    onSubmit({
      content: content.trim(),
      humorTags: selectedTags,
      media: mediaFile || undefined,
    });

    // Reset form
    setContent('');
    setSelectedTags([]);
    setMediaFile(null);
    setMediaPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md border border-gray-200 p-4 mb-6"
    >
      <form onSubmit={handleSubmit}>
        {/* Text Input */}
        <div className="mb-4">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What's making you laugh today?"
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            rows={3}
          />
        </div>

        {/* Media Preview */}
        {mediaPreview && (
          <div className="mb-4 relative">
            <div className="rounded-lg overflow-hidden">
              {mediaFile?.type.startsWith('video/') ? (
                <video
                  src={mediaPreview}
                  controls
                  className="w-full max-h-64 object-cover"
                />
              ) : (
                <img
                  src={mediaPreview}
                  alt="Preview"
                  className="w-full max-h-64 object-cover"
                />
              )}
            </div>
            <button
              type="button"
              onClick={handleRemoveMedia}
              className="absolute top-2 right-2 p-1 bg-black bg-opacity-50 rounded-full text-white hover:bg-opacity-70"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Humor Tags */}
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Select humor style(s):</p>
          <div className="flex flex-wrap gap-2">
            {humorStyles.map((style) => (
              <button
                key={style}
                type="button"
                onClick={() => handleTagToggle(style)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedTags.includes(style)
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {style.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              onChange={handleMediaSelect}
              className="hidden"
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-2 px-3 py-2 text-gray-500 hover:text-purple-500 hover:bg-purple-50 rounded-lg transition-colors"
            >
              <Image className="w-5 h-5" />
              <span className="text-sm">Photo/Video</span>
            </button>

            <button
              type="button"
              className="flex items-center space-x-2 px-3 py-2 text-gray-500 hover:text-purple-500 hover:bg-purple-50 rounded-lg transition-colors"
            >
              <Smile className="w-5 h-5" />
              <span className="text-sm">AI Assist</span>
            </button>
          </div>

          <motion.button
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={isLoading || (!content.trim() && !mediaFile)}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
            <span>{isLoading ? 'Posting...' : 'Post'}</span>
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
}