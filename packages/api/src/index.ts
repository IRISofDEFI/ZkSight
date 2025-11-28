/**
 * Main entry point for the API server
 * 
 * This file exports the server setup for use in other modules
 * and starts the server when run directly.
 */
export { createApp } from './server';

// Start server if this is the main module
if (require.main === module) {
  require('./server');
}
