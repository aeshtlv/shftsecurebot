// API Response types

export interface User {
  telegramId: number;
  username?: string;
  firstName: string;
  lastName?: string;
  languageCode?: string;
  isPremium?: boolean;
}

export interface Subscription {
  status: 'active' | 'expired' | 'disabled' | 'limited';
  plan: string;
  duration: string;
  startDate: string;
  endDate: string;
  trafficUsed: number;
  trafficTotal: number;
  autoRenew: boolean;
  subscriptionUrl?: string;
  shortUuid?: string;
}

export interface LoyaltyProfile {
  level: 'bronze' | 'silver' | 'gold' | 'platinum';
  points: number;
  totalSpent: number;
  discount: number;
  nextLevel?: {
    name: string;
    pointsRequired: number;
    pointsToGo: number;
    progress: number;
  };
}

export interface Referral {
  count: number;
  earned: number;
  referralLink: string;
}

export interface Plan {
  id: string;
  period: string;
  months: number;
  basePrice: number;
  discountedPrice: number;
  traffic: string;
  trafficGb: number;
  pricePerMonth: number;
  savings?: number;
  badge?: string;
}

export interface GiftCode {
  id: string;
  code: string;
  status: 'active' | 'used' | 'expired';
  period: string;
  months: number;
  createdAt: string;
  activatedAt?: string;
  recipientUsername?: string;
}

export interface ReceivedGift {
  id: string;
  code: string;
  period: string;
  fromUsername: string;
  activatedAt: string;
}

export interface Transaction {
  id: string;
  date: string;
  amount: number;
  currency: string;
  type: 'subscription' | 'gift';
  period: string;
  method: 'stars' | 'sbp' | 'card';
  status: 'completed' | 'pending' | 'failed';
}

export interface DashboardData {
  user: User;
  subscription?: Subscription;
  loyalty: LoyaltyProfile;
  referral: Referral;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

