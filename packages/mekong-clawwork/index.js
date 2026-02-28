'use strict';

const fs = require('fs');
const path = require('path');

/**
 * ClawWorkBridge — thin wrapper around ClawWork AI Coworker economic benchmark.
 * Reference: github.com/HKUDS/ClawWork
 */
class ClawWorkBridge {
  /**
   * @param {Object} config
   * @param {string} config.balanceFile  - Path to JSON file storing balance state
   * @param {string} config.tasksDir     - Directory containing GDPVal task JSON files
   */
  constructor({ balanceFile, tasksDir } = {}) {
    this.balanceFile = balanceFile || path.join(__dirname, 'data', 'balance.json');
    this.tasksDir = tasksDir || path.join(__dirname, 'data');
    this.completionsFile = path.join(this.tasksDir, 'completions.jsonl');
  }

  /**
   * Reads GDPVal task definitions from a JSON file.
   * @param {string} [filePath] - Defaults to data/sample-tasks.json
   * @returns {Array<Object>} Array of task objects
   */
  loadTasks(filePath) {
    const target = filePath || path.join(this.tasksDir, 'sample-tasks.json');
    if (!fs.existsSync(target)) {
      throw new Error(`Tasks file not found: ${target}`);
    }
    const raw = fs.readFileSync(target, 'utf8');
    return JSON.parse(raw);
  }

  /**
   * Creates an economic tracker for managing agent budget.
   * @param {number} initialBalance - Starting balance in USD
   * @returns {{ balance: number, deduct: Function, canAfford: Function, getStats: Function }}
   */
  createEconomicTracker(initialBalance = 1000) {
    let balance = initialBalance;
    const history = [];

    return {
      get balance() { return balance; },

      deduct(cost) {
        if (cost < 0) throw new Error('Cost must be non-negative');
        if (balance < cost) throw new Error(`Insufficient balance: need ${cost}, have ${balance}`);
        balance -= cost;
        history.push({ type: 'deduct', amount: cost, ts: Date.now() });
        return balance;
      },

      canAfford(cost) {
        return balance >= cost;
      },

      getStats() {
        const totalSpent = history
          .filter(e => e.type === 'deduct')
          .reduce((sum, e) => sum + e.amount, 0);
        return {
          initialBalance,
          currentBalance: balance,
          totalSpent,
          transactionCount: history.length,
          utilizationRate: totalSpent / initialBalance,
        };
      },
    };
  }

  /**
   * Generates a /cook mission prompt from a GDPVal task.
   * @param {Object} task - GDPVal task object
   * @returns {string} Mission prompt string
   */
  generateMission(task) {
    if (!task || !task.id) throw new Error('Invalid task: missing id');
    return [
      `/cook [ClawWork:${task.id}] ${task.role} task — ${task.description}`,
      `Sector: ${task.sector} | Budget: $${task.maxPayment} | Max iterations: ${task.iterations}`,
      'Deliver working implementation with verification. Report actual cost on completion.',
    ].join('\n');
  }

  /**
   * Records task completion to a JSONL file.
   * @param {string} taskId    - GDPVal task ID (e.g. "gdp-001")
   * @param {number} quality   - Quality score 0.0–1.0
   * @param {number} cost      - Actual cost in USD
   */
  recordCompletion(taskId, quality, cost) {
    if (!taskId) throw new Error('taskId is required');
    const entry = {
      taskId,
      quality: Math.min(1, Math.max(0, quality)),
      cost,
      completedAt: new Date().toISOString(),
    };
    fs.appendFileSync(this.completionsFile, JSON.stringify(entry) + '\n', 'utf8');
    return entry;
  }
}

module.exports = { ClawWorkBridge };
