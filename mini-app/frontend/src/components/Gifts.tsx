import { useState } from 'react';
import { Gift, Copy, Check, Plus, Clock, CheckCircle2 } from 'lucide-react';
import { haptic } from '../lib/utils';
import { SUBSCRIPTION_PLANS, getLoyaltyLevel, getDiscountedPrice } from '../config/pricing';

// TODO: Get from API
const mockPurchasedGifts = [
  { id: 1, code: 'GIFT-ABC123-XYZ', days: 30, status: 'active', createdAt: '2026-01-15' },
  { id: 2, code: 'GIFT-DEF456-QRS', days: 90, status: 'used', createdAt: '2025-12-20', activatedAt: '2025-12-25' },
];

const mockReceivedGifts = [
  { id: 1, code: 'GIFT-GHI789-TUV', days: 30, fromUser: '@friend', activatedAt: '2026-01-10' },
];

const currentUserPoints = 850;

export function Gifts() {
  const [activeTab, setActiveTab] = useState<'purchase' | 'my' | 'received'>('purchase');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState('1m');
  const [activateCode, setActivateCode] = useState('');

  const loyaltyLevel = getLoyaltyLevel(currentUserPoints);

  const handleCopyCode = (code: string) => {
    haptic('success');
    navigator.clipboard?.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleActivateGift = () => {
    if (!activateCode.trim()) return;
    haptic('medium');
    // TODO: Implement activation via API
    console.log('Activate gift:', activateCode);
  };

  const handlePurchaseGift = () => {
    haptic('medium');
    // TODO: Implement purchase flow
    console.log('Purchase gift:', selectedPlan);
  };

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
          { id: 'my', label: 'Мои подарки' },
          { id: 'received', label: 'Полученные' },
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
            <div className="flex gap-3">
              <input
                type="text"
                value={activateCode}
                onChange={(e) => setActivateCode(e.target.value.toUpperCase())}
                placeholder="GIFT-XXXXX-XXX"
                className="flex-1 bg-[#2A2A2A] rounded-xl px-4 py-3 text-white placeholder:text-[#6B7280] outline-none border border-transparent focus:border-[#6366F1] font-mono"
              />
              <button 
                onClick={handleActivateGift}
                className="px-5 py-3 rounded-xl bg-[#10B981] font-semibold hover:bg-[#059669] transition-colors"
              >
                <Check className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* My Gifts Tab */}
      {activeTab === 'my' && (
        <div className="space-y-3">
          {mockPurchasedGifts.length === 0 ? (
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
            mockPurchasedGifts.map((gift) => (
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
                  <span className="text-sm text-[#6B7280]">{gift.days} дней</span>
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
                      ? `Создан: ${new Date(gift.createdAt).toLocaleDateString('ru-RU')}`
                      : `Активирован: ${new Date(gift.activatedAt!).toLocaleDateString('ru-RU')}`
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
          {mockReceivedGifts.length === 0 ? (
            <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
              <Gift className="w-12 h-12 text-[#6B7280] mx-auto mb-4" />
              <p className="text-[#6B7280]">У вас пока нет полученных подарков</p>
            </div>
          ) : (
            mockReceivedGifts.map((gift) => (
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
                  <span className="text-sm font-semibold">{gift.days} дней</span>
                </div>

                <div className="flex items-center justify-between text-xs text-[#6B7280]">
                  <span>От: {gift.fromUser}</span>
                  <span>{new Date(gift.activatedAt).toLocaleDateString('ru-RU')}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

