import { useState } from 'react';
import { Check, Star, CreditCard, Smartphone, Zap } from 'lucide-react';
import { haptic } from '../lib/utils';
import { 
  SUBSCRIPTION_PLANS, 
  getLoyaltyLevel, 
  getDiscountedPrice,
  LOYALTY_DISCOUNTS 
} from '../config/pricing';

const paymentMethods = [
  { id: 'stars', name: 'Telegram Stars', icon: <Star className="w-5 h-5" />, available: true },
  { id: 'sbp', name: 'СБП', icon: <Smartphone className="w-5 h-5" />, available: true },
  { id: 'card', name: 'Банковская карта', icon: <CreditCard className="w-5 h-5" />, available: true },
];

// TODO: Get from API
const currentUserPoints = 850;

export function Shop() {
  const [selectedPlan, setSelectedPlan] = useState('3m');
  const [isGift, setIsGift] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState('stars');
  
  const loyaltyLevel = getLoyaltyLevel(currentUserPoints);
  const discount = LOYALTY_DISCOUNTS[loyaltyLevel];
  
  const selected = SUBSCRIPTION_PLANS.find(p => p.id === selectedPlan);
  const finalPrice = selected ? getDiscountedPrice(selected.price, loyaltyLevel) : 0;
  const savings = selected ? selected.price - finalPrice : 0;

  const handleSelectPlan = (planId: string) => {
    haptic('light');
    setSelectedPlan(planId);
  };

  const handleSelectPayment = (methodId: string) => {
    haptic('light');
    setSelectedPayment(methodId);
  };

  const handleToggleGift = () => {
    haptic('light');
    setIsGift(!isGift);
  };

  const handlePurchase = () => {
    haptic('medium');
    // TODO: Implement payment flow
    console.log('Purchase:', { plan: selectedPlan, isGift, paymentMethod: selectedPayment });
  };

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Магазин подписок</h1>
        <p className="text-sm text-[#6B7280]">Выберите подходящий тариф</p>
      </div>

      {/* Gift Toggle */}
      <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold mb-1">Покупка в подарок</p>
            <p className="text-sm text-[#6B7280]">
              {isGift ? 'Вы получите код для активации' : 'Подписка активируется сразу'}
            </p>
          </div>
          <button
            onClick={handleToggleGift}
            className={`w-12 h-7 rounded-full transition-colors relative ${
              isGift ? 'bg-[#6366F1]' : 'bg-[#2A2A2A]'
            }`}
          >
            <div
              className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                isGift ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Plans */}
      <div className="space-y-3">
        {SUBSCRIPTION_PLANS.map((plan) => {
          const isSelected = selectedPlan === plan.id;
          const discountedPrice = getDiscountedPrice(plan.price, loyaltyLevel);
          const pricePerMonth = Math.round(discountedPrice / plan.months);

          return (
            <button
              key={plan.id}
              onClick={() => handleSelectPlan(plan.id)}
              className={`w-full rounded-2xl p-6 border transition-all text-left relative overflow-hidden ${
                isSelected
                  ? 'bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 border-[#6366F1]'
                  : 'bg-[#1A1A1A] border-white/10 hover:border-white/20'
              }`}
            >
              {/* Badge */}
              {plan.badge && (
                <div className="absolute top-4 right-4">
                  <div className="px-3 py-1 rounded-full bg-[#F59E0B] text-xs font-semibold">
                    {plan.badge}
                  </div>
                </div>
              )}

              <div className="flex items-start gap-4">
                {/* Checkbox */}
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1 transition-colors ${
                    isSelected
                      ? 'bg-[#6366F1] border-[#6366F1]'
                      : 'border-[#6B7280]'
                  }`}
                >
                  {isSelected && <Check className="w-4 h-4" />}
                </div>

                <div className="flex-1">
                  <div className="flex items-baseline gap-2 mb-2">
                    <h3 className="text-xl font-bold">{plan.period}</h3>
                    {discount > 0 && (
                      <span className="text-sm text-[#10B981] font-semibold">
                        −{discount}%
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-[#6B7280] mb-3">{plan.traffic} трафика</p>

                  <div className="flex items-baseline gap-2">
                    {discount > 0 && (
                      <span className="text-lg text-[#6B7280] line-through">
                        {plan.price} ₽
                      </span>
                    )}
                    <span className="text-2xl font-bold">{discountedPrice} ₽</span>
                  </div>

                  <p className="text-sm text-[#6B7280] mt-1">
                    {pricePerMonth} ₽/месяц
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Payment Methods */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Способ оплаты
        </h3>
        <div className="space-y-2">
          {paymentMethods.map((method) => (
            <button
              key={method.id}
              onClick={() => handleSelectPayment(method.id)}
              disabled={!method.available}
              className={`w-full rounded-xl p-4 border transition-all flex items-center gap-3 ${
                selectedPayment === method.id
                  ? 'bg-[#1A1A1A] border-[#6366F1]'
                  : 'bg-[#1A1A1A] border-white/10 hover:border-white/20'
              } ${!method.available && 'opacity-50 cursor-not-allowed'}`}
            >
              <div
                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                  selectedPayment === method.id
                    ? 'bg-[#6366F1] border-[#6366F1]'
                    : 'border-[#6B7280]'
                }`}
              >
                {selectedPayment === method.id && <Check className="w-3 h-3" />}
              </div>
              <div className="flex items-center gap-3 flex-1">
                <div className="text-[#6B7280]">{method.icon}</div>
                <span className="font-semibold">{method.name}</span>
              </div>
              {method.id === 'stars' && (
                <span className="text-xs text-[#6B7280]">~{Math.round(finalPrice)} ⭐</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Promo Code */}
      <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10">
        <input
          type="text"
          placeholder="Промокод (опционально)"
          className="w-full bg-transparent border-none outline-none text-white placeholder:text-[#6B7280]"
        />
      </div>

      {/* Summary */}
      <div className="rounded-2xl bg-gradient-to-br from-[#1A1A1A] to-[#2A2A2A] p-6 border border-white/10 space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-[#6B7280]">Базовая цена</span>
          <span className={discount > 0 ? 'line-through' : ''}>{selected?.price} ₽</span>
        </div>
        {discount > 0 && (
          <div className="flex justify-between text-sm">
            <span className="text-[#6B7280]">Скидка лояльности ({discount}%)</span>
            <span className="text-[#10B981]">−{savings} ₽</span>
          </div>
        )}
        <div className="h-px bg-white/10" />
        <div className="flex justify-between items-baseline">
          <span className="text-lg font-semibold">Итого</span>
          <span className="text-3xl font-bold">{finalPrice} ₽</span>
        </div>
      </div>

      {/* Purchase Button */}
      <button 
        onClick={handlePurchase}
        className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] font-semibold text-lg hover:shadow-lg hover:shadow-[#6366F1]/50 transition-shadow flex items-center justify-center gap-2"
      >
        <Zap className="w-5 h-5" />
        Оплатить {finalPrice} ₽
      </button>

      {/* Info */}
      <p className="text-xs text-center text-[#6B7280] leading-relaxed">
        Подписка активируется автоматически после оплаты.{' '}
        {isGift && 'Вы получите код для активации, которым можно поделиться.'}
      </p>
    </div>
  );
}

