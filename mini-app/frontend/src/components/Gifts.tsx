import React, { useState } from 'react';
import { Gift, Copy, Share2, CheckCircle2, XCircle, Clock } from 'lucide-react';

const purchasedGifts = [
  {
    id: 'g1',
    code: 'SHFT-A7K9-M2N5-P8Q1',
    status: 'active',
    period: '3 месяца',
    createdAt: new Date('2026-01-15'),
    activatedAt: null
  },
  {
    id: 'g2',
    code: 'SHFT-X3R6-L9T4-W7Y2',
    status: 'used',
    period: '1 месяц',
    createdAt: new Date('2025-12-20'),
    activatedAt: new Date('2025-12-22')
  }
];

const receivedGifts = [
  {
    id: 'r1',
    code: 'SHFT-B5D8-F3H6-J9K2',
    period: '6 месяцев',
    from: 'Мария',
    activatedAt: new Date('2026-01-10')
  }
];

export function Gifts() {
  const [activationCode, setActivationCode] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Мои подарки</h1>
        <p className="text-sm text-[#6B7280]">Управление подарочными кодами</p>
      </div>

      {/* Activation Section */}
      <div className="rounded-2xl bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 p-6 border border-[#6366F1]/30">
        <div className="flex items-center gap-2 mb-4">
          <Gift className="w-5 h-5 text-[#6366F1]" />
          <h3 className="font-semibold">Активировать подарок</h3>
        </div>
        <div className="space-y-3">
          <input
            type="text"
            value={activationCode}
            onChange={(e) => setActivationCode(e.target.value.toUpperCase())}
            placeholder="SHFT-XXXX-XXXX-XXXX"
            className="w-full px-4 py-3 rounded-xl bg-[#0F0F0F] border border-white/10 outline-none focus:border-[#6366F1] transition-colors font-mono text-sm"
            maxLength={19}
          />
          <button className="w-full py-3 rounded-xl bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] font-semibold hover:shadow-lg hover:shadow-[#6366F1]/50 transition-shadow">
            Активировать код
          </button>
        </div>
      </div>

      {/* Purchased Gifts */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
            Купленные подарки
          </h3>
          <span className="text-xs text-[#6B7280]">{purchasedGifts.length}</span>
        </div>

        {purchasedGifts.length === 0 ? (
          <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
            <Gift className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
            <p className="text-[#6B7280]">Вы ещё не купили подарочные коды</p>
          </div>
        ) : (
          <div className="space-y-3">
            {purchasedGifts.map((gift) => (
              <div
                key={gift.id}
                className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      {gift.status === 'active' ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                          <span className="text-sm font-semibold text-[#10B981]">
                            Активен
                          </span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-[#6B7280]" />
                          <span className="text-sm font-semibold text-[#6B7280]">
                            Использован
                          </span>
                        </>
                      )}
                    </div>
                    <p className="text-lg font-semibold">{gift.period}</p>
                  </div>
                  <div className="text-right text-sm text-[#6B7280]">
                    <p>Создан</p>
                    <p className="font-mono text-xs">
                      {gift.createdAt.toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                </div>

                {/* Code */}
                <div className="rounded-xl bg-[#0F0F0F] p-4 mb-3">
                  <p className="text-xs text-[#6B7280] mb-1">Код активации</p>
                  <p className="font-mono text-sm tracking-wider">{gift.code}</p>
                </div>

                {/* Actions */}
                {gift.status === 'active' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleCopy(gift.code, gift.id)}
                      className="flex-1 py-2 px-4 rounded-lg bg-[#2A2A2A] hover:bg-[#3A3A3A] transition-colors flex items-center justify-center gap-2"
                    >
                      {copiedId === gift.id ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                          <span className="text-sm text-[#10B981]">Скопировано</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span className="text-sm">Копировать</span>
                        </>
                      )}
                    </button>
                    <button className="flex-1 py-2 px-4 rounded-lg bg-[#2A2A2A] hover:bg-[#3A3A3A] transition-colors flex items-center justify-center gap-2">
                      <Share2 className="w-4 h-4" />
                      <span className="text-sm">Поделиться</span>
                    </button>
                  </div>
                )}

                {gift.status === 'used' && gift.activatedAt && (
                  <div className="text-sm text-[#6B7280]">
                    Активирован {gift.activatedAt.toLocaleDateString('ru-RU')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Received Gifts */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
            Полученные подарки
          </h3>
          <span className="text-xs text-[#6B7280]">{receivedGifts.length}</span>
        </div>

        {receivedGifts.length === 0 ? (
          <div className="rounded-2xl bg-[#1A1A1A] p-8 border border-white/10 text-center">
            <Clock className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
            <p className="text-[#6B7280]">Вы ещё не получали подарочные коды</p>
          </div>
        ) : (
          <div className="space-y-3">
            {receivedGifts.map((gift) => (
              <div
                key={gift.id}
                className="rounded-2xl bg-gradient-to-br from-[#10B981]/20 to-[#059669]/10 p-5 border border-[#10B981]/30"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Gift className="w-4 h-4 text-[#10B981]" />
                      <span className="text-sm font-semibold text-[#10B981]">
                        От {gift.from}
                      </span>
                    </div>
                    <p className="text-lg font-semibold">{gift.period}</p>
                  </div>
                  <div className="text-right text-sm text-[#6B7280]">
                    <p>Активирован</p>
                    <p className="font-mono text-xs">
                      {gift.activatedAt.toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl bg-[#0F0F0F]/50 p-3">
                  <p className="text-xs text-[#6B7280] mb-1">Код</p>
                  <p className="font-mono text-sm tracking-wider">{gift.code}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10">
        <h4 className="font-semibold mb-2">Как работают подарки</h4>
        <ul className="space-y-2 text-sm text-[#6B7280]">
          <li className="flex gap-2">
            <span>•</span>
            <span>Купите подписку в подарок в магазине</span>
          </li>
          <li className="flex gap-2">
            <span>•</span>
            <span>Поделитесь кодом с другом</span>
          </li>
          <li className="flex gap-2">
            <span>•</span>
            <span>Получатель активирует код в этом разделе</span>
          </li>
          <li className="flex gap-2">
            <span>•</span>
            <span>Каждый код можно использовать только один раз</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
