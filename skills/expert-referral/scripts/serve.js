#!/usr/bin/env node
'use strict';

// OceanBus Yellow Pages service for china-top-doctor-referral
// Long-running: listens for search queries and replies with JSON results.
// First run: node scripts/register.js (one-time)
// Then:      node scripts/serve.js

const { createOceanBus } = require('oceanbus');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DATA_DIR = path.join(os.homedir(), '.oceanbus-doctor-referral');
const CRED_FILE = path.join(DATA_DIR, 'credentials.json');
const REFER_PY = path.join(__dirname, 'refer.py');

function loadCredentials() {
  try {
    if (fs.existsSync(CRED_FILE)) {
      return JSON.parse(fs.readFileSync(CRED_FILE, 'utf-8'));
    }
  } catch (_) {}
  return null;
}

function searchPython(query) {
  return new Promise((resolve, reject) => {
    const python = process.platform === 'win32' ? 'python' : 'python3';
    const proc = spawn(python, [REFER_PY, 'search', '--format', 'json', query], {
      cwd: path.dirname(REFER_PY),
      timeout: 10000,
    });
    let stdout = '', stderr = '';
    proc.stdout.on('data', d => stdout += d);
    proc.stderr.on('data', d => stderr += d);
    proc.on('close', code => {
      if (code !== 0) { reject(new Error(stderr || 'search failed with code ' + code)); return; }
      try { resolve(JSON.parse(stdout)); }
      catch (e) { reject(new Error('invalid JSON: ' + stdout.slice(0, 200))); }
    });
  });
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

  console.log('[doctor-referral] Listening on OceanBus...');
  console.log('  OpenID: ' + creds.openid.slice(0, 16) + '...');

  ob.startListening(async (msg) => {
    try {
      let query;
      try { const data = JSON.parse(msg.content); query = data.query || data.q || ''; }
      catch { query = msg.content.trim(); }

      if (!query) {
        await ob.sendJson(msg.from_openid, { error: 'No query provided. Send { "query": "心内科" }' });
        return;
      }

      const result = await searchPython(query);
      await ob.sendJson(msg.from_openid, result);
      const count = (result.primary || []).length + (result.secondary || []).length;
      console.log('  Replied to', msg.from_openid.slice(0, 12) + '...:', query, '(' + count + ' results)');
    } catch (e) {
      console.error('  Error processing message:', e.message);
      try {
        await ob.sendJson(msg.from_openid, { error: 'Search failed: ' + e.message });
      } catch (_) {}
    }
  });

  await new Promise(() => {}); // keep running
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
