'use client';

import { useState } from 'react';
import { Home, Search, PlusSquare, Heart, User, Menu, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user, logout } = useAuth();

  const navItems = [
    { icon: Home, label: 'Home', href: '/' },
    { icon: Search, label: 'Explore', href: '/explore' },
    { icon: PlusSquare, label: 'Create', href: '/create' },
    { icon: Heart, label: 'Activity', href: '/activity' },
    { icon: User, label: 'Profile', href: '/profile' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                ComedyGram
              </h1>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navItems.map((item) => (
                <motion.a
                  key={item.label}
                  href={item.href}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                >
                  <item.icon className="w-5 h-5" />
                  <span className="hidden lg:block">{item.label}</span>
                </motion.a>
              ))}
            </div>
          </div>

          {/* User Menu */}
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              {user ? (
                <div className="relative">
                  <button
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="flex items-center space-x-2 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">
                        {user.displayName?.charAt(0).toUpperCase() || 'U'}
                      </span>
                    </div>
                  </button>

                  {isMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5"
                    >
                      <div className="py-1">
                        <a
                          href="/profile"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          Your Profile
                        </a>
                        <a
                          href="/settings"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          Settings
                        </a>
                        <button
                          onClick={logout}
                          className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          Sign out
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <a
                    href="/login"
                    className="text-gray-700 hover:text-purple-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Sign in
                  </a>
                  <a
                    href="/register"
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Sign up
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 rounded-md text-gray-700 hover:text-purple-600 hover:bg-purple-50"
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden"
          >
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t border-gray-200">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-purple-600 hover:bg-purple-50"
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </a>
              ))}

              {user ? (
                <>
                  <div className="pt-4 pb-3 border-t border-gray-200">
                    <div className="flex items-center px-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold">
                          {user.displayName?.charAt(0).toUpperCase() || 'U'}
                        </span>
                      </div>
                      <div className="ml-3">
                        <div className="text-base font-medium text-gray-800">
                          {user.displayName}
                        </div>
                        <div className="text-sm font-medium text-gray-500">
                          @{user.username}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 space-y-1">
                      <a
                        href="/profile"
                        className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-purple-600 hover:bg-purple-50"
                      >
                        Your Profile
                      </a>
                      <a
                        href="/settings"
                        className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-purple-600 hover:bg-purple-50"
                      >
                        Settings
                      </a>
                      <button
                        onClick={logout}
                        className="block w-full text-left px-3 py-2 text-base font-medium text-gray-700 hover:text-purple-600 hover:bg-purple-50"
                      >
                        Sign out
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="pt-4 pb-3 border-t border-gray-200 space-y-1">
                  <a
                    href="/login"
                    className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-purple-600 hover:bg-purple-50"
                  >
                    Sign in
                  </a>
                  <a
                    href="/register"
                    className="block px-3 py-2 text-base font-medium bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Sign up
                  </a>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </nav>
  );
}