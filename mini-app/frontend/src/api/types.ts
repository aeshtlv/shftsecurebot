// Типы для API Mini App

export interface User {
  telegramId: number;
  username?: string;
  loyalty: {
    points: number;
    status: 'bronze' | 'silver' | 'gold' | 'platinum';
    totalSpent: number;
    joinedAt: string;
  };
  subscription: Subscription | null;
  referralLink: string;
  totalGiftsPurchased: number;
  totalGiftsReceived: number;
}

export interface Subscription {
  status: 'active' | 'expired' | 'disabled';
  expireAt: string;
  trafficUsed: number;
  trafficLimit: number;
  subscriptionUrl: string;
  autoRenewal: boolean;
}

export interface Payment {
  id: number;
  date: string;
  amount: number;
  currency: string;
  type: 'subscription' | 'gift';
  periodDays: number;
  method: 'stars' | 'sbp' | 'card';
  status: 'pending' | 'completed' | 'failed';
}

export interface GiftCode {
  id: number;
  code: string;
  status: 'active' | 'used';
  periodDays: number;
  createdAt: string;
  activatedAt?: string;
}

export interface ReceivedGift {
  id: number;
  code: string;
  periodDays: number;
  fromUserId: number;
  activatedAt: string;
}

export interface PaymentCreateRequest {
  months: number;
  method: 'stars' | 'sbp' | 'card';
  isGift: boolean;
}

export interface PaymentCreateResponse {
  success: boolean;
  paymentUrl?: string;
  method: string;
  paymentDbId?: number;
  error?: string;
}

export interface GiftActivateRequest {
  code: string;
}

export interface GiftActivateResponse {
  success: boolean;
  expireDate?: string;
  error?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

