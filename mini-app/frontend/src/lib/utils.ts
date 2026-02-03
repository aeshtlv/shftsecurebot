import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Утилита для объединения классов Tailwind
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Хаптическая обратная связь Telegram
 */
export function haptic(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning' = 'light') {
  try {
    const webApp = window.Telegram?.WebApp;
    if (!webApp?.HapticFeedback) return;

    if (type === 'success' || type === 'error' || type === 'warning') {
      webApp.HapticFeedback.notificationOccurred(type);
    } else {
      webApp.HapticFeedback.impactOccurred(type);
    }
  } catch {
    // Haptic не доступен
  }
}

/**
 * Форматирование байтов в человекочитаемый формат
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Б';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = i < sizes.length ? sizes[i] : sizes[sizes.length - 1];

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + size;
}

/**
 * Склонение слов
 */
export function pluralize(count: number, words: [string, string, string]): string {
  const cases = [2, 0, 1, 1, 1, 2];
  const index = (count % 100 > 4 && count % 100 < 20) 
    ? 2 
    : cases[Math.min(count % 10, 5)];
  return words[index];
}

/**
 * Форматирование даты
 */
export function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('ru-RU', options || {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * Форматирование цены
 */
export function formatPrice(price: number, currency: string = '₽'): string {
  return `${price.toLocaleString('ru-RU')} ${currency}`;
}

/**
 * Задержка
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Копирование в буфер обмена
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // Fallback
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    return true;
  } catch {
    return false;
  }
}
