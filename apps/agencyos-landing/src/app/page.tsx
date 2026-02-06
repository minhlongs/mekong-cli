import { NavbarSection } from "@/components/navbar-section";
import { HeroSection } from "@/components/hero-section";
import { FeaturesSection } from "@/components/features-section";
import { PricingSection } from "@/components/pricing-section";
import { FooterSection } from "@/components/footer-section";

export default function Home() {
  return (
    <main className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-50 selection:bg-indigo-500/30">
      <NavbarSection />
      <HeroSection />
      <FeaturesSection />
      <PricingSection />
      <FooterSection />
    </main>
  );
}
