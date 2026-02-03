import { useState } from 'react';
import { Copy, QrCode, Share2, Calendar, Zap, Crown, Users, AlertCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { formatBytes, pluralize, haptic } from '../lib/utils';
import { LOYALTY_COLORS, getLoyaltyLevel, LOYALTY_DISCOUNTS } from '../config/pricing';
import { useUserProfile } from '../hooks/useApi';
import { getTelegramUser } from '../api/client';

export function Dashboard() {
  const { data: profile, loading, error } = useUserProfile();
  const [copied, setCopied] = useState<'config' | 'link' | null>(null);

  // Копирование конфига подписки
  const handleCopyConfig = async () => {
    if (!profile?.subscription?.subscriptionUrl) {
      haptic('error');
      toast.error('Нет активной подписки');
      return;
    }
    
    try {
      await navigator.clipboard.writeText(profile.subscription.subscriptionUrl);
      haptic('success');
      setCopied('config');
      toast.success('Конфиг скопирован!', { duration: 2000 });
      setTimeout(() => setCopied(null), 2000);
    } catch {
      // Fallback для старых браузеров
      const textArea = document.createElement('textarea');
      textArea.value = profile.subscription.subscriptionUrl;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      haptic('success');
      setCopied('config');
      toast.success('Конфиг скопирован!', { duration: 2000 });
      setTimeout(() => setCopied(null), 2000);
    }
  };

  // Показать QR-код
  const handleShowQr = () => {
    if (!profile?.subscription?.subscriptionUrl) {
      haptic('error');
      return;
    }
    haptic('light');
    // Открываем URL с QR-кодом через Telegram
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(profile.subscription.subscriptionUrl)}`;
    window.open(qrUrl, '_blank');
  };

  // Поделиться реферальной ссылкой
  const handleShare = async () => {
    if (!profile?.referralLink) {
      haptic('error');
      toast.error('Реферальная ссылка недоступна');
      return;
    }

    const shareText = `🔒 Попробуй shftsecure — быстрый и надёжный VPN!\n\nПерейди по ссылке и получи бонус:\n${profile.referralLink}`;

    // Пробуем нативный Share API
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'shftsecure VPN',
          text: shareText,
        });
        haptic('success');
        toast.success('Ссылка отправлена!');
        return;
      } catch {
        // Пользователь отменил или ошибка
      }
    }

    // Fallback - копируем ссылку
    try {
      await navigator.clipboard.writeText(profile.referralLink);
      haptic('success');
      setCopied('link');
      toast.success('Реферальная ссылка скопирована!', { duration: 2000 });
      setTimeout(() => setCopied(null), 2000);
    } catch {
      haptic('error');
      toast.error('Не удалось скопировать ссылку');
    }
  };

  // Загрузка
  if (loading) {
    return (
      <div className="max-w-md mx-auto px-4 pt-6 flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-[#6366F1]" />
      </div>
    );
  }

  // Ошибка
  if (error || !profile) {
    return (
      <div className="max-w-md mx-auto px-4 pt-6">
        <div className="rounded-2xl bg-red-500/10 border border-red-500/30 p-6 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-400">{error || 'Не удалось загрузить данные'}</p>
        </div>
      </div>
    );
  }

  const tgUser = getTelegramUser();
  const loyaltyLevel = getLoyaltyLevel(profile.loyalty.points);
  const discount = LOYALTY_DISCOUNTS[loyaltyLevel];
  const levelColor = LOYALTY_COLORS[loyaltyLevel];

  const subscription = profile.subscription;
  const hasSubscription = subscription && subscription.status === 'active';

  // Расчёт дней подписки
  let daysLeft = 0;
  let daysTotal = 90;
  let daysPassed = 0;
  let timeProgress = 0;
  let endDate = new Date();

  if (hasSubscription && subscription.expireAt) {
    endDate = new Date(subscription.expireAt);
    const now = new Date();
    daysLeft = Math.max(0, Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
    // Примерная оценка общего периода (можно улучшить)
    daysTotal = Math.max(daysLeft, 30);
    daysPassed = Math.max(0, daysTotal - daysLeft);
    timeProgress = Math.min(100, (daysPassed / daysTotal) * 100);
  }

  const trafficUsed = subscription?.trafficUsed || 0;
  const trafficLimit = subscription?.trafficLimit || 1;
  const trafficProgress = Math.min(100, (trafficUsed / trafficLimit) * 100);

  return (
    <div className="max-w-md mx-auto px-4 pt-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">shftsecure</h1>
          <p className="text-sm text-[#6B7280]">
            {hasSubscription ? 'Ваша подписка' : 'Подписка не активна'}
          </p>
        </div>
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#6366F1]/30">
          <span className="text-xl font-bold">
            {(tgUser?.first_name?.[0] || 'S').toUpperCase()}
          </span>
        </div>
      </div>

      {/* Main Subscription Card */}
      {hasSubscription ? (
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#1A1A1A] via-[#2A2A2A] to-[#1A1A1A] p-6 border border-white/10 shadow-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-[#6366F1]/10 via-transparent to-[#8B5CF6]/10" />
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#6366F1]/10 blur-3xl rounded-full" />
          
          <div className="relative space-y-5">
            {/* Header Row */}
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
                  <span className="text-sm font-semibold text-[#10B981]">Активна</span>
                </div>
                <h2 className="text-2xl font-bold mb-1">Premium</h2>
                <p className="text-sm text-[#6B7280]">
                  {daysTotal >= 365 ? '12 месяцев' : daysTotal >= 180 ? '6 месяцев' : daysTotal >= 90 ? '3 месяца' : '1 месяц'}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                {subscription.autoRenewal && (
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
                    {pluralize(daysLeft, ['день', 'дня', 'дней'])}
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
                      {endDate.toLocaleDateString('ru-RU', { 
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
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                  </div>
                </div>
              </div>

              {/* Traffic Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-[#6B7280]">Использовано трафика</span>
                  <span className="font-semibold text-white/90">
                    {formatBytes(trafficUsed)} / {formatBytes(trafficLimit)}
                  </span>
                </div>
                <div className="h-2 bg-[#0F0F0F]/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-[#10B981] to-[#059669] transition-all duration-500"
                    style={{ width: `${trafficProgress}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        // Нет подписки
        <div className="rounded-3xl bg-gradient-to-br from-[#1A1A1A] via-[#2A2A2A] to-[#1A1A1A] p-6 border border-white/10 text-center">
          <AlertCircle className="w-12 h-12 text-[#F59E0B] mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Нет активной подписки</h2>
          <p className="text-sm text-[#6B7280] mb-4">
            Оформите подписку в разделе "Магазин"
          </p>
        </div>
      )}

      {/* Loyalty & Referral Cards */}
      <div className="grid grid-cols-2 gap-3">
        {/* Loyalty Card */}
        <div className="rounded-2xl bg-gradient-to-br from-[#1A1A1A] to-[#2A2A2A] p-4 border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-16 h-16 opacity-10">
            <Crown className="w-full h-full" style={{ color: levelColor }} />
          </div>
          <div className="relative">
            <div className="flex items-center gap-2 mb-3">
              <Crown className="w-4 h-4" style={{ color: levelColor }} />
              <p className="text-xs text-[#6B7280]">Статус</p>
            </div>
            <p className="text-xl font-bold mb-1 capitalize" style={{ color: levelColor }}>
              {loyaltyLevel}
            </p>
            <p className="text-sm text-[#6B7280]">
              {profile.loyalty.points.toLocaleString()} баллов
            </p>
            <div className="mt-3 pt-3 border-t border-white/5">
              <p className="text-xs text-[#6B7280]">Скидка</p>
              <p className="text-lg font-bold text-[#10B981]">{discount}%</p>
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
            <p className="text-xl font-bold mb-1">{profile.totalGiftsPurchased + profile.totalGiftsReceived}</p>
            <p className="text-sm text-[#6B7280]">друзей</p>
            <div className="mt-3 pt-3 border-t border-white/5">
              <p className="text-xs text-[#6B7280]">Бонус за друга</p>
              <p className="text-lg font-bold text-[#10B981]">+3 дня</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {hasSubscription && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
            Быстрые действия
          </h3>
          <div className="grid grid-cols-3 gap-2">
            <QuickActionButton
              icon={<Copy className="w-5 h-5" />}
              label={copied === 'config' ? 'Готово!' : 'Конфиг'}
              onClick={handleCopyConfig}
              active={copied === 'config'}
              disabled={!subscription?.subscriptionUrl}
            />
            <QuickActionButton
              icon={<QrCode className="w-5 h-5" />}
              label="QR-код"
              onClick={handleShowQr}
              disabled={!subscription?.subscriptionUrl}
            />
            <QuickActionButton
              icon={<Share2 className="w-5 h-5" />}
              label={copied === 'link' ? 'Готово!' : 'Пригласить'}
              onClick={handleShare}
              active={copied === 'link'}
            />
          </div>
        </div>
      )}

      {/* Expiration Warning */}
      {hasSubscription && daysLeft <= 7 && (
        <div className="rounded-2xl bg-gradient-to-br from-[#F59E0B]/10 to-[#D97706]/5 border border-[#F59E0B]/30 p-5">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-[#F59E0B]/20 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5 text-[#F59E0B]" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-[#F59E0B] mb-1">
                Подписка истекает через {daysLeft} {pluralize(daysLeft, ['день', 'дня', 'дней'])}
              </p>
              <p className="text-sm text-[#6B7280]">
                {subscription.autoRenewal 
                  ? 'Автопродление включено — всё под контролем'
                  : 'Продлите подписку в разделе "Магазин"'
                }
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function QuickActionButton({ icon, label, onClick, active, disabled }: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all ${
        disabled
          ? 'bg-[#1A1A1A]/50 opacity-50 cursor-not-allowed'
          : active
            ? 'bg-[#10B981] text-white shadow-lg shadow-[#10B981]/30'
            : 'bg-[#1A1A1A] border border-white/10 hover:bg-[#2A2A2A] hover:border-white/20'
      }`}
    >
      <div className={active ? 'text-white' : disabled ? 'text-[#6B7280]' : 'text-[#6366F1]'}>
        {icon}
      </div>
      <span className="text-xs font-medium text-center leading-tight">{label}</span>
    </button>
  );
}
