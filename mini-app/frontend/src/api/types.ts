// Подписка пользователя
export interface Subscription {
  status: 'active' | 'expired' | 'none';
  expireAt: string | null;
  trafficUsed: number;
  trafficLimit: number;
  subscriptionUrl: string | null;
  autoRenewal: boolean;
}

// Данные лояльности
export interface Loyalty {
  points: number;
  status: 'bronze' | 'silver' | 'gold' | 'platinum';
  discount: number;
  totalSpent: number;
}

// Профиль пользователя
export interface User {
  telegramId: number;
  username: string | null;
  subscription: Subscription | null;
  loyalty: Loyalty;
  referralLink: string;
  totalGiftsPurchased: number;
  totalGiftsReceived: number;
}

// Платёж
export interface Payment {
  id: string;
  type: 'subscription' | 'gift';
  amount: number;
  currency: string;
  method: 'stars' | 'sbp' | 'card';
  status: 'completed' | 'pending' | 'failed';
  periodDays: number;
  date: string;
}

// Подарочный код
export interface GiftCode {
  id: string;
  code: string;
  status: 'active' | 'used' | 'expired';
  periodDays: number;
  createdAt: string;
  activatedAt: string | null;
}

// Полученный подарок
export interface ReceivedGift {
  id: string;
  code: string;
  periodDays: number;
  activatedAt: string;
}

// Ответы API
export interface UserProfileResponse {
  success: boolean;
  user: User;
}

export interface PaymentsResponse {
  success: boolean;
  payments: Payment[];
}

export interface GiftsResponse {
  success: boolean;
  purchasedGifts: GiftCode[];
  receivedGifts: ReceivedGift[];
}

export interface ActivateGiftResponse {
  success: boolean;
  error?: string;
  expireDate?: string;
}

export interface CreatePaymentResponse {
  success: boolean;
  paymentUrl?: string;
  invoiceLink?: string;
  error?: string;
}

export interface PaymentStatusResponse {
  success: boolean;
  status: 'pending' | 'completed' | 'failed';
}
