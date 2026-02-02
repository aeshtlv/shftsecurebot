import React, { useState } from 'react';
import { Copy, QrCode, Share2, CheckCircle2, AlertCircle, Calendar, Zap, TrendingUp, Crown, Users, Gift as GiftIcon } from 'lucide-react';

export function Dashboard() {
  const [copied, setCopied] = useState<'config' | 'link' | null>(null);

  const subscriptionData = {
    status: 'active',
    plan: 'Premium',
    duration: '3 месяца',
    startDate: new Date('2026-01-15'),
    endDate: new Date('2026-04-15'),
    trafficUsed: 45.8,
    trafficTotal: 300,
    autoRenew: true,
    devicesConnected: 3,
    devicesMax: 5
  };

  const loyaltyData = {
    level: 'Gold',
    points: 3200,
    discount: 10,
    color: '#FFD700'
  };

  const referralData = {
    referrals: 5,
    earned: 2500
  };

  const daysLeft = Math.ceil((subscriptionData.endDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  const daysTotal = Math.ceil((subscriptionData.endDate.getTime() - subscriptionData.startDate.getTime()) / (1000 * 60 * 60 * 24));
  const daysPassed = daysTotal - daysLeft;
  const timeProgress = (daysPassed / daysTotal) * 100;

  const handleCopy = (type: 'config' | 'link') => {
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="max-w-md mx-auto px-4 pt-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">shftsecure</h1>
          <p className="text-sm text-[#6B7280]">Ваша подписка</p>
        </div>
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#6366F1]/30">
          <span className="text-xl font-bold">S</span>
        </div>
      </div>

      {/* Main Subscription Card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#1A1A1A] via-[#2A2A2A] to-[#1A1A1A] p-6 border border-white/10 shadow-xl">
        <div className="absolute inset-0 bg-gradient-to-br from-[#6366F1]/10 via-transparent to-[#8B5CF6]/10"></div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-[#6366F1]/10 blur-3xl rounded-full"></div>
        
        <div className="relative space-y-5">
          {/* Header Row */}
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></div>
                <span className="text-sm font-semibold text-[#10B981]">Активна</span>
              </div>
              <h2 className="text-2xl font-bold mb-1">{subscriptionData.plan}</h2>
              <p className="text-sm text-[#6B7280]">{subscriptionData.duration}</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              {subscriptionData.autoRenew && (
                <div className="px-3 py-1.5 rounded-full bg-[#6366F1]/20 border border-[#6366F1]/30">
                  <div className="flex items-center gap-1.5">
                    <Zap className="w-3 h-3 text-[#6366F1]" />
                    <span className="text-xs font-semibold text-[#6366F1]">Авто</span>
                  </div>
                </div>
              )}
              <div className="text-right">
                <p className="text-2xl font-bold">{daysLeft}</p>
                <p className="text-xs text-[#6B7280]">
                  {daysLeft === 1 ? 'день' : daysLeft < 5 ? 'дня' : 'дней'}
                </p>
              </div>
            </div>
          </div>

          {/* Expiry Date */}
          <div className="rounded-xl bg-[#0F0F0F]/50 backdrop-blur-sm p-4 border border-white/5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#2A2A2A] flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-[#6366F1]" />
                </div>
                <div>
                  <p className="text-xs text-[#6B7280] mb-0.5">Активна до</p>
                  <p className="font-semibold">
                    {subscriptionData.endDate.toLocaleDateString('ru-RU', { 
                      day: 'numeric', 
                      month: 'long',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Progress Bars */}
          <div className="space-y-4">
            {/* Time Progress */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Срок подписки</span>
                <span className="font-semibold text-white/90">
                  {daysPassed} из {daysTotal} дней
                </span>
              </div>
              <div className="h-2 bg-[#0F0F0F]/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#6366F1] via-[#7C3AED] to-[#8B5CF6] transition-all duration-500 relative overflow-hidden"
                  style={{ width: `${timeProgress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                </div>
              </div>
            </div>

            {/* Traffic Progress */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Использовано трафика</span>
                <span className="font-semibold text-white/90">
                  {subscriptionData.trafficUsed.toFixed(1)} / {subscriptionData.trafficTotal} ГБ
                </span>
              </div>
              <div className="h-2 bg-[#0F0F0F]/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#10B981] to-[#059669] transition-all duration-500"
                  style={{ width: `${(subscriptionData.trafficUsed / subscriptionData.trafficTotal) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loyalty & Referral Cards */}
      <div className="grid grid-cols-2 gap-3">
        {/* Loyalty Card */}
        <div className="rounded-2xl bg-gradient-to-br from-[#1A1A1A] to-[#2A2A2A] p-4 border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-16 h-16 opacity-10">
            <Crown className="w-full h-full" style={{ color: loyaltyData.color }} />
          </div>
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <Crown className="w-4 h-4" style={{ color: loyaltyData.color }} />
              <p className="text-xs text-[#6B7280]">Статус</p>
            </div>
            <p className="text-xl font-bold mb-1" style={{ color: loyaltyData.color }}>
              {loyaltyData.level}
            </p>
            <p className="text-sm text-[#6B7280]">
              {loyaltyData.points.toLocaleString()} баллов
            </p>
            <div className="mt-3 pt-3 border-t border-white/5">
              <p className="text-xs text-[#6B7280]">Скидка</p>
              <p className="text-lg font-bold text-[#10B981]">{loyaltyData.discount}%</p>
            </div>
          </div>
        </div>

        {/* Referral Card */}
        <div className="rounded-2xl bg-gradient-to-br from-[#1A1A1A] to-[#2A2A2A] p-4 border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-16 h-16 opacity-10">
            <Users className="w-full h-full text-[#6366F1]" />
          </div>
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-4 h-4 text-[#6366F1]" />
              <p className="text-xs text-[#6B7280]">Рефералы</p>
            </div>
            <p className="text-xl font-bold mb-1">{referralData.referrals}</p>
            <p className="text-sm text-[#6B7280]">друзей</p>
            <div className="mt-3 pt-3 border-t border-white/5">
              <p className="text-xs text-[#6B7280]">Заработано</p>
              <p className="text-lg font-bold text-[#10B981]">
                {referralData.earned.toLocaleString()} ₽
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Быстрые действия
        </h3>
        <div className="grid grid-cols-3 gap-2">
          <QuickActionButton
            icon={<Copy className="w-5 h-5" />}
            label={copied === 'config' ? 'Готово!' : 'Конфиг'}
            onClick={() => handleCopy('config')}
            active={copied === 'config'}
          />
          <QuickActionButton
            icon={<QrCode className="w-5 h-5" />}
            label="QR-код"
            onClick={() => {}}
          />
          <QuickActionButton
            icon={<Share2 className="w-5 h-5" />}
            label={copied === 'link' ? 'Готово!' : 'Пригласить'}
            onClick={() => handleCopy('link')}
            active={copied === 'link'}
          />
        </div>
      </div>

      {/* Device Stats */}
      <div className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Устройства</h3>
          <span className="text-sm text-[#6B7280]">
            {subscriptionData.devicesConnected} / {subscriptionData.devicesMax}
          </span>
        </div>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#2A2A2A] flex items-center justify-center text-xl">
              📱
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">iPhone 15 Pro</p>
              <p className="text-xs text-[#6B7280]">Последний вход: сегодня, 14:23</p>
            </div>
            <div className="w-2 h-2 rounded-full bg-[#10B981]"></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#2A2A2A] flex items-center justify-center text-xl">
              💻
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">MacBook Pro</p>
              <p className="text-xs text-[#6B7280]">Последний вход: сегодня, 10:15</p>
            </div>
            <div className="w-2 h-2 rounded-full bg-[#10B981]"></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#2A2A2A] flex items-center justify-center text-xl">
              🖥️
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">Windows Desktop</p>
              <p className="text-xs text-[#6B7280]">Последний вход: вчера, 22:41</p>
            </div>
            <div className="w-2 h-2 rounded-full bg-[#6B7280]"></div>
          </div>
        </div>
        <button className="w-full mt-4 py-2.5 rounded-xl bg-[#2A2A2A] hover:bg-[#3A3A3A] transition-colors text-sm font-medium">
          Управление устройствами
        </button>
      </div>

      {/* Expiration Warning */}
      {daysLeft <= 7 && (
        <div className="rounded-2xl bg-gradient-to-br from-[#F59E0B]/10 to-[#D97706]/5 border border-[#F59E0B]/30 p-5">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-[#F59E0B]/20 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5 text-[#F59E0B]" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-[#F59E0B] mb-1">
                Подписка истекает через {daysLeft} {daysLeft === 1 ? 'день' : daysLeft < 5 ? 'дня' : 'дней'}
              </p>
              <p className="text-sm text-[#6B7280] mb-3">
                {subscriptionData.autoRenew 
                  ? 'Автопродление включено — всё под контролем'
                  : 'Продлите подписку, чтобы не потерять доступ'
                }
              </p>
              {!subscriptionData.autoRenew && (
                <button className="px-4 py-2 rounded-lg bg-[#F59E0B] text-white text-sm font-semibold hover:bg-[#D97706] transition-colors">
                  Продлить сейчас
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function QuickActionButton({ icon, label, onClick, active }: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all ${
        active
          ? 'bg-[#10B981] text-white shadow-lg shadow-[#10B981]/30'
          : 'bg-[#1A1A1A] border border-white/10 hover:bg-[#2A2A2A] hover:border-white/20'
      }`}
    >
      <div className={active ? 'text-white' : 'text-[#6366F1]'}>
        {icon}
      </div>
      <span className="text-xs font-medium text-center leading-tight">{label}</span>
    </button>
  );
}
