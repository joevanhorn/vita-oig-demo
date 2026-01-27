/**
 * Cryptographic utilities for webhook signature verification
 * and GitHub secret encryption
 */

const crypto = require('crypto');

/**
 * Verify webhook signature
 *
 * @param {Object} payload - Webhook payload
 * @param {string} signature - Signature from X-Webhook-Signature header
 * @param {string} secret - Shared secret
 * @returns {boolean}
 */
function verifyWebhookSignature(payload, signature, secret) {
  if (!signature || !secret) {
    return false;
  }

  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(JSON.stringify(payload));
  const calculated = hmac.digest('hex');

  // Timing-safe comparison
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(calculated)
    );
  } catch (err) {
    return false;
  }
}

/**
 * Encrypt a secret for GitHub using libsodium
 *
 * @param {string} value - Secret value to encrypt
 * @param {string} publicKey - GitHub public key (base64)
 * @returns {Promise<string>} Encrypted value (base64)
 */
async function encryptSecret(value, publicKey) {
  const sodium = require('libsodium-wrappers');
  await sodium.ready;

  const messageBytes = Buffer.from(value);
  const keyBytes = Buffer.from(publicKey, 'base64');

  const encryptedBytes = sodium.crypto_box_seal(messageBytes, keyBytes);

  return Buffer.from(encryptedBytes).toString('base64');
}

module.exports = {
  verifyWebhookSignature,
  encryptSecret
};
