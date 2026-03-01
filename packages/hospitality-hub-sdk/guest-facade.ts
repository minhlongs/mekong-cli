/**
 * @agencyos/hospitality-hub-sdk — Guest Experience & Loyalty Facade
 *
 * Provides unified interface for guest profile management, preferences tracking,
 * loyalty program tiers, and stay history.
 */

export interface GuestProfile {
  id: string;
  name: string;
  email: string;
  loyaltyTier: 'bronze' | 'silver' | 'gold' | 'platinum';
  preferences: GuestPreferences;
  stayHistory: StayRecord[];
  loyaltyPoints: number;
}

export interface GuestPreferences {
  roomType?: string;
  floorPreference?: 'high' | 'low' | 'no-preference';
  pillowType?: 'soft' | 'firm';
  dietaryRestrictions?: string[];
  amenities?: string[];
}

export interface StayRecord {
  reservationId: string;
  hotelId: string;
  checkIn: string;
  checkOut: string;
  roomType: string;
  totalSpent: number;
  rating?: number;
}

export interface LoyaltyReward {
  id: string;
  name: string;
  pointsCost: number;
  type: 'upgrade' | 'discount' | 'amenity' | 'free-night';
}

export function createGuestManager() {
  return {
    getProfile: async (_guestId: string) => ({} as GuestProfile),
    updatePreferences: async (_guestId: string, _prefs: Partial<GuestPreferences>) => ({ success: true }),
    getStayHistory: async (_guestId: string) => [] as StayRecord[],
  };
}

export function createLoyaltyProgram() {
  return {
    getPoints: async (_guestId: string) => ({ points: 0, tier: 'bronze' as GuestProfile['loyaltyTier'] }),
    redeemReward: async (_guestId: string, _rewardId: string) => ({ success: true, pointsUsed: 0 }),
    listRewards: async (_tier: GuestProfile['loyaltyTier']) => [] as LoyaltyReward[],
  };
}
