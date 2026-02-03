// Цены подписок (синхронизировано с ботом)
export const SUBSCRIPTION_PLANS = [
  {
    id: '1m',
    months: 1,
    period: '1 месяц',
    price: 129,
    traffic: 'Для знакомства',
    trafficBytes: 100 * 1024 * 1024 * 1024,
    popular: false,
  },
  {
    id: '3m',
    months: 3,
    period: '3 месяца',
    price: 299,
    traffic: 'Популярный выбор ⭐',
    trafficBytes: 300 * 1024 * 1024 * 1024,
    popular: true,
  },
  {
    id: '6m',
    months: 6,
    period: '6 месяцев',
    price: 549,
    traffic: 'Для постоянных',
    trafficBytes: 600 * 1024 * 1024 * 1024,
    popular: false,
  },
  {
    id: '12m',
    months: 12,
    period: '12 месяцев',
    price: 999,
    traffic: 'Всё включено',
    trafficBytes: 1200 * 1024 * 1024 * 1024,
    popular: false,
  },
] as const;

// Пороги лояльности (Quick Start)
export const LOYALTY_THRESHOLDS = {
  bronze: 0,
  silver: 250,
  gold: 1000,
  platinum: 2500,
} as const;

// Скидки по уровням лояльности (в процентах для отображения)
export const LOYALTY_DISCOUNTS = {
  bronze: 0,
  silver: 5,
  gold: 10,
  platinum: 15,
} as const;

// Цвета уровней лояльности
export const LOYALTY_COLORS = {
  bronze: '#CD7F32',
  silver: '#C0C0C0',
  gold: '#FFD700',
  platinum: '#E5E4E2',
} as const;

export type LoyaltyLevel = keyof typeof LOYALTY_THRESHOLDS;

export function getLoyaltyLevel(points: number): LoyaltyLevel {
  if (points >= LOYALTY_THRESHOLDS.platinum) return 'platinum';
  if (points >= LOYALTY_THRESHOLDS.gold) return 'gold';
  if (points >= LOYALTY_THRESHOLDS.silver) return 'silver';
  return 'bronze';
}

export function getDiscountedPrice(price: number, level: LoyaltyLevel): number {
  const discount = LOYALTY_DISCOUNTS[level];
  return Math.ceil(price * (100 - discount) / 100);
}

export function getNextLevelInfo(currentPoints: number, currentLevel: LoyaltyLevel) {
  const levels: LoyaltyLevel[] = ['bronze', 'silver', 'gold', 'platinum'];
  const currentIndex = levels.indexOf(currentLevel);
  
  if (currentIndex >= levels.length - 1) return null;
  
  const nextLevel = levels[currentIndex + 1];
  const pointsNeeded = LOYALTY_THRESHOLDS[nextLevel] - currentPoints;
  const progress = (currentPoints - LOYALTY_THRESHOLDS[currentLevel]) / 
    (LOYALTY_THRESHOLDS[nextLevel] - LOYALTY_THRESHOLDS[currentLevel]) * 100;
  
  return {
    nextLevel,
    pointsNeeded,
    progress: Math.min(100, Math.max(0, progress)),
  };
}

