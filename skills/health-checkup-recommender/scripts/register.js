#!/usr/bin/env node
'use strict';

// OceanBus registration + Yellow Pages publish for health-checkup-recommender
// One-time setup. Run: node scripts/register.js

const { createOceanBus } = require('oceanbus');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DATA_DIR = path.join(os.homedir(), '.oceanbus-checkup-recommender');
const CRED_FILE = path.join(DATA_DIR, 'credentials.json');

const YP_TAGS = [
  'health-checkup', 'medical', '体检推荐',
  '个性化体检', '循证医学', 'health-screening', 'preventive-care'
];

const YP_DESC = 'AI智能体检推荐服务。依据国家卫建委2025版指引及BMJ/JAMA循证数据，提供个性化体检方案。覆盖全国220城数百家机构。';

function ensureDir() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

function loadCredentials() {
  try {
    if (fs.existsSync(CRED_FILE)) {
      return JSON.parse(fs.readFileSync(CRED_FILE, 'utf-8'));
    }
  } catch (_) {}
  return null;
}

function saveCredentials(agentId, apiKey, openid) {
  ensureDir();
  fs.writeFileSync(CRED_FILE, JSON.stringify({
    agent_id: agentId,
    api_key: apiKey,
    openid: openid,
    source: 'health-checkup-recommender',
    created_at: new Date().toISOString(),
  }, null, 2), { mode: 0o600 });
}

async function main() {
  ensureDir();

  const existing = loadCredentials();
  if (existing) {
    console.log('Already registered.');
    console.log('  OpenID: ' + existing.openid.slice(0, 16) + '...');
    console.log('  To re-register, delete: ' + DATA_DIR);
    return;
  }

  console.log('Registering OceanBus agent...');
  const ob = await createOceanBus({ keyStore: { type: 'memory' } });

  const reg = await ob.register();
  console.log('  Agent ID: ' + reg.agent_id);

  const openid = await ob.getOpenId();
  console.log('  OpenID:   ' + openid);

  saveCredentials(reg.agent_id, reg.api_key, openid);
  console.log('  Credentials saved to ' + CRED_FILE);

  console.log('Publishing to Yellow Pages...');
  const key = await ob.createServiceKey();
  ob.l1.yellowPages.setIdentity(openid, key.signer, key.publicKey);
  await ob.l1.yellowPages.registerService(YP_TAGS, YP_DESC);
  console.log('  Published with tags: ' + YP_TAGS.join(', '));

  ob.l1.yellowPages.clearIdentity();
  await ob.destroy();
  console.log('Done. Now run: node scripts/serve.js');
}

main().catch(err => {
  console.error('Registration failed:', err.message);
  process.exit(1);
});
