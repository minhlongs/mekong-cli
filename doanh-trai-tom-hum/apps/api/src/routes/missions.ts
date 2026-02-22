import { Hono } from "hono";
import { PrismaClient, Prisma } from "@lobster/db";

export function createMissionRoutes(prisma: PrismaClient) {
    const router = new Hono();

    const VALID_STATUSES = ["TODO", "IN_PROGRESS", "DONE"] as const;
    const VALID_PRIORITIES = ["LOW", "MEDIUM", "HIGH"] as const;

    // GET /api/missions
    router.get("/", async (c) => {
        try {
            const missions = await prisma.mission.findMany({
                orderBy: { createdAt: "desc" },
            });
            return c.json({ success: true, data: missions });
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Unknown error";
            return c.json({ success: false, error: { message: msg, code: "INTERNAL_ERROR" } }, 500);
        }
    });

    // POST /api/missions
    router.post("/", async (c) => {
        try {
            const body = await c.req.json();
            const { title, status, priority } = body;

            if (!title || typeof title !== "string" || title.trim().length === 0) {
                return c.json(
                    { success: false, error: { message: "Title is required", code: "VALIDATION_ERROR" } },
                    400
                );
            }

            const safeStatus = VALID_STATUSES.includes(status) ? status : "TODO";
            const safePriority = VALID_PRIORITIES.includes(priority) ? priority : "MEDIUM";

            const mission = await prisma.mission.create({
                data: { title: title.trim(), status: safeStatus, priority: safePriority },
            });
            return c.json({ success: true, data: mission }, 201);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Unknown error";
            return c.json({ success: false, error: { message: msg, code: "INTERNAL_ERROR" } }, 500);
        }
    });

    // PATCH /api/missions/:id
    router.patch("/:id", async (c) => {
        try {
            const id = c.req.param("id");
            const body = await c.req.json();
            const { title, status, priority } = body;

            const data: Prisma.MissionUpdateInput = {};
            if (title !== undefined) data.title = String(title).trim();
            if (status !== undefined) {
                if (!VALID_STATUSES.includes(status)) {
                    return c.json({ success: false, error: { message: "Invalid status", code: "VALIDATION_ERROR" } }, 400);
                }
                data.status = status;
            }
            if (priority !== undefined) {
                if (!VALID_PRIORITIES.includes(priority)) {
                    return c.json({ success: false, error: { message: "Invalid priority", code: "VALIDATION_ERROR" } }, 400);
                }
                data.priority = priority;
            }

            if (Object.keys(data).length === 0) {
                return c.json(
                    { success: false, error: { message: "No fields to update", code: "VALIDATION_ERROR" } },
                    400
                );
            }

            const mission = await prisma.mission.update({ where: { id }, data });
            return c.json({ success: true, data: mission });
        } catch (e: unknown) {
            if (e && typeof e === "object" && "code" in e && (e as { code: string }).code === "P2025") {
                return c.json({ success: false, error: { message: "Mission not found", code: "NOT_FOUND" } }, 404);
            }
            const msg = e instanceof Error ? e.message : "Unknown error";
            return c.json({ success: false, error: { message: msg, code: "INTERNAL_ERROR" } }, 500);
        }
    });

    // DELETE /api/missions/:id
    router.delete("/:id", async (c) => {
        try {
            const id = c.req.param("id");
            await prisma.mission.delete({ where: { id } });
            return c.json({ success: true, data: { id } });
        } catch (e: unknown) {
            if (e && typeof e === "object" && "code" in e && (e as { code: string }).code === "P2025") {
                return c.json({ success: false, error: { message: "Mission not found", code: "NOT_FOUND" } }, 404);
            }
            const msg = e instanceof Error ? e.message : "Unknown error";
            return c.json({ success: false, error: { message: msg, code: "INTERNAL_ERROR" } }, 500);
        }
    });

    return router;
}
