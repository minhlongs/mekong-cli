export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // 1. Basic Auth / Routing check
    if (request.method !== "POST") {
      return new Response("RaaS Gateway Active. Method Not Allowed.", { status: 405 });
    }

    try {
      const body = await request.json();
      const prompt = body.prompt || "";
      const targetDomain = body.domain || "";

      // 2. Security Validation (Moltworker Pattern)
      
      // Block common SQL injection and malicious prompts
      const maliciousPatterns = [
        /ignore previous instructions/i,
        /system prompt/i,
        /reveal your secret/i,
        /DROP TABLE/i,
        /DELETE FROM/i,
        /<script>/i
      ];

      for (const pattern of maliciousPatterns) {
        if (pattern.test(prompt)) {
          return new Response(JSON.stringify({ error: "Security Violation: Malicious prompt detected." }), {
            status: 403,
            headers: { "Content-Type": "application/json" }
          });
        }
      }

      // Validate target domain (must be a valid domain format)
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
      if (targetDomain && !domainRegex.test(targetDomain)) {
        return new Response(JSON.stringify({ error: "Invalid domain format." }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      // 3. Routing to OpenClaw (Inside the Tunnel)
      const openclawUrl = env.OPENCLAW_URL || "https://raas.agencyos.network";
      const openClawEndpoint = `${openclawUrl}/v1/chat/completions`;
      
      const forwardResponse = await fetch(openClawEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${env.SERVICE_TOKEN}`,
          "X-RaaS-Source": "Moltworker-Gateway"
        },
        body: JSON.stringify({
          model: env.DEFAULT_MODEL || "gemini-1.5-pro",
          messages: [{ role: "user", content: prompt }]
        })
      });

      const result = await forwardResponse.json();
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: "Internal Gateway Error", details: err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
};
