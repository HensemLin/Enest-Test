'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { chatAPI } from '@/lib/api';
import { formatRelativeTime } from '@/lib/utils';
import { MessageSquare, FileText, Plus } from 'lucide-react';
import { NewSessionModal } from '@/components/chat/NewSessionModal';

export default function DashboardPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => chatAPI.getAllSessions(),
    retry: 1, // Only retry once instead of 3 times
    staleTime: 30000, // Consider data fresh for 30 seconds
  });

  const handleNewSession = () => {
    setIsModalOpen(true);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage your tender analysis sessions
            </p>
          </div>
          <Button onClick={handleNewSession} className="gap-2">
            <Plus className="h-4 w-4" />
            New Session
          </Button>
        </div>

        {/* Sessions Grid */}
        {isLoading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader>
                  <div className="h-6 w-3/4 rounded bg-gray-200" />
                  <div className="mt-2 h-4 w-1/2 rounded bg-gray-200" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="h-4 w-full rounded bg-gray-200" />
                    <div className="h-4 w-2/3 rounded bg-gray-200" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : error ? (
          <Card className="p-12 text-center">
            <div className="mx-auto max-w-md">
              <MessageSquare className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                Unable to load sessions
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                The backend API might not be running. Make sure it's started on http://localhost:8000
              </p>
              <Button onClick={handleNewSession} className="mt-6 gap-2">
                <Plus className="h-4 w-4" />
                Create New Session Anyway
              </Button>
            </div>
          </Card>
        ) : sessions && sessions.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <Card
                key={session.id}
                className="hover:shadow-md transition-shadow"
              >
                <CardHeader>
                  <CardTitle className="text-lg">
                    Session {session.session_id.slice(0, 12)}...
                  </CardTitle>
                  <CardDescription>
                    Created {formatRelativeTime(session.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      <span>{session.total_messages} messages</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      <span>{session.pdf_ids.length} PDFs</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      Last activity: {formatRelativeTime(session.last_activity)}
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Link href={`/chat/${session.session_id}`} className="w-full">
                    <Button variant="default" className="w-full" size="sm">
                      Open Chat
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <div className="mx-auto max-w-md">
              <MessageSquare className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                No sessions yet
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Get started by creating a new session and uploading your tender
                documents.
              </p>
              <Button onClick={handleNewSession} className="mt-6 gap-2">
                <Plus className="h-4 w-4" />
                Create First Session
              </Button>
            </div>
          </Card>
        )}
      </div>

      <NewSessionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </MainLayout>
  );
}
