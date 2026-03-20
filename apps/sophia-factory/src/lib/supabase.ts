import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Organization = {
  id: string
  name: string
  slug: string
  plan: string
  proposals_remaining: number
  created_at: string
}

export type User = {
  id: string
  email: string
  org_id: string | null
  role: string
  created_at: string
}

export type BrandVoice = {
  id: string
  org_id: string
  training_docs_count: number
  model_status: string
  voice_characteristics: any
  created_at: string
}

export type Proposal = {
  id: string
  org_id: string
  title: string
  client_name: string | null
  status: string
  content: any
  created_at: string
}
