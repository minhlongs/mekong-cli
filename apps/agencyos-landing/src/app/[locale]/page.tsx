import { NavbarSection } from '@/components/navbar-section';
import { HeroSection } from '@/components/hero-section';
import { FeaturesSection } from '@/components/features-section';
import { PricingSection } from '@/components/pricing-section';
import { FAQSection } from '@/components/faq-section';
import { FooterSection } from '@/components/footer-section';

export default function HomePage() {
  return (
    <>
      <NavbarSection />
      <main>
        <HeroSection />
        <FeaturesSection />
        <PricingSection />
        <FAQSection />
      </main>
      <FooterSection />
    </>
  );
}
