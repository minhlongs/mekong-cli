/**
 * License Management API Routes
 * RBAC: Admin-only access for license CRUD operations
 */
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { licenseQueries } from '../../db/queries/license-queries';
import { logger } from '../../utils/logger';
import { LicenseUsageAnalytics } from '../../lib/license-usage-analytics';

interface CreateLicenseBody {
  key?: string;
  tier: 'FREE' | 'PRO' | 'ENTERPRISE';
  tenantId?: string;
  expiresAt?: string;
  metadata?: Record<string, any>;
}

interface RevokeLicenseParams {
  id: string;
}

interface AnalyticsResponse {
  total: number;
  byTier: { free: number; pro: number; enterprise: number };
  byStatus: { active: number; revoked: number };
  usage: { apiCalls: number; mlFeatures: number; premiumData: number };
  recentActivity: Array<{ event: string; timestamp: string; licenseId: string }>;
}

/**
 * Generate secure license key
 * Format: raas-{tier}-{random}-{timestamp}
 */
function generateLicenseKey(tier: string): string {
  const random = Math.random().toString(36).substring(2, 10).toUpperCase();
  const timestamp = Date.now().toString(36).toUpperCase();
  const tierPrefix = tier === 'PRO' ? 'RPP' : tier === 'ENTERPRISE' ? 'REP' : 'FREE';
  return `raas-${tierPrefix.toLowerCase()}-${random}-${timestamp}`;
}

/**
 * RBAC Middleware: Check admin role
 */
async function requireAdmin(request: FastifyRequest, reply: FastifyReply) {
  const user = (request as any).user;
  if (!user || user.role !== 'admin') {
    reply.code(403).send({
      error: 'Forbidden',
      message: 'Admin access required',
    });
  }
}

export async function licenseManagementRoutes(fastify: FastifyInstance) {
  // List all licenses (admin only)
  fastify.get('/api/v1/licenses', {
    preHandler: [requireAdmin],
    handler: async (request: FastifyRequest, reply: FastifyReply) => {
      try {
        const { take, skip, status, tier } = request.query as any;
        const licenses = await licenseQueries.list({
          take: take ? parseInt(take, 10) : 100,
          skip: skip ? parseInt(skip, 10) : 0,
          status,
          tier,
        });
        reply.send({ licenses });
      } catch (error) {
        logger.error('Failed to list licenses:', error);
        reply.code(500).send({ error: 'Failed to list licenses' });
      }
    },
  });

  // Get single license (admin only)
  fastify.get('/api/v1/licenses/:id', {
    preHandler: [requireAdmin],
    handler: async (request: FastifyRequest<{ Params: { id: string } }>, reply: FastifyReply) => {
      try {
        const license = await licenseQueries.findById(request.params.id);
        if (!license) {
          return reply.code(404).send({ error: 'License not found' });
        }
        reply.send({ license });
      } catch (error) {
        logger.error('Failed to get license:', error);
        reply.code(500).send({ error: 'Failed to get license' });
      }
    },
  });

  // Create license (admin only)
  fastify.post('/api/v1/licenses', {
    preHandler: [requireAdmin],
    handler: async (
      request: FastifyRequest<{ Body: CreateLicenseBody }>,
      reply: FastifyReply
    ) => {
      try {
        const { key, tier, tenantId, expiresAt, metadata } = request.body;

        if (!tier || !['FREE', 'PRO', 'ENTERPRISE'].includes(tier)) {
          return reply.code(400).send({ error: 'Invalid tier' });
        }

        const licenseKey = key || generateLicenseKey(tier);
        const license = await licenseQueries.create({
          key: licenseKey,
          tier,
          tenantId,
          expiresAt: expiresAt ? new Date(expiresAt) : undefined,
          metadata: metadata || {},
        });

        // Audit log
        await licenseQueries.logAudit({
          licenseId: license.id,
          event: 'created',
          tier,
          ip: (request as any).ip,
        });

        logger.info(`License created: ${license.id} (${tier})`);
        reply.code(201).send({ license });
      } catch (error) {
        logger.error('Failed to create license:', error);
        reply.code(500).send({ error: 'Failed to create license' });
      }
    },
  });

  // Revoke license (admin only)
  fastify.patch('/api/v1/licenses/:id/revoke', {
    preHandler: [requireAdmin],
    handler: async (
      request: FastifyRequest<{ Params: { id: string }; Body: { reason?: string } }>,
      reply: FastifyReply
    ) => {
      try {
        const { id } = request.params;
        const { reason } = request.body;
        const user = (request as any).user;

        const license = await licenseQueries.revoke(id, user?.id || 'admin');

        // Audit log
        await licenseQueries.logAudit({
          licenseId: license.id,
          event: 'revoked',
          tier: license.tier,
          ip: (request as any).ip,
          metadata: { reason },
        });

        logger.info(`License revoked: ${id} by ${user?.id || 'admin'}`);
        reply.send({ license });
      } catch (error) {
        logger.error('Failed to revoke license:', error);
        reply.code(500).send({ error: 'Failed to revoke license' });
      }
    },
  });

  // Get audit logs (admin only)
  fastify.get('/api/v1/licenses/:id/audit', {
    preHandler: [requireAdmin],
    handler: async (request: FastifyRequest<{ Params: { id: string } }>, reply: FastifyReply) => {
      try {
        const logs = await licenseQueries.getAuditLogs(request.params.id);
        reply.send({ logs });
      } catch (error) {
        logger.error('Failed to get audit logs:', error);
        reply.code(500).send({ error: 'Failed to get audit logs' });
      }
    },
  });

  // Get license analytics (admin only)
  fastify.get('/api/v1/licenses/analytics', {
    preHandler: [requireAdmin],
    handler: async (request: FastifyRequest, reply: FastifyReply) => {
      try {
        const analytics = LicenseUsageAnalytics.getInstance();
        const allEvents = analytics.getEvents(undefined, 10);

        const [licenseStats, recentActivity] = await Promise.all([
          licenseQueries.getAnalytics(),
          licenseQueries.getRecentActivity(10),
        ]);

        const usage = {
          apiCalls: allEvents.filter((e) => e.event === 'api_call').length,
          mlFeatures: allEvents.filter((e) => e.event === 'ml_prediction').length,
          premiumData: allEvents.filter((e) => e.feature === 'premium_data').length,
        };

        const response: AnalyticsResponse = {
          total: licenseStats.total,
          byTier: licenseStats.byTier,
          byStatus: licenseStats.byStatus,
          usage,
          recentActivity: recentActivity.map((log) => ({
            event: log.event,
            timestamp: log.createdAt.toISOString(),
            licenseId: log.licenseId,
          })),
        };

        reply.send(response);
      } catch (error) {
        logger.error('Failed to get license analytics:', error);
        reply.code(500).send({ error: 'Failed to get license analytics' });
      }
    },
  });

  // Delete license (admin only)
  fastify.delete('/api/v1/licenses/:id', {
    preHandler: [requireAdmin],
    handler: async (request: FastifyRequest<{ Params: { id: string } }>, reply: FastifyReply) => {
      try {
        await licenseQueries.delete(request.params.id);
        logger.info(`License deleted: ${request.params.id}`);
        reply.code(204).send();
      } catch (error) {
        logger.error('Failed to delete license:', error);
        reply.code(500).send({ error: 'Failed to delete license' });
      }
    },
  });
}
