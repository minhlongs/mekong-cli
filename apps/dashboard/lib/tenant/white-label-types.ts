/**
 * White-Label Configuration & Domain Verification Types
 */

export interface WhiteLabelConfig {
  // Basic Branding
  brandName: string
  tagline?: string
  logoUrl?: string
  faviconUrl?: string

  // Colors
  primaryColor: string
  secondaryColor: string
  accentColor: string
  backgroundColor: string
  textColor: string

  // Typography
  fontFamily?: string
  headingFont?: string

  // Custom Domain
  customDomain?: string
  domainVerified: boolean
  sslEnabled: boolean

  // Custom CSS
  customCss?: string

  // Footer
  showPoweredBy: boolean
  poweredByText?: string

  // Login Page
  loginBackgroundUrl?: string
  loginMessage?: string

  // Email Templates
  emailFromName?: string
  emailReplyTo?: string
}

export interface DomainVerification {
  domain: string
  txtRecord: string
  cnameRecord: string
  verified: boolean
  verifiedAt?: Date
}

export interface WhiteLabelRow {
  brand_name?: string
  tagline?: string
  logo_url?: string
  favicon_url?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  background_color?: string
  text_color?: string
  font_family?: string
  heading_font?: string
  custom_domain?: string
  domain_verified?: boolean
  ssl_enabled?: boolean
  custom_css?: string
  show_powered_by?: boolean
  powered_by_text?: string
  login_background_url?: string
  login_message?: string
  email_from_name?: string
  email_reply_to?: string
}
