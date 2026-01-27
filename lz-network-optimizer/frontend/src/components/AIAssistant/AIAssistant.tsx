import { useState } from 'react';
import { Bot, Send, Lightbulb, User } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

interface AIAssistantProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  messages: Message[];
}

const SUGGESTIONS = [
  'Optimize download speed',
  'Improve network access success',
  'Fix upload quality issues',
  'Reduce connection drops',
];

export default function AIAssistant({ onSubmit, isLoading, messages }: AIAssistantProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (!isLoading) {
      onSubmit(suggestion);
    }
  };

  return (
    <div className="card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/5">
        <div className="w-10 h-10 bg-accent-teal/20 rounded-lg flex items-center justify-center">
          <Bot className="w-5 h-5 text-accent-teal" />
        </div>
        <div>
          <h3 className="font-semibold text-white">AI Assistant</h3>
          <p className="text-xs text-gray-500">Natural language optimization</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-[200px]">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.isBot ? '' : 'flex-row-reverse'}`}
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                message.isBot ? 'bg-accent-teal/20' : 'bg-accent-green/20'
              }`}
            >
              {message.isBot ? (
                <Bot className="w-4 h-4 text-accent-teal" />
              ) : (
                <User className="w-4 h-4 text-accent-green" />
              )}
            </div>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.isBot
                  ? 'bg-bg-card-hover text-gray-300'
                  : 'bg-accent-green/20 text-white'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              <span className="text-xs text-gray-500 mt-1 block">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-accent-teal/20 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-accent-teal" />
            </div>
            <div className="bg-bg-card-hover rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-accent-teal rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-accent-teal rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-accent-teal rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Suggestions */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <Lightbulb className="w-3 h-3" />
          <span>TRY ASKING</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={isLoading}
              className="text-left text-sm text-gray-400 bg-bg-input hover:bg-bg-card-hover px-3 py-2 rounded-lg border border-white/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Lightbulb className="w-3 h-3 text-accent-green flex-shrink-0" />
              <span className="truncate">{suggestion}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe your network optimization goal..."
          disabled={isLoading}
          className="input flex-1"
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="btn-primary px-4 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}
