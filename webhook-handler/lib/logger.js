/**
 * Simple logger with different log levels
 */

const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3
};

const currentLevel = LOG_LEVELS[process.env.LOG_LEVEL] || LOG_LEVELS.info;

function log(level, message, meta = {}) {
  if (LOG_LEVELS[level] > currentLevel) return;

  const timestamp = new Date().toISOString();
  const emoji = {
    error: '❌',
    warn: '⚠️',
    info: 'ℹ️',
    debug: '🔍'
  }[level] || '';

  const output = {
    timestamp,
    level: level.toUpperCase(),
    message,
    ...meta
  };

  const logFn = level === 'error' ? console.error : console.log;

  if (process.env.NODE_ENV === 'production') {
    // JSON logging for production
    logFn(JSON.stringify(output));
  } else {
    // Pretty logging for development
    logFn(`${emoji} [${timestamp}] ${level.toUpperCase()}: ${message}`, meta);
  }
}

const logger = {
  error: (message, meta) => log('error', message, meta),
  warn: (message, meta) => log('warn', message, meta),
  info: (message, meta) => log('info', message, meta),
  debug: (message, meta) => log('debug', message, meta)
};

module.exports = { logger };
