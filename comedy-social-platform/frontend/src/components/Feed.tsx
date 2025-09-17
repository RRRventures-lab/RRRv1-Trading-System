'use client';

import { useState, useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Post, CreatePostData } from '@/types';
import api from '@/lib/api';
import PostCard from './PostCard';
import CreatePost from './CreatePost';
import { motion } from 'framer-motion';

const fetchPosts = async ({ pageParam = 1 }) => {
  const response = await api.get(`/posts?page=${pageParam}&limit=10`);
  return response.data;
};

const createPost = async (data: CreatePostData) => {
  const formData = new FormData();
  formData.append('content', data.content);
  formData.append('humorTags', JSON.stringify(data.humorTags));
  if (data.media) {
    formData.append('media', data.media);
  }

  const response = await api.post('/posts', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export default function Feed() {
  const [isCreatingPost, setIsCreatingPost] = useState(false);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: fetchPosts,
    getNextPageParam: (lastPage, pages) => {
      return lastPage.length === 10 ? pages.length + 1 : undefined;
    },
    initialPageParam: 1,
  });

  const handleCreatePost = async (postData: CreatePostData) => {
    try {
      setIsCreatingPost(true);
      await createPost(postData);
      refetch();
    } catch (error) {
      console.error('Error creating post:', error);
    } finally {
      setIsCreatingPost(false);
    }
  };

  const handleLike = async (postId: string) => {
    try {
      await api.post(`/posts/${postId}/like`);
      refetch();
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  const handleLaugh = async (postId: string) => {
    try {
      await api.post(`/posts/${postId}/laugh`);
      refetch();
    } catch (error) {
      console.error('Error reacting to post:', error);
    }
  };

  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + document.documentElement.scrollTop >=
        document.documentElement.offsetHeight - 1000
      ) {
        if (hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const posts = data?.pages.flatMap(page => page) || [];

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-md h-64 animate-pulse">
            <div className="p-4">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                <div className="space-y-2">
                  <div className="w-24 h-4 bg-gray-300 rounded"></div>
                  <div className="w-16 h-3 bg-gray-300 rounded"></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="w-full h-4 bg-gray-300 rounded"></div>
                <div className="w-3/4 h-4 bg-gray-300 rounded"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <CreatePost onSubmit={handleCreatePost} isLoading={isCreatingPost} />

      <div className="space-y-6">
        {posts.map((post: Post, index) => (
          <motion.div
            key={post.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <PostCard
              post={post}
              onLike={handleLike}
              onLaugh={handleLaugh}
            />
          </motion.div>
        ))}

        {isFetchingNextPage && (
          <div className="bg-white rounded-lg shadow-md h-64 animate-pulse">
            <div className="p-4">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                <div className="space-y-2">
                  <div className="w-24 h-4 bg-gray-300 rounded"></div>
                  <div className="w-16 h-3 bg-gray-300 rounded"></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="w-full h-4 bg-gray-300 rounded"></div>
                <div className="w-3/4 h-4 bg-gray-300 rounded"></div>
              </div>
            </div>
          </div>
        )}

        {!hasNextPage && posts.length > 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">You've reached the end! 🎭</p>
          </div>
        )}

        {posts.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">😂</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No posts yet!
            </h3>
            <p className="text-gray-500">
              Be the first to share something funny
            </p>
          </div>
        )}
      </div>
    </div>
  );
}