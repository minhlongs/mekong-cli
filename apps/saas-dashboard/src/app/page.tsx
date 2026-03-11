export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">SaaS Dashboard</h1>
        <p className="text-lg text-muted-foreground">
          Analytics and subscription management platform
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <a
            href="/dashboard"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition"
          >
            Dashboard
          </a>
          <a
            href="/login"
            className="px-6 py-3 border border-input rounded-md hover:bg-accent hover:text-accent-foreground transition"
          >
            Sign In
          </a>
        </div>
      </div>
    </main>
  );
}
