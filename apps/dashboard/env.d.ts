declare module 'vinext' {
  import type { PluginOption } from 'vite'
  export default function vinext(options?: Record<string, unknown>): PluginOption
}

declare module '@cloudflare/vite-plugin' {
  import type { PluginOption } from 'vite'
  export function cloudflare(options?: Record<string, unknown>): PluginOption
}
