#!/usr/bin/env node
/**
 * Okta Terraform GitOps - Webhook Handler
 *
 * Proof of Concept webhook handler for Demo Platform component integration.
 * Handles component lifecycle webhooks and provisions GitHub repositories.
 */

require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const webhookRoutes = require('./routes/webhooks');
const { logger } = require('./lib/logger');
const { validateConfig } = require('./lib/config');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('user-agent')
  });
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'okta-terraform-webhook-handler',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Webhook routes
app.use('/webhooks', webhookRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path
  });
});

// Validate configuration on startup
try {
  validateConfig();
  logger.info('Configuration validated successfully');
} catch (error) {
  logger.error('Configuration validation failed:', error.message);
  process.exit(1);
}

// Start server
app.listen(PORT, () => {
  logger.info(`🚀 Webhook handler listening on port ${PORT}`);
  logger.info(`📍 Environment: ${process.env.NODE_ENV || 'development'}`);
  logger.info(`🔗 Health check: http://localhost:${PORT}/health`);
  logger.info(`📥 Webhook endpoint: http://localhost:${PORT}/webhooks/component-requested`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully...');
  process.exit(0);
});

module.exports = app;
