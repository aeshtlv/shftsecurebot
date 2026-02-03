import React, { useState } from 'react';
import { 
  CreditCard, 
  Star, 
  Smartphone, 
  CheckCircle2, 
  Clock, 
  Filter,
  Download
} from 'lucide-react';

const transactions = [
  {
    id: 't1',
    date: new Date('2026-01-28'),
    amount: 790,
    currency: '₽',
    type: 'subscription',
    period: '3 месяца',
    method: 'stars',
    status: 'completed'
  },
  {
    id: 't2',
    date: new Date('2026-01-15'),
    amount: 290,
    currency: '₽',
    type: 'gift',
    period: '1 месяц',
    method: 'sbp',
    status: 'completed'
  },
  {
    id: 't3',
    date: new Date('2025-12-20'),
    amount: 1490,
    currency: '₽',
    type: 'subscription',
    period: '6 месяцев',
    method: 'card',
    status: 'completed'
  },
  {
    id: 't4',
    date: new Date('2025-11-05'),
    amount: 290,
    currency: '₽',
    type: 'subscription',
    period: '1 месяц',
    method: 'stars',
    status: 'completed'
  },
  {
    id: 't5',
    date: new Date('2025-10-12'),
    amount: 790,
    currency: '₽',
    type: 'subscription',
    period: '3 месяца',
    method: 'sbp',
    status: 'completed'
  }
];

const methodIcons = {
  stars: <Star className="w-4 h-4" />,
  sbp: <Smartphone className="w-4 h-4" />,
  card: <CreditCard className="w-4 h-4" />
};

const methodNames = {
  stars: 'Telegram Stars',
  sbp: 'СБП',
  card: 'Банковская карта'
};

const typeNames = {
  subscription: 'Подписка',
  gift: 'Подарок'
};

export function History() {
  const [filter, setFilter] = useState<'all' | 'subscription' | 'gift'>('all');
  const [showFilters, setShowFilters] = useState(false);

  const filteredTransactions = transactions.filter(t => 
    filter === 'all' ? true : t.type === filter
  );

  const totalSpent = transactions
    .filter(t => t.status === 'completed')
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">История платежей</h1>
        <p className="text-sm text-[#6B7280]">Все ваши транзакции</p>
      </div>

      {/* Stats */}
      <div className="rounded-2xl bg-gradient-to-br from-[#1A1A1A] to-[#2A2A2A] p-6 border border-white/10">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-[#6B7280] mb-1">Всего потрачено</p>
            <p className="text-2xl font-bold">{totalSpent.toLocaleString('ru-RU')} ₽</p>
          </div>
          <div>
            <p className="text-sm text-[#6B7280] mb-1">Транзакций</p>
            <p className="text-2xl font-bold">{transactions.length}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#1A1A1A] border border-white/10 hover:bg-[#2A2A2A] transition-colors"
        >
          <Filter className="w-4 h-4" />
          <span className="text-sm font-medium">Фильтры</span>
        </button>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#1A1A1A] border border-white/10 hover:bg-[#2A2A2A] transition-colors">
          <Download className="w-4 h-4" />
          <span className="text-sm font-medium">Экспорт</span>
        </button>
      </div>

      {/* Filter Options */}
      {showFilters && (
        <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10 space-y-2">
          <FilterButton
            label="Все"
            active={filter === 'all'}
            onClick={() => setFilter('all')}
            count={transactions.length}
          />
          <FilterButton
            label="Подписки"
            active={filter === 'subscription'}
            onClick={() => setFilter('subscription')}
            count={transactions.filter(t => t.type === 'subscription').length}
          />
          <FilterButton
            label="Подарки"
            active={filter === 'gift'}
            onClick={() => setFilter('gift')}
            count={transactions.filter(t => t.type === 'gift').length}
          />
        </div>
      )}

      {/* Transactions List */}
      <div className="space-y-3">
        {filteredTransactions.map((transaction, idx) => {
          const isFirstOfMonth = idx === 0 || 
            transaction.date.getMonth() !== filteredTransactions[idx - 1].date.getMonth();

          return (
            <React.Fragment key={transaction.id}>
              {isFirstOfMonth && (
                <div className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide pt-2">
                  {transaction.date.toLocaleDateString('ru-RU', { 
                    month: 'long', 
                    year: 'numeric' 
                  })}
                </div>
              )}
              
              <div className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10 hover:border-white/20 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#2A2A2A] flex items-center justify-center text-[#6B7280]">
                      {methodIcons[transaction.method as keyof typeof methodIcons]}
                    </div>
                    <div>
                      <p className="font-semibold mb-1">
                        {typeNames[transaction.type as keyof typeof typeNames]} • {transaction.period}
                      </p>
                      <p className="text-sm text-[#6B7280]">
                        {methodNames[transaction.method as keyof typeof methodNames]}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold">
                      {transaction.amount} {transaction.currency}
                    </p>
                    {transaction.method === 'stars' && (
                      <p className="text-xs text-[#6B7280]">
                        ~{Math.round(transaction.amount / 2)} ⭐
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-white/5">
                  <div className="flex items-center gap-2">
                    {transaction.status === 'completed' ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                        <span className="text-sm text-[#10B981]">Завершено</span>
                      </>
                    ) : (
                      <>
                        <Clock className="w-4 h-4 text-[#F59E0B]" />
                        <span className="text-sm text-[#F59E0B]">В обработке</span>
                      </>
                    )}
                  </div>
                  <p className="text-xs text-[#6B7280]">
                    {transaction.date.toLocaleDateString('ru-RU')} в{' '}
                    {transaction.date.toLocaleTimeString('ru-RU', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {filteredTransactions.length === 0 && (
        <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
          <Clock className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
          <p className="text-[#6B7280]">Транзакции не найдены</p>
        </div>
      )}

      {/* Info */}
      <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10">
        <p className="text-xs text-[#6B7280] leading-relaxed">
          Все транзакции сохраняются и доступны для просмотра в любое время. 
          Вы можете экспортировать историю в PDF для бухгалтерии.
        </p>
      </div>
    </div>
  );
}

function FilterButton({ 
  label, 
  active, 
  onClick, 
  count 
}: { 
  label: string; 
  active: boolean; 
  onClick: () => void;
  count: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full px-4 py-3 rounded-xl text-left transition-colors flex items-center justify-between ${
        active 
          ? 'bg-[#6366F1] text-white' 
          : 'bg-[#2A2A2A] hover:bg-[#3A3A3A]'
      }`}
    >
      <span className="font-medium">{label}</span>
      <span className={`text-sm ${active ? 'text-white/80' : 'text-[#6B7280]'}`}>
        {count}
      </span>
    </button>
  );
}
