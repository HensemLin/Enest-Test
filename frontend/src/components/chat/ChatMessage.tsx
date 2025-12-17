'use client';

import { useState } from 'react';
import { ChatMessage as ChatMessageType } from '@/types';
import { formatDateTime } from '@/lib/utils';
import { User, Bot, Copy, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SourceCard } from './SourceCard';
import { TypingIndicator } from './TypingIndicator';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
  };

  const sourceCount = message.sources?.length || 0;

  return (
    <div className={`flex gap-4 p-4 ${isUser ? 'bg-white' : 'bg-gray-50'}`}>
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
          isUser ? 'bg-primary-100' : 'bg-gray-200'
        }`}
      >
        {isUser ? (
          <User className="h-5 w-5 text-primary-700" />
        ) : (
          <Bot className="h-5 w-5 text-gray-700" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-gray-500">
            {formatDateTime(message.timestamp)}
          </span>
        </div>

        <div className="prose prose-sm max-w-none text-gray-700">
          {message.content === '...' ? (
            <TypingIndicator />
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Sources Accordion */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-primary-600 transition-colors"
            >
              {sourcesExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              Sources ({sourceCount})
            </button>

            {sourcesExpanded && (
              <div className="mt-2 grid gap-2 animate-in slide-in-from-top-2 duration-200">
                {message.sources.map((source, idx) => (
                  <SourceCard key={idx} source={source} index={idx + 1} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        {!isUser && message.content !== '...' && (
          <div className="flex gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="gap-2"
            >
              <Copy className="h-4 w-4" />
              Copy
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
