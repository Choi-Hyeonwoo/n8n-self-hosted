#!/usr/bin/env node
/**
 * Brain Sync - Claude Code ↔ RON Strategy Parser
 *
 * 여러 Claude Code 인스턴스 간 컨텍스트/전략 동기화
 *
 * Usage:
 *   node brain_sync.js push "task description" --priority high
 *   node brain_sync.js pull
 *   node brain_sync.js status
 *   node brain_sync.js watch
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 설정
const CONFIG = {
    SYNC_DIR: process.env.BRAIN_SYNC_DIR || '/home/user/n8n-self-hosted/openclaw/.brain',
    STRATEGY_FILE: 'strategies.json',
    CONTEXT_FILE: 'shared_context.json',
    LOCK_FILE: '.brain.lock',
    MAX_STRATEGIES: 50,
    LOCK_TIMEOUT_MS: 30000,
};

// 유틸리티 함수
function ensureDir(dir) {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
}

function log(msg, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
        info: '📋',
        success: '✅',
        warn: '⚠️',
        error: '❌',
        sync: '🔄',
    }[level] || '•';
    console.log(`[${timestamp}] ${prefix} ${msg}`);
}

function generateId() {
    return crypto.randomBytes(4).toString('hex');
}

// 파일 잠금 (동시 접근 방지)
class FileLock {
    constructor(lockPath) {
        this.lockPath = lockPath;
        this.locked = false;
    }

    async acquire(timeoutMs = CONFIG.LOCK_TIMEOUT_MS) {
        const startTime = Date.now();
        const lockInfo = {
            pid: process.pid,
            timestamp: new Date().toISOString(),
            hostname: require('os').hostname(),
        };

        while (Date.now() - startTime < timeoutMs) {
            try {
                // Check if lock exists and is stale
                if (fs.existsSync(this.lockPath)) {
                    const existingLock = JSON.parse(fs.readFileSync(this.lockPath, 'utf8'));
                    const lockAge = Date.now() - new Date(existingLock.timestamp).getTime();

                    if (lockAge > CONFIG.LOCK_TIMEOUT_MS) {
                        // Stale lock, remove it
                        fs.unlinkSync(this.lockPath);
                    } else {
                        // Wait and retry
                        await new Promise(r => setTimeout(r, 100));
                        continue;
                    }
                }

                // Acquire lock
                fs.writeFileSync(this.lockPath, JSON.stringify(lockInfo), { flag: 'wx' });
                this.locked = true;
                return true;
            } catch (e) {
                if (e.code === 'EEXIST') {
                    // Another process acquired lock
                    await new Promise(r => setTimeout(r, 100));
                } else {
                    throw e;
                }
            }
        }

        throw new Error('Failed to acquire lock: timeout');
    }

    release() {
        if (this.locked && fs.existsSync(this.lockPath)) {
            fs.unlinkSync(this.lockPath);
            this.locked = false;
        }
    }
}

// 전략 관리자
class StrategyManager {
    constructor() {
        this.syncDir = CONFIG.SYNC_DIR;
        this.strategyPath = path.join(this.syncDir, CONFIG.STRATEGY_FILE);
        this.contextPath = path.join(this.syncDir, CONFIG.CONTEXT_FILE);
        this.lock = new FileLock(path.join(this.syncDir, CONFIG.LOCK_FILE));

        ensureDir(this.syncDir);
        this.initFiles();
    }

    initFiles() {
        if (!fs.existsSync(this.strategyPath)) {
            fs.writeFileSync(this.strategyPath, JSON.stringify({
                strategies: [],
                lastUpdate: new Date().toISOString(),
            }, null, 2));
        }

        if (!fs.existsSync(this.contextPath)) {
            fs.writeFileSync(this.contextPath, JSON.stringify({
                currentTask: null,
                sharedMemory: {},
                agents: {},
                lastSync: new Date().toISOString(),
            }, null, 2));
        }
    }

    loadStrategies() {
        try {
            return JSON.parse(fs.readFileSync(this.strategyPath, 'utf8'));
        } catch (e) {
            return { strategies: [], lastUpdate: new Date().toISOString() };
        }
    }

    saveStrategies(data) {
        data.lastUpdate = new Date().toISOString();
        fs.writeFileSync(this.strategyPath, JSON.stringify(data, null, 2));
    }

    loadContext() {
        try {
            return JSON.parse(fs.readFileSync(this.contextPath, 'utf8'));
        } catch (e) {
            return { currentTask: null, sharedMemory: {}, agents: {}, lastSync: new Date().toISOString() };
        }
    }

    saveContext(data) {
        data.lastSync = new Date().toISOString();
        fs.writeFileSync(this.contextPath, JSON.stringify(data, null, 2));
    }

    // 전략 추가
    async push(task, options = {}) {
        await this.lock.acquire();
        try {
            const data = this.loadStrategies();

            const strategy = {
                id: generateId(),
                task,
                priority: options.priority || 'normal',
                status: 'pending',
                source: options.source || 'claude-code',
                createdAt: new Date().toISOString(),
                metadata: options.metadata || {},
            };

            data.strategies.unshift(strategy);

            // 최대 개수 유지
            if (data.strategies.length > CONFIG.MAX_STRATEGIES) {
                data.strategies = data.strategies.slice(0, CONFIG.MAX_STRATEGIES);
            }

            this.saveStrategies(data);
            log(`Strategy pushed: [${strategy.id}] ${task}`, 'success');

            return strategy;
        } finally {
            this.lock.release();
        }
    }

    // 전략 가져오기 (pending 상태 우선)
    async pull(options = {}) {
        await this.lock.acquire();
        try {
            const data = this.loadStrategies();

            let strategies = data.strategies;

            // 필터링
            if (options.status) {
                strategies = strategies.filter(s => s.status === options.status);
            }
            if (options.priority) {
                strategies = strategies.filter(s => s.priority === options.priority);
            }

            // 우선순위 정렬
            const priorityOrder = { high: 0, normal: 1, low: 2 };
            strategies.sort((a, b) => {
                if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
                    return priorityOrder[a.priority] - priorityOrder[b.priority];
                }
                return new Date(a.createdAt) - new Date(b.createdAt);
            });

            if (options.limit) {
                strategies = strategies.slice(0, options.limit);
            }

            return strategies;
        } finally {
            this.lock.release();
        }
    }

    // 전략 상태 업데이트
    async update(id, updates) {
        await this.lock.acquire();
        try {
            const data = this.loadStrategies();
            const strategy = data.strategies.find(s => s.id === id);

            if (!strategy) {
                throw new Error(`Strategy not found: ${id}`);
            }

            Object.assign(strategy, updates, { updatedAt: new Date().toISOString() });
            this.saveStrategies(data);

            log(`Strategy updated: [${id}] → ${updates.status || 'modified'}`, 'sync');
            return strategy;
        } finally {
            this.lock.release();
        }
    }

    // 컨텍스트 공유
    async shareContext(key, value) {
        await this.lock.acquire();
        try {
            const context = this.loadContext();
            context.sharedMemory[key] = {
                value,
                updatedAt: new Date().toISOString(),
                source: process.env.AGENT_ID || 'unknown',
            };
            this.saveContext(context);
            log(`Context shared: ${key}`, 'sync');
        } finally {
            this.lock.release();
        }
    }

    // 컨텍스트 읽기
    async getContext(key) {
        const context = this.loadContext();
        return key ? context.sharedMemory[key] : context.sharedMemory;
    }

    // 에이전트 등록/하트비트
    async registerAgent(agentId, info = {}) {
        await this.lock.acquire();
        try {
            const context = this.loadContext();
            context.agents[agentId] = {
                ...info,
                lastSeen: new Date().toISOString(),
                status: 'active',
            };
            this.saveContext(context);
            log(`Agent registered: ${agentId}`, 'success');
        } finally {
            this.lock.release();
        }
    }

    // 활성 에이전트 목록
    async getActiveAgents(timeoutMs = 60000) {
        const context = this.loadContext();
        const now = Date.now();

        return Object.entries(context.agents)
            .filter(([_, agent]) => {
                const lastSeen = new Date(agent.lastSeen).getTime();
                return now - lastSeen < timeoutMs;
            })
            .map(([id, agent]) => ({ id, ...agent }));
    }

    // 상태 요약
    async status() {
        const strategies = this.loadStrategies();
        const context = this.loadContext();
        const activeAgents = await this.getActiveAgents();

        const statusCount = strategies.strategies.reduce((acc, s) => {
            acc[s.status] = (acc[s.status] || 0) + 1;
            return acc;
        }, {});

        return {
            strategies: {
                total: strategies.strategies.length,
                byStatus: statusCount,
                lastUpdate: strategies.lastUpdate,
            },
            context: {
                sharedKeys: Object.keys(context.sharedMemory).length,
                currentTask: context.currentTask,
                lastSync: context.lastSync,
            },
            agents: {
                active: activeAgents.length,
                list: activeAgents,
            },
        };
    }
}

// Watch 모드 (파일 변경 감시)
async function watchMode(manager) {
    log('Watch mode started. Monitoring for changes...', 'info');

    const agentId = `watcher-${generateId()}`;
    await manager.registerAgent(agentId, { type: 'watcher' });

    // 주기적 하트비트
    setInterval(async () => {
        await manager.registerAgent(agentId, { type: 'watcher' });
    }, 30000);

    // 파일 감시
    fs.watch(CONFIG.SYNC_DIR, async (eventType, filename) => {
        if (filename && filename.endsWith('.json')) {
            log(`File changed: ${filename}`, 'sync');

            if (filename === CONFIG.STRATEGY_FILE) {
                const pending = await manager.pull({ status: 'pending', limit: 5 });
                if (pending.length > 0) {
                    log(`Pending strategies: ${pending.length}`, 'info');
                    pending.forEach(s => {
                        log(`  [${s.priority}] ${s.task}`, 'info');
                    });
                }
            }
        }
    });

    // 종료 시그널 처리
    process.on('SIGINT', () => {
        log('Watch mode stopped.', 'info');
        process.exit(0);
    });

    // 무한 대기
    await new Promise(() => {});
}

// CLI 메인
async function main() {
    const args = process.argv.slice(2);
    const command = args[0] || 'status';

    const manager = new StrategyManager();

    try {
        switch (command) {
            case 'push': {
                const task = args[1];
                if (!task) {
                    console.error('Usage: brain_sync.js push "task description" [--priority high|normal|low]');
                    process.exit(1);
                }

                const priorityIdx = args.indexOf('--priority');
                const priority = priorityIdx > -1 ? args[priorityIdx + 1] : 'normal';

                const sourceIdx = args.indexOf('--source');
                const source = sourceIdx > -1 ? args[sourceIdx + 1] : 'claude-code';

                await manager.push(task, { priority, source });
                break;
            }

            case 'pull': {
                const statusIdx = args.indexOf('--status');
                const status = statusIdx > -1 ? args[statusIdx + 1] : 'pending';

                const limitIdx = args.indexOf('--limit');
                const limit = limitIdx > -1 ? parseInt(args[limitIdx + 1]) : 10;

                const strategies = await manager.pull({ status, limit });

                if (strategies.length === 0) {
                    log('No strategies found', 'info');
                } else {
                    console.log(JSON.stringify(strategies, null, 2));
                }
                break;
            }

            case 'complete':
            case 'done': {
                const id = args[1];
                if (!id) {
                    console.error('Usage: brain_sync.js complete <strategy-id>');
                    process.exit(1);
                }
                await manager.update(id, { status: 'completed' });
                break;
            }

            case 'fail': {
                const id = args[1];
                const reason = args[2] || 'Unknown error';
                if (!id) {
                    console.error('Usage: brain_sync.js fail <strategy-id> [reason]');
                    process.exit(1);
                }
                await manager.update(id, { status: 'failed', error: reason });
                break;
            }

            case 'share': {
                const key = args[1];
                const value = args.slice(2).join(' ');
                if (!key || !value) {
                    console.error('Usage: brain_sync.js share <key> <value>');
                    process.exit(1);
                }
                await manager.shareContext(key, value);
                break;
            }

            case 'get': {
                const key = args[1];
                const context = await manager.getContext(key);
                console.log(JSON.stringify(context, null, 2));
                break;
            }

            case 'agents': {
                const agents = await manager.getActiveAgents();
                if (agents.length === 0) {
                    log('No active agents', 'info');
                } else {
                    console.log(JSON.stringify(agents, null, 2));
                }
                break;
            }

            case 'register': {
                const agentId = args[1] || `agent-${generateId()}`;
                const type = args[2] || 'claude-code';
                await manager.registerAgent(agentId, { type });
                console.log(agentId);
                break;
            }

            case 'watch':
                await watchMode(manager);
                break;

            case 'status':
            default: {
                const status = await manager.status();
                console.log('\n╔════════════════════════════════════════╗');
                console.log('║       Brain Sync Status                ║');
                console.log('╠════════════════════════════════════════╣');
                console.log(`║ Strategies: ${status.strategies.total} total`);
                Object.entries(status.strategies.byStatus).forEach(([k, v]) => {
                    console.log(`║   - ${k}: ${v}`);
                });
                console.log('╠────────────────────────────────────────╣');
                console.log(`║ Shared Context: ${status.context.sharedKeys} keys`);
                console.log(`║ Active Agents: ${status.agents.active}`);
                status.agents.list.forEach(a => {
                    console.log(`║   - ${a.id} (${a.type || 'unknown'})`);
                });
                console.log('╚════════════════════════════════════════╝\n');
                break;
            }
        }
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        process.exit(1);
    }
}

// Export for programmatic use
module.exports = { StrategyManager, CONFIG };

// CLI 실행
if (require.main === module) {
    main().catch(e => {
        console.error(e);
        process.exit(1);
    });
}
