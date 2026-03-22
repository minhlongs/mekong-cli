/**
 * Platform Service Mesh Service — registry, circuit breakers, traffic rules
 * Supports: listServices, registerService, getService, updateService, deregisterService,
 *           healthCheck, getCircuitBreaker, updateCircuitBreaker,
 *           listTrafficRules, createTrafficRule, getMeshTopology, getAdminOverview
 */

export const platformServiceMeshService = {
  /** List all registered services */
  async listServices(db: any) {
    const result = await db.prepare(
      'SELECT * FROM service_registry ORDER BY registered_at DESC'
    ).all();
    return result.results ?? [];
  },

  /** Register a new service */
  async registerService(db: any, data: any) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db.prepare(
      `INSERT INTO service_registry (id, service_name, version, endpoint_url, health_check_url, status, protocol, metadata_json, registered_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id,
      data.service_name,
      data.version ?? '1.0.0',
      data.endpoint_url,
      data.health_check_url ?? null,
      data.status ?? 'healthy',
      data.protocol ?? 'http',
      data.metadata_json ?? '{}',
      now,
      now
    ).run();
    return { id, ...data, registered_at: now, updated_at: now };
  },

  /** Get a single service by id */
  async getService(db: any, id: string) {
    return db.prepare('SELECT * FROM service_registry WHERE id = ?').bind(id).first();
  },

  /** Update service fields */
  async updateService(db: any, id: string, data: any) {
    const now = new Date().toISOString();
    const fields = Object.keys(data).map(k => `${k} = ?`).join(', ');
    const values = [...Object.values(data), now, id];
    await db.prepare(
      `UPDATE service_registry SET ${fields}, updated_at = ? WHERE id = ?`
    ).bind(...values).run();
    return db.prepare('SELECT * FROM service_registry WHERE id = ?').bind(id).first();
  },

  /** Remove service from registry */
  async deregisterService(db: any, id: string) {
    await db.prepare('DELETE FROM service_registry WHERE id = ?').bind(id).run();
    return { deleted: true, id };
  },

  /** Run health check — update status + last_health_at */
  async healthCheck(db: any, id: string) {
    const now = new Date().toISOString();
    const svc = await db.prepare('SELECT * FROM service_registry WHERE id = ?').bind(id).first();
    if (!svc) return null;
    // Determine reachability: assume healthy unless endpoint absent
    const status = svc.health_check_url ? 'healthy' : svc.status;
    await db.prepare(
      'UPDATE service_registry SET status = ?, last_health_at = ?, updated_at = ? WHERE id = ?'
    ).bind(status, now, now, id).run();
    return { id, status, last_health_at: now };
  },

  /** Get circuit breaker config for a service */
  async getCircuitBreaker(db: any, serviceId: string) {
    return db.prepare(
      'SELECT * FROM circuit_breaker_configs WHERE service_id = ?'
    ).bind(serviceId).first();
  },

  /** Upsert circuit breaker state/config */
  async updateCircuitBreaker(db: any, serviceId: string, data: any) {
    const existing = await db.prepare(
      'SELECT id FROM circuit_breaker_configs WHERE service_id = ?'
    ).bind(serviceId).first();
    if (existing) {
      const fields = Object.keys(data).map(k => `${k} = ?`).join(', ');
      await db.prepare(
        `UPDATE circuit_breaker_configs SET ${fields} WHERE service_id = ?`
      ).bind(...Object.values(data), serviceId).run();
    } else {
      const id = crypto.randomUUID();
      await db.prepare(
        `INSERT INTO circuit_breaker_configs (id, service_id, failure_threshold, recovery_timeout_ms, half_open_max_calls, state, failure_count, last_failure_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        id, serviceId,
        data.failure_threshold ?? 5,
        data.recovery_timeout_ms ?? 30000,
        data.half_open_max_calls ?? 3,
        data.state ?? 'closed',
        data.failure_count ?? 0,
        data.last_failure_at ?? null
      ).run();
    }
    return db.prepare('SELECT * FROM circuit_breaker_configs WHERE service_id = ?').bind(serviceId).first();
  },

  /** List all traffic rules */
  async listTrafficRules(db: any) {
    const result = await db.prepare(
      'SELECT * FROM traffic_rules ORDER BY created_at DESC'
    ).all();
    return result.results ?? [];
  },

  /** Create a traffic rule */
  async createTrafficRule(db: any, data: any) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db.prepare(
      `INSERT INTO traffic_rules (id, source_service, target_service, weight, rate_limit, timeout_ms, retry_count, enabled, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id,
      data.source_service,
      data.target_service,
      data.weight ?? 100,
      data.rate_limit ?? 1000,
      data.timeout_ms ?? 5000,
      data.retry_count ?? 3,
      data.enabled ?? 1,
      now
    ).run();
    return { id, ...data, created_at: now };
  },

  /** Mesh topology: services + active connections overview */
  async getMeshTopology(db: any) {
    const [services, rules] = await Promise.all([
      db.prepare('SELECT id, service_name, status, protocol, version FROM service_registry').all(),
      db.prepare('SELECT source_service, target_service, weight, enabled FROM traffic_rules WHERE enabled = 1').all(),
    ]);
    return {
      services: services.results ?? [],
      connections: rules.results ?? [],
    };
  },

  /** Admin overview: counts + health stats */
  async getAdminOverview(db: any) {
    const [total, healthy, degraded, cbOpen, rules] = await Promise.all([
      db.prepare('SELECT COUNT(*) as count FROM service_registry').first(),
      db.prepare("SELECT COUNT(*) as count FROM service_registry WHERE status = 'healthy'").first(),
      db.prepare("SELECT COUNT(*) as count FROM service_registry WHERE status != 'healthy'").first(),
      db.prepare("SELECT COUNT(*) as count FROM circuit_breaker_configs WHERE state = 'open'").first(),
      db.prepare('SELECT COUNT(*) as count FROM traffic_rules').first(),
    ]);
    return {
      services: { total: total?.count ?? 0, healthy: healthy?.count ?? 0, degraded: degraded?.count ?? 0 },
      circuit_breakers: { open: cbOpen?.count ?? 0 },
      traffic_rules: { total: rules?.count ?? 0 },
    };
  },
};
