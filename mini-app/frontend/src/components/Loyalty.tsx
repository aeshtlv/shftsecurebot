import { Trophy, TrendingUp, Sparkles } from 'lucide-react';
import { 
  SUBSCRIPTION_PLANS,
  LOYALTY_THRESHOLDS, 
  LOYALTY_DISCOUNTS, 
  LOYALTY_COLORS,
  getLoyaltyLevel,
  getNextLevelInfo,
  getDiscountedPrice,
  type LoyaltyLevel 
} from '../config/pricing';

const loyaltyLevels: { name: LoyaltyLevel; displayName: string }[] = [
  { name: 'bronze', displayName: 'Bronze' },
  { name: 'silver', displayName: 'Silver' },
  { name: 'gold', displayName: 'Gold' },
  { name: 'platinum', displayName: 'Platinum' },
];

// TODO: Get from API
const currentPoints = 850;
const userName = 'Пользователь';
const userUsername = '@user';

export function Loyalty() {
  const currentLevel = getLoyaltyLevel(currentPoints);
  const currentLevelIndex = loyaltyLevels.findIndex(l => l.name === currentLevel);
  const discount = LOYALTY_DISCOUNTS[currentLevel];
  const color = LOYALTY_COLORS[currentLevel];
  const nextLevelInfo = getNextLevelInfo(currentPoints, currentLevel);

  return (
    <div className="max-w-md mx-auto px-4 pt-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Программа лояльности</h1>
        <p className="text-sm text-[#6B7280]">Зарабатывайте баллы и получайте скидки</p>
      </div>

      {/* User Profile */}
      <div className="rounded-2xl bg-[#1A1A1A] p-6 border border-white/10">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center text-2xl font-bold">
            {userName.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold">{userName}</h2>
            <p className="text-sm text-[#6B7280]">{userUsername}</p>
          </div>
        </div>

        {/* Current Status */}
        <div
          className="rounded-xl p-6 relative overflow-hidden"
          style={{
            background: `linear-gradient(135deg, ${color}22 0%, ${color}11 100%)`
          }}
        >
          <div className="absolute top-4 right-4 opacity-20">
            <Trophy className="w-16 h-16" style={{ color }} />
          </div>
          <div className="relative">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5" style={{ color }} />
              <span className="text-lg font-bold capitalize" style={{ color }}>
                {currentLevel}
              </span>
            </div>
            <p className="text-3xl font-bold mb-1">{currentPoints.toLocaleString('ru-RU')}</p>
            <p className="text-sm text-[#6B7280]">баллов накоплено</p>
            
            <div className="mt-4 p-3 rounded-lg bg-[#0F0F0F]/50">
              <p className="text-sm text-[#6B7280] mb-1">Ваша текущая скидка</p>
              <p className="text-2xl font-bold text-[#10B981]">{discount}%</p>
            </div>
          </div>
        </div>

        {/* Progress to Next Level */}
        {nextLevelInfo && (
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-[#6B7280]">До уровня {nextLevelInfo.nextLevel}</span>
              <span className="font-semibold">
                {nextLevelInfo.pointsNeeded} баллов
              </span>
            </div>
            <div className="h-2 bg-[#2A2A2A] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] transition-all duration-500"
                style={{ width: `${nextLevelInfo.progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* All Levels */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Уровни лояльности
        </h3>
        <div className="space-y-3">
          {loyaltyLevels.map((level, idx) => {
            const levelColor = LOYALTY_COLORS[level.name];
            const levelDiscount = LOYALTY_DISCOUNTS[level.name];
            const levelPoints = LOYALTY_THRESHOLDS[level.name];
            const isCurrentLevel = idx === currentLevelIndex;

            return (
              <div
                key={level.name}
                className={`rounded-xl p-4 border transition-all ${
                  isCurrentLevel
                    ? 'bg-[#1A1A1A] border-white/20'
                    : 'bg-[#1A1A1A]/50 border-white/5'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: `${levelColor}22` }}
                    >
                      <Trophy className="w-5 h-5" style={{ color: levelColor }} />
                    </div>
                    <div>
                      <p className="font-semibold" style={{ color: levelColor }}>
                        {level.displayName}
                      </p>
                      <p className="text-xs text-[#6B7280]">
                        От {levelPoints.toLocaleString('ru-RU')} баллов
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-[#10B981]">{levelDiscount}%</p>
                    <p className="text-xs text-[#6B7280]">скидка</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pricing Table with Discounts */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Цены с вашей скидкой
        </h3>
        <div className="rounded-2xl bg-[#1A1A1A] border border-white/10 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left p-4 text-sm font-semibold text-[#6B7280]">Период</th>
                <th className="text-right p-4 text-sm font-semibold text-[#6B7280]">Без скидки</th>
                <th className="text-right p-4 text-sm font-semibold text-[#6B7280]">Ваша цена</th>
              </tr>
            </thead>
            <tbody>
              {SUBSCRIPTION_PLANS.map((plan, idx) => {
                const discountedPrice = getDiscountedPrice(plan.price, currentLevel);
                return (
                  <tr
                    key={plan.id}
                    className={idx < SUBSCRIPTION_PLANS.length - 1 ? 'border-b border-white/5' : ''}
                  >
                    <td className="p-4">
                      <div>
                        <p className="font-semibold">{plan.period}</p>
                        <p className="text-xs text-[#6B7280]">{plan.traffic}</p>
                      </div>
                    </td>
                    <td className="p-4 text-right">
                      <p className="text-sm text-[#6B7280] line-through">
                        {plan.price} ₽
                      </p>
                    </td>
                    <td className="p-4 text-right">
                      <p className="text-lg font-bold text-[#10B981]">
                        {discountedPrice} ₽
                      </p>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* How to Earn Points */}
      <div className="rounded-2xl bg-[#1A1A1A] p-6 border border-white/10">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-[#6366F1]" />
          <h3 className="font-semibold">Как зарабатывать баллы</h3>
        </div>
        <ul className="space-y-3 text-sm">
          <li className="flex justify-between">
            <span className="text-[#6B7280]">Покупка подписки</span>
            <span className="font-semibold">1 ₽ = 1 балл</span>
          </li>
          <li className="flex justify-between">
            <span className="text-[#6B7280]">Реферальная программа</span>
            <span className="font-semibold">500 баллов</span>
          </li>
          <li className="flex justify-between">
            <span className="text-[#6B7280]">Ежемесячная подписка</span>
            <span className="font-semibold">100 баллов/мес</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

