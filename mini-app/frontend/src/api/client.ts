import type {
  User,
  Payment,
  GiftCode,
  ReceivedGift,
  PaymentCreateRequest,
  PaymentCreateResponse,
  GiftActivateRequest,
  GiftActivateResponse,
} from './types';

// API Base URL - настраивается через env переменные при деплое
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/mini-app';

// Получаем initData из Telegram WebApp
function getInitData(): string {
  return window.Telegram?.WebApp?.initData || '';
}

// Базовый fetch с авторизацией
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const initData = getInitData();
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// === User API ===

export async function getUserProfile(): Promise<User> {
  return fetchApi<User>('/user/profile');
}

export async function getUserPayments(): Promise<{ payments: Payment[] }> {
  return fetchApi<{ payments: Payment[] }>('/user/payments');
}

export async function getUserGifts(): Promise<{
  purchasedGifts: GiftCode[];
  receivedGifts: ReceivedGift[];
}> {
  return fetchApi<{
    purchasedGifts: GiftCode[];
    receivedGifts: ReceivedGift[];
  }>('/user/gifts');
}

// === Gift API ===

export async function activateGiftCode(
  code: string
): Promise<GiftActivateResponse> {
  return fetchApi<GiftActivateResponse>('/gift/activate', {
    method: 'POST',
    body: JSON.stringify({ code } as GiftActivateRequest),
  });
}

// === Payment API ===

export async function createPayment(
  request: PaymentCreateRequest
): Promise<PaymentCreateResponse> {
  return fetchApi<PaymentCreateResponse>('/payment/create', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function checkPaymentStatus(
  paymentDbId: number
): Promise<{ status: string; message: string; giftCode?: string }> {
  return fetchApi<{ status: string; message: string; giftCode?: string }>(
    `/payment/check_status/${paymentDbId}`
  );
}

// === Utility ===

export function getTelegramUser() {
  return window.Telegram?.WebApp?.initDataUnsafe?.user;
}

export function isInTelegram(): boolean {
  return !!window.Telegram?.WebApp?.initData;
}

