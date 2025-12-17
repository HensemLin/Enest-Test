// Load environment variables from root .env file (for local development)
if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config({ path: '../.env' });
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',

  // Prevent Next.js from removing trailing slashes
  trailingSlash: false,
  skipTrailingSlashRedirect: true,
};

module.exports = nextConfig;
