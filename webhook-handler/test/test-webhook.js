#!/usr/bin/env node
/**
 * Test webhook handler locally
 *
 * Usage: node test/test-webhook.js
 */

require('dotenv').config();
const axios = require('axios');
const mockPayload = require('./mock-webhook-payload.json');

const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:3000/webhooks/component-requested';

async function testWebhook() {
  console.log('🧪 Testing webhook handler...\n');
  console.log(`📍 Target: ${WEBHOOK_URL}\n`);

  // Update mock payload with current timestamp
  const payload = {
    ...mockPayload,
    timestamp: new Date().toISOString(),
    component_instance_id: `instance-test-${Date.now()}`
  };

  console.log('📤 Sending payload:');
  console.log(JSON.stringify(payload, null, 2));
  console.log('\n');

  try {
    const response = await axios.post(WEBHOOK_URL, payload, {
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': 'test-signature-ignored-in-dev-mode'
      },
      timeout: 10000
    });

    console.log('✅ Response received:');
    console.log(`   Status: ${response.status} ${response.statusText}`);
    console.log(`   Data:`, response.data);
    console.log('\n');

    console.log('✅ Webhook test completed successfully!');
    console.log('📝 Check the server logs for provisioning progress.');

  } catch (error) {
    console.error('❌ Test failed:', error.message);

    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }

    process.exit(1);
  }
}

// Run test
testWebhook();
