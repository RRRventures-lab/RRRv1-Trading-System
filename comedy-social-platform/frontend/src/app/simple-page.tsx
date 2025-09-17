'use client';

import { useState, useEffect } from 'react';
import { Heart, MessageCircle, Share, Laugh } from 'lucide-react';

interface Post {
  id: string;
  userId: string;
  content: string;
  mediaUrl?: string;
  mediaType?: string;
  humorTags: string[];
  likes: number;
  laughReacts: number;
  comments: number;
  shares: number;
  isAIGenerated: boolean;
  createdAt: string;
  user: {
    username: string;
    displayName: string;
    profilePicture?: string;
    verified: boolean;
  };
}

const humorStyleColors: Record<string, string> = {
  'dark': 'bg-gray-800 text-white',
  'wholesome': 'bg-green-100 text-green-800',
  'satirical': 'bg-red-100 text-red-800',
  'observational': 'bg-blue-100 text-blue-800',
  'surreal': 'bg-purple-100 text-purple-800',
  'wordplay': 'bg-yellow-100 text-yellow-800',
  'physical': 'bg-orange-100 text-orange-800',
  'self_deprecating': 'bg-pink-100 text-pink-800',
};

export default function SimplePage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/posts');
        const data = await response.json();
        setPosts(data);
      } catch (error) {
        console.error('Error fetching posts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const handleLike = async (postId: string) => {
    try {
      await fetch(`http://localhost:5001/api/posts/${postId}/like`, {
        method: 'POST',
      });
      // Update local state
      setPosts(posts.map(post =>
        post.id === postId
          ? { ...post, likes: post.likes + 1 }
          : post
      ));
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  const handleLaugh = async (postId: string) => {
    try {
      await fetch(`http://localhost:5001/api/posts/${postId}/laugh`, {
        method: 'POST',
      });
      // Update local state
      setPosts(posts.map(post =>
        post.id === postId
          ? { ...post, laughReacts: post.laughReacts + 1 }
          : post
      ));
    } catch (error) {
      console.error('Error laughing at post:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🎭</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading ComedyGram...</h2>
          <p className="text-gray-600">Getting the jokes ready!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              ComedyGram
            </h1>
            <nav className="hidden md:flex space-x-8">
              <a href="#" className="text-gray-700 hover:text-purple-600">Home</a>
              <a href="#" className="text-gray-700 hover:text-purple-600">Explore</a>
              <a href="#" className="text-gray-700 hover:text-purple-600">Create</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-2xl mx-auto py-8 px-4">
        <div className="space-y-6">
          {posts.map((post) => (
            <div key={post.id} className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
              {/* Post Header */}
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
              </div>

              {/* Post Content */}
              <div className="px-4 pb-2">
                <p className="text-gray-900 mb-3 whitespace-pre-wrap">{post.content}</p>

                {/* Humor Tags */}
                {post.humorTags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {post.humorTags.map((tag) => (
                      <span
                        key={tag}
                        className={`px-2 py-1 rounded-full text-xs font-medium ${humorStyleColors[tag] || 'bg-gray-100 text-gray-800'}`}
                      >
                        {tag.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="px-4 py-3 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-6">
                    <button
                      onClick={() => handleLike(post.id)}
                      className="flex items-center space-x-2 text-gray-500 hover:text-red-500 transition-colors"
                    >
                      <Heart className="w-5 h-5" />
                      <span className="text-sm">{post.likes}</span>
                    </button>

                    <button
                      onClick={() => handleLaugh(post.id)}
                      className="flex items-center space-x-2 text-gray-500 hover:text-yellow-500 transition-colors"
                    >
                      <Laugh className="w-5 h-5" />
                      <span className="text-sm">{post.laughReacts}</span>
                    </button>

                    <button className="flex items-center space-x-2 text-gray-500 hover:text-blue-500">
                      <MessageCircle className="w-5 h-5" />
                      <span className="text-sm">{post.comments}</span>
                    </button>

                    <button className="flex items-center space-x-2 text-gray-500 hover:text-green-500">
                      <Share className="w-5 h-5" />
                      <span className="text-sm">{post.shares}</span>
                    </button>
                  </div>

                  <span className="text-xs text-gray-400">
                    {new Date(post.createdAt).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {posts.length === 0 && (
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
      </main>
    </div>
  );
}