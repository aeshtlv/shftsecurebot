import { useState } from 'react';
import { Gift, Copy, Check, Plus, Clock, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { haptic } from '../lib/utils';
import { SUBSCRIPTION_PLANS, getLoyaltyLevel, getDiscountedPrice } from '../config/pricing';
import { useGifts, useUserProfile } from '../hooks/useApi';
import { activateGiftCode } from '../api/client';

export function Gifts() {
  const { data: profile } = useUserProfile();
  const { purchased, received, loading, error, refetch } = useGifts();
  const [activeTab, setActiveTab] = useState<'purchase' | 'my' | 'received'>('purchase');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState('1m');
  const [activateCode, setActivateCode] = useState('');
  const [activating, setActivating] = useState(false);
  const [activateError, setActivateError] = useState<string | null>(null);
  const [activateSuccess, setActivateSuccess] = useState<string | null>(null);

  const currentUserPoints = profile?.loyalty.points || 0;
  const loyaltyLevel = getLoyaltyLevel(currentUserPoints);

  const handleCopyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      haptic('success');
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch {
      haptic('error');
    }
  };

  const handleActivateGift = async () => {
    if (!activateCode.trim()) return;
    
    setActivating(true);
    setActivateError(null);
    setActivateSuccess(null);
    haptic('medium');

    try {
      const result = await activateGiftCode(activateCode.trim());
      if (result.success) {
        setActivateSuccess(`Подарок активирован! Подписка до ${result.expireDate}`);
        setActivateCode('');
        haptic('success');
        refetch();
      } else {
        setActivateError(result.error || 'Не удалось активировать код');
        haptic('error');
      }
    } catch (e) {
      setActivateError(e instanceof Error ? e.message : 'Ошибка активации');
      haptic('error');
    } finally {
      setActivating(false);
    }
  };

  const handlePurchaseGift = () => {
    haptic('medium');
    // TODO: Реализовать покупку через API
    alert('Функция покупки подарка будет добавлена');
  };

  if (loading) {
    return (
      <div className="max-w-md mx-auto px-4 pt-6 flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-[#6366F1]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto px-4 pt-6">
        <div className="rounded-2xl bg-red-500/10 border border-red-500/30 p-6 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Подарочные подписки</h1>
        <p className="text-sm text-[#6B7280]">Дарите и получайте подарки</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 bg-[#1A1A1A] rounded-xl">
        {[
          { id: 'purchase', label: 'Купить' },
          { id: 'my', label: `Мои (${purchased.length})` },
          { id: 'received', label: `Полученные (${received.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              haptic('light');
              setActiveTab(tab.id as typeof activeTab);
            }}
            className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-[#6366F1] text-white'
                : 'text-[#6B7280] hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Purchase Tab */}
      {activeTab === 'purchase' && (
        <div className="space-y-6">
          {/* Gift Plans */}
          <div className="space-y-3">
            {SUBSCRIPTION_PLANS.map((plan) => {
              const isSelected = selectedPlan === plan.id;
              const discountedPrice = getDiscountedPrice(plan.price, loyaltyLevel);

              return (
                <button
                  key={plan.id}
                  onClick={() => {
                    haptic('light');
                    setSelectedPlan(plan.id);
                  }}
                  className={`w-full rounded-2xl p-5 border transition-all text-left flex items-center gap-4 ${
                    isSelected
                      ? 'bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 border-[#6366F1]'
                      : 'bg-[#1A1A1A] border-white/10 hover:border-white/20'
                  }`}
                >
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    isSelected ? 'bg-[#6366F1]' : 'bg-[#2A2A2A]'
                  }`}>
                    <Gift className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold">{plan.period}</p>
                    <p className="text-sm text-[#6B7280]">{plan.traffic}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold">{discountedPrice} ₽</p>
                    {discountedPrice < plan.price && (
                      <p className="text-xs text-[#6B7280] line-through">{plan.price} ₽</p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Purchase Button */}
          <button 
            onClick={handlePurchaseGift}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] font-semibold text-lg hover:shadow-lg hover:shadow-[#6366F1]/50 transition-shadow flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Купить подарок
          </button>

          {/* Activate Gift Code */}
          <div className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10 space-y-4">
            <h3 className="font-semibold">Активировать подарок</h3>
            
            {activateSuccess && (
              <div className="p-3 rounded-lg bg-[#10B981]/20 text-[#10B981] text-sm">
                {activateSuccess}
              </div>
            )}
            
            {activateError && (
              <div className="p-3 rounded-lg bg-red-500/20 text-red-400 text-sm">
                {activateError}
              </div>
            )}
            
            <div className="flex gap-3">
              <input
                type="text"
                value={activateCode}
                onChange={(e) => setActivateCode(e.target.value.toUpperCase())}
                placeholder="GIFT-XXXX-XXXX"
                className="flex-1 bg-[#2A2A2A] rounded-xl px-4 py-3 text-white placeholder:text-[#6B7280] outline-none border border-transparent focus:border-[#6366F1] font-mono"
              />
              <button 
                onClick={handleActivateGift}
                disabled={activating || !activateCode.trim()}
                className="px-5 py-3 rounded-xl bg-[#10B981] font-semibold hover:bg-[#059669] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {activating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Check className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* My Gifts Tab */}
      {activeTab === 'my' && (
        <div className="space-y-3">
          {purchased.length === 0 ? (
            <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
              <Gift className="w-12 h-12 text-[#6B7280] mx-auto mb-4" />
              <p className="text-[#6B7280]">У вас пока нет подарков</p>
              <button 
                onClick={() => setActiveTab('purchase')}
                className="mt-4 text-[#6366F1] font-semibold"
              >
                Купить первый подарок
              </button>
            </div>
          ) : (
            purchased.map((gift) => (
              <div
                key={gift.id}
                className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {gift.status === 'active' ? (
                      <div className="w-2 h-2 rounded-full bg-[#10B981]" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-[#6B7280]" />
                    )}
                    <span className={`text-sm font-medium ${
                      gift.status === 'active' ? 'text-[#10B981]' : 'text-[#6B7280]'
                    }`}>
                      {gift.status === 'active' ? 'Активен' : 'Использован'}
                    </span>
                  </div>
                  <span className="text-sm text-[#6B7280]">{gift.periodDays} дней</span>
                </div>

                <div className="flex items-center justify-between">
                  <code className="font-mono text-sm bg-[#2A2A2A] px-3 py-2 rounded-lg">
                    {gift.code}
                  </code>
                  {gift.status === 'active' && (
                    <button
                      onClick={() => handleCopyCode(gift.code)}
                      className={`p-2 rounded-lg transition-colors ${
                        copiedCode === gift.code
                          ? 'bg-[#10B981] text-white'
                          : 'bg-[#2A2A2A] hover:bg-[#3A3A3A]'
                      }`}
                    >
                      {copiedCode === gift.code ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  )}
                </div>

                <div className="flex items-center gap-2 mt-3 text-xs text-[#6B7280]">
                  <Clock className="w-3 h-3" />
                  <span>
                    {gift.status === 'active'
                      ? `Создан: ${gift.createdAt}`
                      : `Активирован: ${gift.activatedAt}`
                    }
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Received Tab */}
      {activeTab === 'received' && (
        <div className="space-y-3">
          {received.length === 0 ? (
            <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
              <Gift className="w-12 h-12 text-[#6B7280] mx-auto mb-4" />
              <p className="text-[#6B7280]">У вас пока нет полученных подарков</p>
            </div>
          ) : (
            received.map((gift) => (
              <div
                key={gift.id}
                className="rounded-2xl bg-gradient-to-br from-[#10B981]/10 to-[#059669]/5 p-5 border border-[#10B981]/30"
              >
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  <span className="text-sm font-medium text-[#10B981]">Активирован</span>
                </div>

                <div className="flex items-center justify-between mb-3">
                  <code className="font-mono text-sm bg-[#0F0F0F]/50 px-3 py-2 rounded-lg">
                    {gift.code}
                  </code>
                  <span className="text-sm font-semibold">{gift.periodDays} дней</span>
                </div>

                <div className="text-xs text-[#6B7280]">
                  <span>Активирован: {gift.activatedAt}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
