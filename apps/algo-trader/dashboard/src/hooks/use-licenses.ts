/**
 * License data fetching hook with loading and error states.
 * Uses useState pattern consistent with project conventions.
 */
import { useState, useCallback, useEffect } from 'react';
import { useApiClient } from './use-api-client';

export interface License {
  id: string;
  name: string;
  key: string;
  tier: 'FREE' | 'PRO' | 'ENTERPRISE';
  status: 'active' | 'expired' | 'revoked';
  createdAt: string;
  expiresAt?: string;
  usageCount: number;
  maxUsage?: number;
  userId?: string;
  updatedAt?: string;
}

export interface LicenseFilters {
  status?: 'all' | 'active' | 'expired' | 'revoked';
  tier?: 'all' | 'FREE' | 'PRO' | 'ENTERPRISE';
}

export function useLicenses() {
  const { fetchApi } = useApiClient();
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLicenses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<License[]>('/licenses');
      if (data) {
        setLicenses(data);
      } else {
        setError('Failed to load licenses');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [fetchApi]);

  const revokeLicense = useCallback(async (licenseId: string) => {
    const result = await fetchApi<License>(`/licenses/${licenseId}/revoke`, {
      method: 'POST',
    });
    if (result) {
      setLicenses((prev) => prev.map((l) => (l.id === licenseId ? { ...l, status: 'revoked' as const } : l)));
    }
    return !!result;
  }, [fetchApi]);

  const deleteLicense = useCallback(async (licenseId: string) => {
    const success = await fetchApi(`/licenses/${licenseId}`, {
      method: 'DELETE',
    });
    if (success) {
      setLicenses((prev) => prev.filter((l) => l.id !== licenseId));
    }
    return !!success;
  }, [fetchApi]);

  useEffect(() => {
    loadLicenses();
  }, [loadLicenses]);

  return {
    licenses,
    loading,
    error,
    reload: loadLicenses,
    revokeLicense,
    deleteLicense,
  };
}
