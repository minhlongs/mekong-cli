/**
 * AGI Level 9: Vector Service — 知識注入 (Knowledge Injection)
 *
 * 📜 Binh Pháp Ch.13 用間: 「先知者，不可取於鬼神... 必取於人，知敵之情者也」
 *    "Foreknowledge cannot be gotten from spirits... it must be obtained from men who know the enemy's condition"
 *
 * This service provides:
 * 1. Semantic Embedding via Antigravity Proxy (port 20128)
 * 2. Persistent Vector Store via LanceDB (Columnar Disk-based)
 * 3. SQL-style metadata filtering for RAG
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const config = require('../config');
const lancedb = require('@lancedb/lancedb');

const DATA_DIR = path.join(config.MEKONG_DIR, 'apps/openclaw-worker/data/vector_db');
const PROXY_PORT = config.PROXY_PORT || 20128;

// Ensure data dir
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

function log(msg) {
  const ts = new Date().toLocaleTimeString('en-US', { hour12: false });
  const line = `[${ts}] [tom-hum] [VECTOR] ${msg}`;
  try { fs.appendFileSync(config.LOG_FILE, line + '\n'); } catch (e) { }
}

/**
 * Get embedding vector for a given text.
 * Uses Antigravity Proxy (OpenAI-compatible embeddings endpoint).
 */
async function getEmbedding(text) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      input: text,
      model: "text-embedding-3-small" // Proxy maps this to best available
    });

    const req = http.request({
      hostname: '127.0.0.1',
      port: PROXY_PORT,
      path: '/v1/embeddings',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'ollama' // Required by Antigravity Proxy
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (result.error) throw new Error(result.error.message || JSON.stringify(result.error));
          const vector = result.data?.[0]?.embedding;
          if (!vector) throw new Error('No embedding returned from proxy');
          resolve(vector);
        } catch (e) {
          reject(new Error(`Embedding parse error: ${e.message} | Response: ${data.slice(0, 100)}`));
        }
      });
    });

    req.on('error', (e) => reject(new Error(`Embedding request failed: ${e.message}`)));
    req.write(body);
    req.end();
  });
}

/**
 * Connect to LanceDB and get/create a table.
 */
async function getTable(tableName, schema = null) {
  try {
    const db = await lancedb.connect(DATA_DIR);
    const tableNames = await db.tableNames();

    if (tableNames.includes(tableName)) {
      return await db.openTable(tableName);
    }

    if (!schema) {
      throw new Error(`Table ${tableName} does not exist and no schema provided for creation.`);
    }

    return await db.createTable(tableName, schema);
  } catch (e) {
    log(`Table Error (${tableName}): ${e.message}`);
    throw e;
  }
}

/**
 * Upsert data into a LanceDB table.
 * Data should be an array of objects. If objects don't have vectors, they will be generated.
 */
async function upsert(tableName, data) {
  const table = await getTable(tableName, data);

  // Ensure every item has a vector
  for (const item of data) {
    if (!item.vector && item.text) {
      item.vector = await getEmbedding(item.text);
    }
  }

  await table.add(data);
  log(`Upserted ${data.length} items into ${tableName}`);
}

/**
 * Perform semantic search.
 */
async function search(tableName, queryText, filter = "", limit = 5) {
  try {
    const vector = await getEmbedding(queryText);
    const table = await getTable(tableName);

    let query = table.search(vector).limit(limit);
    if (filter) {
      query = query.where(filter);
    }

    const results = await query.execute();
    return results;
  } catch (e) {
    log(`Search Error (${tableName}): ${e.message}`);
    return [];
  }
}

module.exports = {
  getEmbedding,
  getTable,
  upsert,
  search
};
