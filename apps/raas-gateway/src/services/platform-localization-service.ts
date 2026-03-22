/**
 * Platform Localization Service — i18n locale configs, translation keys, translations
 */

export interface LocaleConfig {
  id: string;
  tenant_id: string;
  default_locale: string;
  supported_locales: string; // JSON array
  timezone: string;
  date_format: string;
  number_format: string;
  currency_locale: string;
  created_at: string;
  updated_at: string;
}

export interface TranslationKey {
  id: string;
  key_path: string;
  namespace: string;
  default_value: string;
  description?: string;
  created_at: string;
}

export interface Translation {
  id: string;
  key_id: string;
  locale: string;
  value: string;
  is_verified: number;
  translated_by?: string;
  created_at: string;
  updated_at: string;
}

export async function getLocaleConfig(db: any, tenantId: string): Promise<LocaleConfig | null> {
  const row = await db.prepare(
    'SELECT * FROM locale_configs WHERE tenant_id = ?'
  ).bind(tenantId).first() as LocaleConfig | null;
  return row ?? null;
}

export async function updateLocaleConfig(
  db: any,
  tenantId: string,
  updates: Partial<Pick<LocaleConfig, 'default_locale' | 'supported_locales' | 'timezone' | 'date_format' | 'number_format' | 'currency_locale'>>
): Promise<LocaleConfig> {
  const existing = await getLocaleConfig(db, tenantId);
  if (!existing) {
    await db.prepare(`
      INSERT INTO locale_configs (tenant_id, default_locale, supported_locales, timezone, date_format, number_format, currency_locale)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).bind(
      tenantId,
      updates.default_locale ?? 'en',
      updates.supported_locales ?? '["en"]',
      updates.timezone ?? 'UTC',
      updates.date_format ?? 'YYYY-MM-DD',
      updates.number_format ?? 'en-US',
      updates.currency_locale ?? 'en-US'
    ).run();
  } else {
    const fields = Object.keys(updates).map((k) => `${k} = ?`).join(', ');
    const values = Object.values(updates);
    await db.prepare(
      `UPDATE locale_configs SET ${fields}, updated_at = datetime('now') WHERE tenant_id = ?`
    ).bind(...values, tenantId).run();
  }
  return (await getLocaleConfig(db, tenantId)) as LocaleConfig;
}

export async function getTranslations(
  db: any,
  locale: string
): Promise<Array<{ key_path: string; namespace: string; value: string }>> {
  const { results } = await db.prepare(`
    SELECT tk.key_path, tk.namespace, COALESCE(t.value, tk.default_value) AS value
    FROM translation_keys tk
    LEFT JOIN translations t ON t.key_id = tk.id AND t.locale = ?
  `).bind(locale).all() as { results: Array<{ key_path: string; namespace: string; value: string }> };
  return results ?? [];
}

export async function upsertTranslation(
  db: any,
  input: { key_id: string; locale: string; value: string; translated_by?: string; is_verified?: boolean }
): Promise<Translation> {
  const { key_id, locale, value, translated_by, is_verified = false } = input;
  await db.prepare(`
    INSERT INTO translations (key_id, locale, value, is_verified, translated_by)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(key_id, locale) DO UPDATE SET
      value = excluded.value,
      is_verified = excluded.is_verified,
      translated_by = excluded.translated_by,
      updated_at = datetime('now')
  `).bind(key_id, locale, value, is_verified ? 1 : 0, translated_by ?? null).run();
  return db.prepare(
    'SELECT * FROM translations WHERE key_id = ? AND locale = ?'
  ).bind(key_id, locale).first() as Promise<Translation>;
}

export async function listKeys(db: any, namespace?: string): Promise<TranslationKey[]> {
  const query = namespace
    ? db.prepare('SELECT * FROM translation_keys WHERE namespace = ? ORDER BY key_path').bind(namespace)
    : db.prepare('SELECT * FROM translation_keys ORDER BY namespace, key_path');
  const { results } = await query.all() as { results: TranslationKey[] };
  return results ?? [];
}

export async function createKey(
  db: any,
  input: { key_path: string; namespace?: string; default_value: string; description?: string }
): Promise<TranslationKey> {
  const { key_path, namespace = 'common', default_value, description } = input;
  await db.prepare(`
    INSERT INTO translation_keys (key_path, namespace, default_value, description)
    VALUES (?, ?, ?, ?)
  `).bind(key_path, namespace, default_value, description ?? null).run();
  return db.prepare(
    'SELECT * FROM translation_keys WHERE key_path = ? AND namespace = ?'
  ).bind(key_path, namespace).first() as Promise<TranslationKey>;
}

export async function getNamespaceTranslations(
  db: any,
  namespace: string,
  locale: string
): Promise<Record<string, string>> {
  const { results } = await db.prepare(`
    SELECT tk.key_path, COALESCE(t.value, tk.default_value) AS value
    FROM translation_keys tk
    LEFT JOIN translations t ON t.key_id = tk.id AND t.locale = ?
    WHERE tk.namespace = ?
  `).bind(locale, namespace).all() as { results: Array<{ key_path: string; value: string }> };
  return Object.fromEntries((results ?? []).map((r) => [r.key_path, r.value]));
}

export async function getSupportedLocales(db: any, tenantId: string): Promise<string[]> {
  const config = await getLocaleConfig(db, tenantId);
  if (!config) return ['en'];
  try { return JSON.parse(config.supported_locales); } catch { return ['en']; }
}

export async function getAdminOverview(db: any): Promise<{
  total_keys: number;
  total_translations: number;
  locales: string[];
  namespaces: string[];
  coverage: Record<string, number>;
}> {
  const { results: keyRows } = await db.prepare(
    'SELECT COUNT(*) as cnt FROM translation_keys'
  ).all() as { results: Array<{ cnt: number }> };
  const { results: transRows } = await db.prepare(
    'SELECT COUNT(*) as cnt FROM translations'
  ).all() as { results: Array<{ cnt: number }> };
  const { results: localeRows } = await db.prepare(
    'SELECT DISTINCT locale FROM translations ORDER BY locale'
  ).all() as { results: Array<{ locale: string }> };
  const { results: nsRows } = await db.prepare(
    'SELECT DISTINCT namespace FROM translation_keys ORDER BY namespace'
  ).all() as { results: Array<{ namespace: string }> };

  const totalKeys = keyRows?.[0]?.cnt ?? 0;
  const locales = (localeRows ?? []).map((r) => r.locale);
  const coverage: Record<string, number> = {};
  for (const loc of locales) {
    const { results: covRows } = await db.prepare(
      'SELECT COUNT(*) as cnt FROM translations WHERE locale = ?'
    ).bind(loc).all() as { results: Array<{ cnt: number }> };
    const cnt = covRows?.[0]?.cnt ?? 0;
    coverage[loc] = totalKeys > 0 ? Math.round((cnt / totalKeys) * 100) : 0;
  }
  return {
    total_keys: totalKeys,
    total_translations: transRows?.[0]?.cnt ?? 0,
    locales,
    namespaces: (nsRows ?? []).map((r) => r.namespace),
    coverage,
  };
}
