import type { 
  User, 
  Payment, 
  GiftCode, 
  ReceivedGift,
  UserProfileResponse, 
  PaymentsResponse, 
  GiftsResponse,
  ActivateGiftResponse,
  CreatePaymentResponse,
  PaymentStatusResponse
} from './types';

// Получаем initData из Telegram WebApp
function getInitData(): string {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData;
  }
  return '';
}

// Получаем данные пользователя из Telegram
export function getTelegramUser() {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user;
  }
  return null;
}

// Базовый URL API
const API_BASE = '/api';

// Обёртка для запросов с авторизацией
async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const initData = getInitData();
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP error ${response.status}`);
  }

  return response.json();
}

// API методы

/**
 * Получить профиль пользователя
 */
export async function getUserProfile(): Promise<User> {
  const response = await apiRequest<UserProfileResponse>('/profile');
  if (!response.success || !response.user) {
    throw new Error('Не удалось получить профиль');
  }
  return response.user;
}

/**
 * Получить историю платежей
 */
export async function getUserPayments(): Promise<{ payments: Payment[] }> {
  const response = await apiRequest<PaymentsResponse>('/payments');
  return { payments: response.payments || [] };
}

/**
 * Получить подарочные коды
 */
export async function getUserGifts(): Promise<{ purchasedGifts: GiftCode[]; receivedGifts: ReceivedGift[] }> {
  const response = await apiRequest<GiftsResponse>('/gifts');
  return {
    purchasedGifts: response.purchasedGifts || [],
    receivedGifts: response.receivedGifts || [],
  };
}

/**
 * Активировать подарочный код
 */
export async function activateGiftCode(code: string): Promise<ActivateGiftResponse> {
  return apiRequest<ActivateGiftResponse>('/gifts/activate', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

/**
 * Создать платёж
 */
export async function createPayment(
  months: number,
  method: 'stars' | 'sbp' | 'card',
  isGift: boolean = false
): Promise<CreatePaymentResponse> {
  return apiRequest<CreatePaymentResponse>('/payments/create', {
    method: 'POST',
    body: JSON.stringify({ months, method, isGift }),
  });
}

/**
 * Проверить статус платежа
 */
export async function checkPaymentStatus(paymentId: string): Promise<PaymentStatusResponse> {
  return apiRequest<PaymentStatusResponse>(`/payments/${paymentId}/status`);
}
