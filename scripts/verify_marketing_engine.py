"""
Verify Marketing Engine.
Tests Content Factory and Client Magnet via Marketing MCP Server.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from antigravity.mcp_servers.marketing_server.handlers import MarketingHandler


async def verify_marketing():
    print("🧪 Verifying Marketing Engine...")
    print("=" * 50)

    handler = MarketingHandler()

    # 1. Test Content Pipeline
    print("\n📝 Testing Content Pipeline...")
    topic = "Growth Hacking for AI Agencies"
    content_result = await handler.content_pipeline(topic)

    if content_result['article_words'] > 0:
        print(f"   ✅ Article generated ({content_result['article_words']} words)")
    else:
        print("   ❌ Article generation failed")

    if len(content_result['social_posts']) == 5:
        print(f"   ✅ Social posts generated ({len(content_result['social_posts'])})")
    else:
        print(f"   ❌ Social posts mismatch: {len(content_result['social_posts'])}")

    if content_result['seo_score'] > 80:
        print(f"   ✅ SEO Score: {content_result['seo_score']}")
    else:
        print(f"   ⚠️ Low SEO Score: {content_result['seo_score']}")

    # 2. Test Lead Pipeline
    print("\n🎯 Testing Lead Pipeline...")
    lead_result = await handler.lead_pipeline()

    if lead_result['total'] > 0:
        print(f"   ✅ Leads found: {lead_result['total']}")
        print(f"   🔥 Hot leads: {lead_result['hot']}")
        print(f"   📧 Emails sent: {lead_result['emails_sent']}")
    else:
        print("   ❌ No leads processed")

    # 3. Test Idea Generation
    print("\n💡 Testing Idea Generation...")
    ideas = await handler.generate_ideas(3)
    if len(ideas) == 3:
        print(f"   ✅ Generated {len(ideas)} ideas")
        for idea in ideas:
            print(f"      - {idea}")
    else:
        print("   ❌ Idea generation failed")

    print("\n" + "=" * 50)
    print("✨ Marketing Engine Verified")

if __name__ == "__main__":
    asyncio.run(verify_marketing())
