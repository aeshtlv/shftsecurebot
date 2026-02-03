import { useState } from 'react';
import { Check, Star, CreditCard, Smartphone, Loader2, AlertCircle, Crown } from 'lucide-react';
import { haptic } from '../lib/utils';
import { 
  SUBSCRIPTION_PLANS, 
  getLoyaltyLevel, 
  getDiscountedPrice, 
  LOYALTY_DISCOUNTS,
  LOYALTY_COLORS 
} from '../config/pricing';
import { useUserProfile } from '../hooks/useApi';
import { createPayment } from '../api/client';

type PaymentMethod = 'stars' | 'sbp' | 'card';

const paymentMethods: { id: PaymentMethod; name: string; icon: React.ReactNode; description: string }[] = [
  { id: 'stars', name: 'Telegram Stars', icon: <Star className="w-5 h-5" />, description: 'Быстрая оплата' },
  { id: 'sbp', name: 'СБП', icon: <Smartphone className="w-5 h-5" />, description: 'Без комиссии' },
  { id: 'card', name: 'Карта', icon: <CreditCard className="w-5 h-5" />, description: 'Visa/MasterCard/МИР' },
];

export function Shop() {
  const { data: profile, loading: profileLoading } = useUserProfile();
  const [selectedPlan, setSelectedPlan] = useState('3m');
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('stars');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentUserPoints = profile?.loyalty.points || 0;
  const loyaltyLevel = getLoyaltyLevel(currentUserPoints);
  const discount = LOYALTY_DISCOUNTS[loyaltyLevel];
  const levelColor = LOYALTY_COLORS[loyaltyLevel];

  const handlePurchase = async () => {
    setProcessing(true);
    setError(null);
    haptic('medium');

    try {
      const plan = SUBSCRIPTION_PLANS.find(p => p.id === selectedPlan);
      if (!plan) {
        throw new Error('План не найден');
      }

      const result = await createPayment(plan.months, selectedMethod, false);
      
      if (result.success && result.paymentUrl) {
        haptic('success');
        // Открываем URL оплаты
        window.open(result.paymentUrl, '_blank');
      } else {
        throw new Error(result.error || 'Ошибка создания платежа');
      }
    } catch (e) {
      haptic('error');
      setError(e instanceof Error ? e.message : 'Произошла ошибка');
    } finally {
      setProcessing(false);
    }
  };

  const selectedPlanData = SUBSCRIPTION_PLANS.find(p => p.id === selectedPlan);
  const finalPrice = selectedPlanData ? getDiscountedPrice(selectedPlanData.price, loyaltyLevel) : 0;

  if (profileLoading) {
    return (
      <div className="max-w-md mx-auto px-4 pt-6 flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-[#6366F1]" />
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Магазин</h1>
        <p className="text-sm text-[#6B7280]">Выберите подходящий тариф</p>
      </div>

      {/* Loyalty Discount Badge */}
      {discount > 0 && (
        <div 
          className="rounded-xl p-4 border flex items-center gap-3"
          style={{ 
            backgroundColor: `${levelColor}11`,
            borderColor: `${levelColor}33`
          }}
        >
          <Crown className="w-6 h-6" style={{ color: levelColor }} />
          <div>
            <p className="font-semibold" style={{ color: levelColor }}>
              Ваша скидка: {discount}%
            </p>
            <p className="text-sm text-[#6B7280]">
              Статус {loyaltyLevel} • {currentUserPoints.toLocaleString()} баллов
            </p>
          </div>
        </div>
      )}

      {/* Subscription Plans */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Выберите период
        </h3>
        <div className="space-y-3">
          {SUBSCRIPTION_PLANS.map((plan) => {
            const isSelected = selectedPlan === plan.id;
            const discountedPrice = getDiscountedPrice(plan.price, loyaltyLevel);
            const hasDiscount = discountedPrice < plan.price;

            return (
              <button
                key={plan.id}
                onClick={() => {
                  haptic('light');
                  setSelectedPlan(plan.id);
                }}
                className={`w-full rounded-2xl p-5 border transition-all text-left relative overflow-hidden ${
                  isSelected
                    ? 'bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 border-[#6366F1]'
                    : 'bg-[#1A1A1A] border-white/10 hover:border-white/20'
                }`}
              >
                {plan.popular && (
                  <div className="absolute top-0 right-0 bg-[#10B981] text-xs font-bold px-3 py-1 rounded-bl-xl">
                    Популярный
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      isSelected 
                        ? 'border-[#6366F1] bg-[#6366F1]' 
                        : 'border-[#6B7280]'
                    }`}>
                      {isSelected && <Check className="w-4 h-4" />}
                    </div>
                    <div>
                      <p className="font-semibold text-lg">{plan.period}</p>
                      <p className="text-sm text-[#6B7280]">{plan.traffic}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{discountedPrice} ₽</p>
                    {hasDiscount && (
                      <p className="text-sm text-[#6B7280] line-through">{plan.price} ₽</p>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Payment Methods */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Способ оплаты
        </h3>
        <div className="grid grid-cols-3 gap-2">
          {paymentMethods.map((method) => {
            const isSelected = selectedMethod === method.id;

            return (
              <button
                key={method.id}
                onClick={() => {
                  haptic('light');
                  setSelectedMethod(method.id);
                }}
                className={`rounded-xl p-4 border transition-all flex flex-col items-center gap-2 ${
                  isSelected
                    ? 'bg-[#6366F1]/20 border-[#6366F1]'
                    : 'bg-[#1A1A1A] border-white/10 hover:border-white/20'
                }`}
              >
                <div className={isSelected ? 'text-[#6366F1]' : 'text-[#6B7280]'}>
                  {method.icon}
                </div>
                <span className="text-xs font-medium text-center">{method.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Purchase Button */}
      <button
        onClick={handlePurchase}
        disabled={processing || !selectedPlan || !selectedMethod}
        className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] font-semibold text-lg hover:shadow-lg hover:shadow-[#6366F1]/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {processing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Обработка...
          </>
        ) : (
          <>
            Оплатить {finalPrice} ₽
          </>
        )}
      </button>

      {/* Info */}
      <p className="text-xs text-center text-[#6B7280]">
        После оплаты подписка активируется автоматически
      </p>
    </div>
  );
}
