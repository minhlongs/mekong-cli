import { GlassCard, GlassButton, GlassContainer, AnimatedBackground } from "@/components/glass";
import { Heading } from "@/components/typography/heading";

export default function DesignTestPage() {
  return (
    <>
      <AnimatedBackground />
      <GlassContainer className="py-20">
        <div className="space-y-8">
          <Heading size="h1" gradient>
            Design System Test
          </Heading>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <GlassCard variant="default">
              <h3 className="text-xl font-bold mb-2">Default Card</h3>
              <p className="text-gray-300">Basic glassmorphism card</p>
            </GlassCard>

            <GlassCard variant="highlighted">
              <h3 className="text-xl font-bold mb-2">Highlighted Card</h3>
              <p className="text-gray-300">With glow border effect</p>
            </GlassCard>

            <GlassCard variant="interactive">
              <h3 className="text-xl font-bold mb-2">Interactive Card</h3>
              <p className="text-gray-300">Hover to see scale effect</p>
            </GlassCard>
          </div>

          <div className="flex gap-4">
            <GlassButton variant="primary" magnetic>
              Primary Button
            </GlassButton>
            <GlassButton variant="glass">Glass Button</GlassButton>
            <GlassButton variant="outline">Outline Button</GlassButton>
          </div>
        </div>
      </GlassContainer>
    </>
  );
}
