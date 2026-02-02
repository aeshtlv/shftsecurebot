// Pricing configuration for SHFT Secure
// These values should match the bot's configuration

export const PLANS = [
  {
    id: '1m',
    period: '1 месяц',
    months: 1,
    basePrice: 129,
    traffic: '100 ГБ',
    trafficGb: 100,
    badge: null,
  },
  {
    id: '3m',
    period: '3 месяца',
    months: 3,
    basePrice: 299,
    traffic: '300 ГБ',
    trafficGb: 300,
    badge: 'Популярный',
  },
  {
    id: '6m',
    period: '6 месяцев',
    months: 6,
    basePrice: 549,
    traffic: '600 ГБ',
    trafficGb: 600,
    badge: null,
  },
  {
    id: '12m',
    period: '12 месяцев',
    months: 12,
    basePrice: 999,
    traffic: '1200 ГБ',
    trafficGb: 1200,
    badge: 'Выгодный',
  },
] as const;

// Loyalty levels configuration (Quick Start model)
export const LOYALTY_LEVELS = [
  { name: 'Bronze', nameRu: 'Бронза', points: 0, discount: 0, color: '#CD7F32' },
  { name: 'Silver', nameRu: 'Серебро', points: 250, discount: 5, color: '#C0C0C0' },
  { name: 'Gold', nameRu: 'Золото', points: 1000, discount: 10, color: '#FFD700' },
  { name: 'Platinum', nameRu: 'Платина', points: 2500, discount: 15, color: '#E5E4E2' },
] as const;

// Pre-calculated discounted prices (rounded)
export const DISCOUNTED_PRICES = {
  bronze: { '1m': 129, '3m': 299, '6m': 549, '12m': 999 },
  silver: { '1m': 119, '3m': 279, '6m': 519, '12m': 949 },
  gold: { '1m': 115, '3m': 269, '6m': 489, '12m': 899 },
  platinum: { '1m': 109, '3m': 249, '6m': 459, '12m': 849 },
} as const;

// Helper functions
export function getLoyaltyLevel(points: number) {
  for (let i = LOYALTY_LEVELS.length - 1; i >= 0; i--) {
    if (points >= LOYALTY_LEVELS[i].points) {
      return {
        ...LOYALTY_LEVELS[i],
        index: i,
        nextLevel: LOYALTY_LEVELS[i + 1] || null,
      };
    }
  }
  return { ...LOYALTY_LEVELS[0], index: 0, nextLevel: LOYALTY_LEVELS[1] };
}

export function getDiscountedPrice(planId: string, loyaltyLevel: string): number {
  const level = loyaltyLevel.toLowerCase() as keyof typeof DISCOUNTED_PRICES;
  const prices = DISCOUNTED_PRICES[level] || DISCOUNTED_PRICES.bronze;
  return prices[planId as keyof typeof prices] || 0;
}

export function calculateSavings(basePrice: number, discountedPrice: number): number {
  if (basePrice <= 0) return 0;
  return Math.round(((basePrice - discountedPrice) / basePrice) * 100);
}

export function getPlanById(id: string) {
  return PLANS.find(p => p.id === id);
}

