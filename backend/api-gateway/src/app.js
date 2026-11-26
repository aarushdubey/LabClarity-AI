/** Builds the Express application (no network listening here, so it is testable). */
import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { API_PREFIX } from './config/constants.js';
import { securityMiddleware } from './middleware/security.js';
import { createApiLimiter } from './middleware/rateLimiter.js';
import { requestLogger } from './middleware/requestLogger.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';
import { createApiRouter } from './routes/index.js';

export function createApp({ config, controllers }) {
  const app = express();

  app.disable('x-powered-by');
  if (config.trustProxy) app.set('trust proxy', config.trustProxy);

  app.use(requestLogger);
  app.use(securityMiddleware(config));
  app.use(API_PREFIX, createApiLimiter(config.rateLimit), createApiRouter(controllers, config));

  if (!config.isTest) {
    const candidates = [
      path.resolve(process.cwd(), 'frontend/dist'),
      path.resolve(process.cwd(), '../../frontend/dist'),
      path.resolve(import.meta.dirname, '../../../frontend/dist'),
    ];
    const dist = candidates.find((d) => fs.existsSync(path.join(d, 'index.html')));
    if (dist) {
      app.use(express.static(dist));
      app.use((req, res, next) => {
        if (req.method !== 'GET') return next();
        if (req.path.startsWith('/api') || req.path.startsWith('/health')) return next();
        res.sendFile(path.join(dist, 'index.html'));
      });
    }
  }

  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}
