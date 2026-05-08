#!/usr/bin/env node
'use strict';

// OceanBus registration + Yellow Pages publish for china-top-doctor-referral
// One-time setup. Run: node scripts/register.js

const { createOceanBus } = require('oceanbus');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DATA_DIR = path.join(os.homedir(), '.oceanbus-doctor-referral');
const CRED_FILE = path.join(DATA_DIR, 'credentials.json');

const YP_TAGS = [
  'doctor-referral', 'medical', 'expert-search',
  'Beijing', 'Shanghai', '三甲医院', '专家推荐'
];

const YP_DESC = '顶级三甲医院专家推荐服务。228位协和/复旦/交大系主任副主任专家，覆盖北京上海高端私立门诊。按科室/疾病/症状搜索匹配。';

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
    source: 'china-top-doctor-referral',
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
