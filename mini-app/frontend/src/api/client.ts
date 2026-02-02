import type { 
  ApiResponse, 
  DashboardData, 
  LoyaltyProfile, 
  Plan, 
  GiftCode, 
  ReceivedGift, 
  Transaction 
} from './types';

// API base URL - will be configured for production
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/webapp';

// Get Telegram initData for authentication
function getInitData(): string {
  return window.Telegram?.WebApp?.initData || '';
}

// Generic fetch wrapper with authentication
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': getInitData(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

// API Methods

export async function getDashboard(): Promise<ApiResponse<DashboardData>> {
  return fetchApi<DashboardData>('/dashboard');
}

export async function getLoyalty(): Promise<ApiResponse<LoyaltyProfile>> {
  return fetchApi<LoyaltyProfile>('/loyalty');
}

export async function getPlans(): Promise<ApiResponse<Plan[]>> {
  return fetchApi<Plan[]>('/plans');
}

export async function getGifts(): Promise<ApiResponse<{ 
  purchased: GiftCode[]; 
  received: ReceivedGift[] 
}>> {
  return fetchApi('/gifts');
}

export async function activateGift(code: string): Promise<ApiResponse<{ success: boolean }>> {
  return fetchApi('/gifts/activate', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

export async function getPayments(): Promise<ApiResponse<Transaction[]>> {
  return fetchApi<Transaction[]>('/payments');
}

export async function createPayment(params: {
  planId: string;
  method: 'stars' | 'sbp' | 'card';
  isGift: boolean;
}): Promise<ApiResponse<{ paymentUrl?: string; invoiceUrl?: string }>> {
  return fetchApi('/payment/create', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getSubscriptionQr(): Promise<ApiResponse<{ qrCode: string }>> {
  return fetchApi('/subscription/qr');
}

export async function getSubscriptionConfig(): Promise<ApiResponse<{ config: string }>> {
  return fetchApi('/subscription/config');
}

// Telegram WebApp helpers
export function hapticFeedback(type: 'light' | 'medium' | 'heavy' = 'light') {
  window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(type);
}

export function hapticNotification(type: 'success' | 'error' | 'warning') {
  window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
}

export function showAlert(message: string): Promise<void> {
  return new Promise((resolve) => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showAlert(message, resolve);
    } else {
      alert(message);
      resolve();
    }
  });
}

export function showConfirm(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showConfirm(message, resolve);
    } else {
      resolve(confirm(message));
    }
  });
}

export function openInvoice(url: string): Promise<string> {
  return new Promise((resolve) => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openInvoice(url, resolve);
    } else {
      window.open(url, '_blank');
      resolve('opened');
    }
  });
}

export function copyToClipboard(text: string): Promise<boolean> {
  return navigator.clipboard.writeText(text)
    .then(() => {
      hapticNotification('success');
      return true;
    })
    .catch(() => false);
}

