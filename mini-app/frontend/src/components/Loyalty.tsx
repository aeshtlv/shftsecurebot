import React from 'react';
import { Trophy, TrendingUp, Sparkles } from 'lucide-react';
import { LOYALTY_LEVELS, PLANS, DISCOUNTED_PRICES, getLoyaltyLevel } from '../config/pricing';

export function Loyalty() {
  // TODO: Get from API
  const currentPoints = 320;
  const userName = 'Пользователь';
  const userHandle = '@user';

  const levelInfo = getLoyaltyLevel(currentPoints);
  const current = levelInfo;
  const next = levelInfo.nextLevel;
  
  const progress = next
    ? ((currentPoints - current.points) / (next.points - current.points)) * 100
    : 100;

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
            {userName.charAt(0)}
          </div>
          <div>
            <h2 className="text-xl font-bold">{userName}</h2>
            <p className="text-sm text-[#6B7280]">{userHandle}</p>
          </div>
        </div>

        {/* Current Status */}
        <div
          className="rounded-xl p-6 relative overflow-hidden"
          style={{
            background: `linear-gradient(135deg, ${current.color}22 0%, ${current.color}11 100%)`
          }}
        >
          <div className="absolute top-4 right-4 opacity-20">
            <Trophy className="w-16 h-16" style={{ color: current.color }} />
          </div>
          <div className="relative">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5" style={{ color: current.color }} />
              <span className="text-lg font-bold" style={{ color: current.color }}>
                {current.nameRu}
              </span>
            </div>
            <p className="text-3xl font-bold mb-1">{currentPoints.toLocaleString('ru-RU')}</p>
            <p className="text-sm text-[#6B7280]">баллов накоплено</p>
            
            <div className="mt-4 p-3 rounded-lg bg-[#0F0F0F]/50">
              <p className="text-sm text-[#6B7280] mb-1">Ваша текущая скидка</p>
              <p className="text-2xl font-bold text-[#10B981]">{current.discount}%</p>
            </div>
          </div>
        </div>

        {/* Progress to Next Level */}
        {next && (
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-[#6B7280]">До уровня {next.nameRu}</span>
              <span className="font-semibold">
                {next.points - currentPoints} баллов
              </span>
            </div>
            <div className="h-2 bg-[#2A2A2A] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] transition-all duration-500"
                style={{ width: `${Math.min(progress, 100)}%` }}
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
          {LOYALTY_LEVELS.map((level, idx) => (
            <div
              key={level.name}
              className={`rounded-xl p-4 border transition-all ${
                idx === current.index
                  ? 'bg-[#1A1A1A] border-white/20'
                  : 'bg-[#1A1A1A]/50 border-white/5'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: `${level.color}22` }}
                  >
                    <Trophy className="w-5 h-5" style={{ color: level.color }} />
                  </div>
                  <div>
                    <p className="font-semibold" style={{ color: level.color }}>
                      {level.nameRu}
                    </p>
                    <p className="text-xs text-[#6B7280]">
                      От {level.points.toLocaleString('ru-RU')} баллов
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-[#10B981]">{level.discount}%</p>
                  <p className="text-xs text-[#6B7280]">скидка</p>
                </div>
              </div>
            </div>
          ))}
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
                <th className="text-right p-4 text-sm font-semibold text-[#6B7280]">
                  Ваша цена
                </th>
              </tr>
            </thead>
            <tbody>
              {PLANS.map((plan, idx) => {
                const levelKey = current.name.toLowerCase() as keyof typeof DISCOUNTED_PRICES;
                const discountedPrice = DISCOUNTED_PRICES[levelKey]?.[plan.id as keyof typeof DISCOUNTED_PRICES.bronze] || plan.basePrice;
                
                return (
                  <tr
                    key={plan.id}
                    className={idx < PLANS.length - 1 ? 'border-b border-white/5' : ''}
                  >
                    <td className="p-4">
                      <div>
                        <p className="font-semibold">{plan.period}</p>
                        <p className="text-xs text-[#6B7280]">{plan.traffic}</p>
                      </div>
                    </td>
                    <td className="p-4 text-right">
                      <p className="text-sm text-[#6B7280] line-through">
                        {plan.basePrice} ₽
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
            <span className="font-semibold">+50 баллов</span>
          </li>
          <li className="flex justify-between">
            <span className="text-[#6B7280]">Подарочная подписка</span>
            <span className="font-semibold">1 ₽ = 1 балл</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
