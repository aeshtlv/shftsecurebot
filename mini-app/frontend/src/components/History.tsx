import { useState } from 'react';
import { CreditCard, Star, Smartphone, Gift, Clock, CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';
import { haptic } from '../lib/utils';
import { usePayments } from '../hooks/useApi';

const methodIcons: Record<string, React.ReactNode> = {
  stars: <Star className="w-4 h-4" />,
  sbp: <Smartphone className="w-4 h-4" />,
  card: <CreditCard className="w-4 h-4" />,
};

const methodNames: Record<string, string> = {
  stars: 'Telegram Stars',
  sbp: 'СБП',
  card: 'Банковская карта',
};

export function History() {
  const { data: payments, loading, error } = usePayments();
  const [filter, setFilter] = useState<'all' | 'subscription' | 'gift'>('all');

  const filteredPayments = payments.filter((payment) => {
    if (filter === 'all') return true;
    return payment.type === filter;
  });

  const totalSpent = payments
    .filter((p) => p.status === 'completed' && p.currency === '₽')
    .reduce((sum, p) => sum + p.amount, 0);

  const totalPayments = payments.filter((p) => p.status === 'completed').length;

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
        <h1 className="text-2xl font-bold mb-1">История платежей</h1>
        <p className="text-sm text-[#6B7280]">Все ваши транзакции</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10">
          <p className="text-sm text-[#6B7280] mb-1">Всего потрачено</p>
          <p className="text-2xl font-bold">{totalSpent.toLocaleString()} ₽</p>
        </div>
        <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10">
          <p className="text-sm text-[#6B7280] mb-1">Платежей</p>
          <p className="text-2xl font-bold">{totalPayments}</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2 p-1 bg-[#1A1A1A] rounded-xl">
        {[
          { id: 'all', label: 'Все' },
          { id: 'subscription', label: 'Подписки' },
          { id: 'gift', label: 'Подарки' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              haptic('light');
              setFilter(tab.id as typeof filter);
            }}
            className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors ${
              filter === tab.id
                ? 'bg-[#6366F1] text-white'
                : 'text-[#6B7280] hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Payments List */}
      <div className="space-y-3">
        {filteredPayments.length === 0 ? (
          <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
            <Clock className="w-12 h-12 text-[#6B7280] mx-auto mb-4" />
            <p className="text-[#6B7280]">Платежей не найдено</p>
          </div>
        ) : (
          filteredPayments.map((payment) => (
            <div
              key={payment.id}
              className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    payment.type === 'gift' 
                      ? 'bg-[#F59E0B]/20 text-[#F59E0B]'
                      : 'bg-[#6366F1]/20 text-[#6366F1]'
                  }`}>
                    {payment.type === 'gift' ? (
                      <Gift className="w-5 h-5" />
                    ) : (
                      <CreditCard className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold">
                      {payment.type === 'gift' ? 'Подарок' : 'Подписка'}
                    </p>
                    <p className="text-sm text-[#6B7280]">{payment.periodDays} дней</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold">
                    {payment.amount} {payment.currency}
                  </p>
                  <div className="flex items-center justify-end gap-1 text-xs text-[#6B7280]">
                    {methodIcons[payment.method]}
                    <span>{methodNames[payment.method] || payment.method}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-white/5">
                <div className="flex items-center gap-2">
                  {payment.status === 'completed' ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                      <span className="text-sm text-[#10B981]">Успешно</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-[#EF4444]" />
                      <span className="text-sm text-[#EF4444]">Ошибка</span>
                    </>
                  )}
                </div>
                <span className="text-sm text-[#6B7280]">{payment.date}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
