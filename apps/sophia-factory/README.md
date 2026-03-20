# Sophia AI Factory

AI-powered proposal generation platform for agencies.

## Quick Start

### Prerequisites

- Node.js 18+
- Supabase account (free tier works)
- OpenAI API key

### 1. Install Dependencies

```bash
npm install
```

### 2. Setup Database

```bash
# Create Supabase project at supabase.com
# Copy database/schema.sql to SQL Editor and run
# Copy database/02-seed-data.sql to seed demo data
```

See [database/01-setup-guide.md](./database/01-setup-guide.md) for detailed instructions.

### 3. Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Supabase credentials.

### 4. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Database Schema

| Table | Description |
|-------|-------------|
| `organizations` | Agencies/companies |
| `users` | User accounts with org membership |
| `brand_voices` | AI-trained brand voice models |
| `proposals` | Generated proposals |
| `templates` | Proposal templates |
| `training_documents` | Documents for brand training |

## Project Structure

```
apps/sophia-factory/
├── database/
│   ├── schema.sql           # Main database schema
│   ├── 01-setup-guide.md    # Supabase setup instructions
│   └── 02-seed-data.sql     # Demo/seed data
├── src/
│   ├── app/                 # Next.js app router pages
│   └── lib/                 # Utilities, Supabase client
├── .env.local.example       # Environment template
└── README.md
```

## Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## Tech Stack

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Backend:** Supabase (PostgreSQL, Auth, Storage)
- **AI:** OpenAI GPT-4, pgvector for embeddings
- **Deployment:** Vercel (frontend), Supabase (backend)

## License

MIT
