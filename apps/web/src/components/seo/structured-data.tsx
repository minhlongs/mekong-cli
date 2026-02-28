// SEO structured data components (JSON-LD)
interface OrganizationLDProps {
  name: string;
  logo: string;
  url: string;
  sameAs?: string[];
}

export function OrganizationLD({ name, logo, url, sameAs }: OrganizationLDProps) {
  const data = { "@context": "https://schema.org", "@type": "Organization", name, logo, url, sameAs };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}

interface ProductLDProps {
  name: string;
  image: string;
  price: string;
  currency: string;
  availability: string;
}

export function ProductLD({ name, image, price, currency, availability }: ProductLDProps) {
  const data = {
    "@context": "https://schema.org", "@type": "Product", name, image,
    offers: { "@type": "Offer", price, priceCurrency: currency, availability: `https://schema.org/${availability}` },
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}
