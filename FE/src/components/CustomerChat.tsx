import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Upload, MessageCircle, Store, Clock, CheckCircle, AlertCircle } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  created_at: string;
  token_count?: number;
}

interface Restaurant {
  slug: string;
  name: string;
  id: string;
  description: string;
}

const API_BASE_URL = 'http://localhost:8000/api';

export default function CustomerChat() {
  const { slug } = useParams<{ slug: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [initializing, setInitializing] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (slug) {
      initializeChat();
    }
  }, [slug]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeChat = async () => {
    try {
      setInitializing(true);
      setError('');

      // Create a new session
      const sessionResponse = await fetch(`${API_BASE_URL}/tenant/${slug}/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!sessionResponse.ok) {
        throw new Error('Failed to create session');
      }

      const sessionData = await sessionResponse.json();
      setSessionId(sessionData.session_id);
      setRestaurant(sessionData.restaurant);

      // Add welcome message
      const welcomeMessage: Message = {
        id: 'welcome',
        sender: 'bot',
        content: `${sessionData.restaurant.description}\n\nI can help you with:\n• Browse our menu\n• Place orders\n• Check order status\n• Answer questions about our food\n\nWhat would you like to do today?`,
        created_at: new Date().toISOString()
      };
      setMessages([welcomeMessage]);

    } catch (err: any) {
      setError(err.message || 'Failed to initialize chat');
    } finally {
      setInitializing(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !sessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content: inputMessage,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Retry logic for better reliability
    let retryCount = 0;
    const maxRetries = 3;
    
    while (retryCount < maxRetries) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        const response = await fetch(`${API_BASE_URL}/tenant/${slug}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: inputMessage,
            session_id: sessionId
          }),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (!data.response) {
          throw new Error('Empty response from server');
        }
        
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          content: data.response,
          created_at: new Date().toISOString(),
          token_count: data.token_count
        };

        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
        return; // Success, exit retry loop
        
      } catch (err: any) {
        retryCount++;
        console.error(`Attempt ${retryCount} failed:`, err);
        
        if (retryCount >= maxRetries) {
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            sender: 'bot',
            content: `I'm having trouble connecting right now. Please check your internet connection and try again. ${err.name === 'AbortError' ? '(Request timed out)' : ''}`,
            created_at: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
          setIsLoading(false);
          return;
        }
        
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/tenant/${slug}/upload-payment-proof`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload image');
      }

      const data = await response.json();
      
      // Add user message about upload
      const uploadMessage: Message = {
        id: Date.now().toString(),
        sender: 'user',
        content: `📎 Uploaded payment proof: ${file.name}`,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, uploadMessage]);

      // Send the image URL to the bot
      setInputMessage(`I've uploaded payment proof. Image URL: ${data.image_url}`);
      
    } catch (err: any) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        sender: 'bot',
        content: 'Failed to upload image. Please try again.',
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  if (initializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Initializing chat...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={initializeChat}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!restaurant) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Restaurant Not Found</h1>
          <p className="text-gray-600">The restaurant you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <div className="h-12 w-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <Store className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <h1 className="text-xl font-bold text-gray-900">{restaurant.name}</h1>
                <p className="text-sm text-gray-500">AI Assistant • Session: {sessionId?.slice(0, 8)}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600 font-medium">Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          {/* Messages Area */}
          <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-gray-50 to-white">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  {message.sender === 'bot' && (
                    <div className="flex items-center mb-2">
                      <MessageCircle className="h-4 w-4 text-blue-600 mr-2" />
                      <span className="text-xs font-medium text-blue-600">AI Assistant</span>
                    </div>
                  )}
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </div>
                  <div className={`text-xs mt-2 flex items-center justify-between ${
                    message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    <span>
                      {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {message.token_count && (
                      <span className="ml-2">
                        {message.token_count} tokens
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <MessageCircle className="h-4 w-4 text-blue-600" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4 bg-white">
            <div className="flex items-end space-x-3">
              <button
                onClick={handleFileUpload}
                className="flex-shrink-0 p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="Upload payment proof"
              >
                <Upload className="h-5 w-5" />
              </button>
              
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  rows={1}
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                />
              </div>
              
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="flex-shrink-0 p-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transform transition-all hover:scale-105 active:scale-95"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send • Upload images for payment proof
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: MessageCircle, text: 'View Menu', action: () => setInputMessage('Show me your menu') },
            { icon: Store, text: 'Place Order', action: () => setInputMessage('I want to place an order') },
            { icon: Clock, text: 'Order Status', action: () => setInputMessage('Check my order status') },
            { icon: CheckCircle, text: 'Payment Info', action: () => setInputMessage('How do I pay?') }
          ].map((item, index) => (
            <button
              key={index}
              onClick={item.action}
              className="flex items-center justify-center space-x-2 p-3 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-blue-300 transition-colors"
            >
              <item.icon className="h-4 w-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">{item.text}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}