import ReportSlugPage from "./report-slug-page";

export function generateStaticParams() {
  // Return at least one path to satisfy next export requirements for catch-all dynamic routes
  return [
    { slug: ["engineering", "stub", "placeholder"] }
  ];
}

export default function Page() {
  return <ReportSlugPage />;
}
