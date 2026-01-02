import { NextRequest, NextResponse } from 'next/server';

// Configure route segment for long-running operations
export const maxDuration = 300; // 5 minutes (max for Vercel Pro)
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const apiKey = process.env.API_KEY || '';

    // Get request body
    const body = await request.json();

    // Forward request to backend with extended timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

    try {
      const response = await fetch(`${apiUrl}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': apiKey,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Get response data
      const data = await response.json();

      // Return response with same status code
      return NextResponse.json(data, { status: response.status });

    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { error: 'Request timeout - the chat operation took too long' },
          { status: 504 }
        );
      }

      throw fetchError;
    }

  } catch (error: any) {
    console.error('[API Route] Error proxying chat message:', error);

    return NextResponse.json(
      {
        error: 'Failed to process chat message',
        details: error.message
      },
      { status: 500 }
    );
  }
}
