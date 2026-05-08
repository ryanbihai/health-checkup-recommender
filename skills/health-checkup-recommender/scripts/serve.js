#!/usr/bin/env node
'use strict';

// OceanBus Yellow Pages service for health-checkup-recommender
// Long-running: listens for patient profiles and replies with recommendations.
// First run: node scripts/register.js (one-time)
// Then:      node scripts/serve.js

const { createOceanBus } = require('oceanbus');
const { recommend } = require('./recommend');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DATA_DIR = path.join(os.homedir(), '.oceanbus-checkup-recommender');
const CRED_FILE = path.join(DATA_DIR, 'credentials.json');

function loadCredentials() {
  try {
    if (fs.existsSync(CRED_FILE)) {
      return JSON.parse(fs.readFileSync(CRED_FILE, 'utf-8'));
    }
  } catch (_) {}
  return null;
}

async function main() {
  const creds = loadCredentials();
  if (!creds) {
    console.error('Not registered. Run: node scripts/register.js');
    process.exit(1);
  }

  const ob = await createOceanBus({
    keyStore: { type: 'memory' },
    identity: { agent_id: creds.agent_id, api_key: creds.api_key },
  });

  const key = await ob.createServiceKey();
  ob.l1.yellowPages.setIdentity(creds.openid, key.signer, key.publicKey);
  ob.l1.yellowPages.startHeartbeat({ intervalMs: 5 * 60 * 1000 });

  console.log('[checkup-recommender] Listening on OceanBus...');
  console.log('  OpenID: ' + creds.openid.slice(0, 16) + '...');

  ob.startListening(async (msg) => {
    try {
      let request;
      try { request = JSON.parse(msg.content); }
      catch {
        await ob.sendJson(msg.from_openid, {
          error: 'Invalid request. Send patient profile as JSON: { "age": 45, "gender": "male", "symptoms": ["胸闷"], "consent": false }'
        });
        return;
      }

      if (!request.age || !request.gender) {
        await ob.sendJson(msg.from_openid, {
          error: 'Missing required fields: age, gender'
        });
        return;
      }

      const result = await recommend(request);
      await ob.sendJson(msg.from_openid, result);
      console.log('  Replied with recommendation:', result.totalPrice + ' yuan,', result.recommendations.length + ' items');
    } catch (e) {
      console.error('  Error:', e.message);
      try {
        await ob.sendJson(msg.from_openid, { error: 'Recommendation failed: ' + e.message });
      } catch (_) {}
    }
  });

  await new Promise(() => {});
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
