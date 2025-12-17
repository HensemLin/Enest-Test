'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { PDFInfo } from '@/components/chat/PDFInfo';
import { chatAPI, pdfAPI } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '@/types';
import { useUIStore } from '@/store/ui-store';
import { cn } from '@/lib/utils';

export default function ChatPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sidebarOpen } = useUIStore();

  // PDFs are determined by the session, not user selection
  const [sessionPdfIds, setSessionPdfIds] = useState<number[]>([]);

  // Fetch available PDFs
  const { data: pdfs, isLoading: pdfsLoading, error: pdfsError } = useQuery({
    queryKey: ['pdfs'],
    queryFn: () => pdfAPI.getAll(),
    retry: 1,
  });

  // Fetch session info to get pdf_ids
  const { data: sessionInfo } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => chatAPI.getSession(sessionId),
    retry: 1,
  });

  // Load PDF IDs from session info (these are locked for this session)
  useEffect(() => {
    if (sessionInfo && sessionInfo.pdf_ids) {
      setSessionPdfIds(sessionInfo.pdf_ids);
    } else {
      // For new sessions, load from localStorage
      const storedPdfs = localStorage.getItem(`session-${sessionId}-pdfs`);
      if (storedPdfs) {
        try {
          const pdfIds = JSON.parse(storedPdfs);
          setSessionPdfIds(pdfIds);
        } catch (e) {
          console.error('Failed to parse stored PDF IDs:', e);
        }
      }
    }
  }, [sessionInfo, sessionId]);

  // Fetch messages for this session
  const { data: messages, isLoading, error } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => chatAPI.getMessages(sessionId),
    retry: 1,
    refetchInterval: false,
  });

  // Send message mutation with optimistic updates
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => chatAPI.sendMessage(sessionId, message, sessionPdfIds),
    onMutate: async (newMessage) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['messages', sessionId] });

      // Snapshot the previous value
      const previousMessages = queryClient.getQueryData<ChatMessageType[]>(['messages', sessionId]);

      // Optimistically update to show user message immediately
      const optimisticUserMessage: ChatMessageType = {
        id: Date.now(), // Temporary ID
        session_id: sessionId,
        role: 'user',
        content: newMessage,
        timestamp: new Date().toISOString(),
      };

      // Add loading assistant message
      const optimisticAssistantMessage: ChatMessageType = {
        id: Date.now() + 1,
        session_id: sessionId,
        role: 'assistant',
        content: '...',
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData<ChatMessageType[]>(
        ['messages', sessionId],
        (old) => [...(old || []), optimisticUserMessage, optimisticAssistantMessage]
      );

      return { previousMessages };
    },
    onError: (err, newMessage, context) => {
      // Rollback on error
      if (context?.previousMessages) {
        queryClient.setQueryData(['messages', sessionId], context.previousMessages);
      }
    },
    onSuccess: () => {
      // Refetch to get the real messages from backend
      queryClient.invalidateQueries({ queryKey: ['messages', sessionId] });
      // Clean up localStorage after session is created
      localStorage.removeItem(`session-${sessionId}-pdfs`);
    },
  });

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (message: string) => {
    sendMessageMutation.mutate(message);
  };

  return (
    <MainLayout>
      <div className={cn(
        "fixed inset-0 top-16 flex gap-4 bg-gray-50 p-6",
        sidebarOpen ? "left-64" : "left-16"
      )}>
        {/* Sidebar - PDF Info (Read-Only) */}
        <div className="w-80 flex-shrink-0 overflow-y-auto">
          <PDFInfo
            pdfs={pdfs || []}
            sessionPdfIds={sessionPdfIds}
            isLoading={pdfsLoading}
          />
        </div>

        {/* Chat Area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Chat Header */}
          <div className="border-b border-gray-200 bg-white px-6 py-4">
            <h1 className="text-xl font-semibold text-gray-900">
              Chat Session
            </h1>
            <p className="text-sm text-gray-500">
              {sessionPdfIds.length > 0
                ? `Chatting with ${sessionPdfIds.length} PDF${sessionPdfIds.length > 1 ? 's' : ''}`
                : 'Loading session...'}
            </p>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto bg-gray-50">
            {isLoading ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
                  <p className="text-sm text-gray-500">Loading messages...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex h-full items-center justify-center p-6">
                <Card className="max-w-md p-6 text-center">
                  <p className="text-gray-700">
                    Unable to load messages. Make sure the backend is running.
                  </p>
                </Card>
              </div>
            ) : sessionInfo && sessionPdfIds.length === 0 ? (
              <div className="flex h-full items-center justify-center p-6">
                <Card className="max-w-md p-8 text-center">
                  <h3 className="mb-2 text-lg font-semibold text-gray-900">
                    No PDFs in this session
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    This session was created without selecting any PDFs. Please create a new session from the dashboard and select the PDFs you want to chat with.
                  </p>
                  <a href="/" className="inline-block">
                    <button className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
                      Go to Dashboard
                    </button>
                  </a>
                </Card>
              </div>
            ) : messages && messages.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            ) : (
              <div className="flex h-full items-center justify-center p-6">
                <Card className="max-w-md p-8 text-center">
                  <h3 className="mb-2 text-lg font-semibold text-gray-900">
                    Start a conversation
                  </h3>
                  <p className="text-sm text-gray-600">
                    Send a message below to begin chatting with the assistant.
                  </p>
                </Card>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={sendMessageMutation.isPending || sessionPdfIds.length === 0}
            placeholder={
              sendMessageMutation.isPending
                ? 'Sending message...'
                : sessionPdfIds.length === 0
                ? 'Loading session...'
                : 'Type your message...'
            }
          />
        </div>
      </div>
    </MainLayout>
  );
}
