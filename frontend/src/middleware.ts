import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Only intercept API requests
  if (request.nextUrl.pathname.startsWith('/api/')) {
    // Get the API URL from environment
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Clone the request headers
    const requestHeaders = new Headers(request.headers);

    // Add the API key from server-side environment variable
    const apiKey = process.env.API_KEY || '';
    if (apiKey) {
      requestHeaders.set('X-API-KEY', apiKey);
    }

    // Create the backend URL (rewrite /api/* to backend)
    // Preserve pathname exactly as-is (including trailing slash)
    const pathname = request.nextUrl.pathname;
    const search = request.nextUrl.search;
    const backendUrl = `${apiUrl}${pathname}${search}`;

    // Debug logging
    console.log('[Middleware] Original pathname:', pathname);
    console.log('[Middleware] Rewriting to:', backendUrl);

    // Rewrite to backend with the API key header
    return NextResponse.rewrite(backendUrl, {
      request: {
        headers: requestHeaders,
      },
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
