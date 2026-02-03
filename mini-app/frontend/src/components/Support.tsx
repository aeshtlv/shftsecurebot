import { MessageCircle, Mail, ChevronRight, Shield, Zap } from 'lucide-react';
import { haptic } from '../lib/utils';

export function Support() {
  const openTelegramSupport = () => {
    haptic('light');
    window.open('https://t.me/shftsup_bot', '_blank');
  };

  const openChannel = () => {
    haptic('light');
    window.open('https://t.me/shftsecure', '_blank');
  };

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Помощь</h1>
        <p className="text-sm text-[#6B7280]">Мы всегда готовы помочь</p>
      </div>

      {/* Quick Support */}
      <div className="rounded-2xl bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 p-6 border border-[#6366F1]/30">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-[#6366F1] flex items-center justify-center">
            <MessageCircle className="w-7 h-7" />
          </div>
          <div className="flex-1">
            <h2 className="font-bold text-lg mb-1">Техническая поддержка</h2>
            <p className="text-sm text-[#6B7280]">Ответим на любые вопросы</p>
          </div>
        </div>
        <button
          onClick={openTelegramSupport}
          className="w-full mt-4 py-3 rounded-xl bg-[#6366F1] font-semibold hover:bg-[#5558E8] transition-colors flex items-center justify-center gap-2"
        >
          <MessageCircle className="w-5 h-5" />
          Написать в поддержку
        </button>
      </div>

      {/* Support Features */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Наши преимущества
        </h3>
        <div className="grid grid-cols-1 gap-3">
          <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#10B981]/20 flex items-center justify-center">
              <Zap className="w-6 h-6 text-[#10B981]" />
            </div>
            <div>
              <p className="font-semibold">🌍 Глобальный доступ</p>
              <p className="text-sm text-[#6B7280]">Надёжное соединение по всему миру</p>
            </div>
          </div>
          <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#6366F1]/20 flex items-center justify-center">
              <Zap className="w-6 h-6 text-[#6366F1]" />
            </div>
            <div>
              <p className="font-semibold">🔌 Простое подключение</p>
              <p className="text-sm text-[#6B7280]">Быстрая настройка без сложных шагов</p>
            </div>
          </div>
          <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#F59E0B]/20 flex items-center justify-center">
              <Shield className="w-6 h-6 text-[#F59E0B]" />
            </div>
            <div>
              <p className="font-semibold">🔒 Приватность</p>
              <p className="text-sm text-[#6B7280]">Мы не храним ваши логи</p>
            </div>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Полезные ссылки
        </h3>
        <div className="space-y-2">
          <button
            onClick={openChannel}
            className="w-full rounded-2xl bg-[#1A1A1A] p-4 border border-white/10 hover:border-white/20 transition-colors flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#6366F1]/20 flex items-center justify-center">
                <Mail className="w-5 h-5 text-[#6366F1]" />
              </div>
              <div className="text-left">
                <p className="font-semibold">Новости и обновления</p>
                <p className="text-sm text-[#6B7280]">@shftsecure</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-[#6B7280]" />
          </button>
        </div>
      </div>

      {/* FAQ */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Частые вопросы
        </h3>
        <div className="space-y-3">
          <FAQItem
            question="Как подключить защищённое соединение?"
            answer="Скопируйте конфиг на главной странице shftsecure и вставьте его в любое приложение для защищённого интернет-соединения: v2rayTun (Android), Happ (iOS), Hiddify (Windows/Mac)."
          />
          <FAQItem
            question="Как продлить подписку?"
            answer="Перейдите в раздел 'Магазин' и выберите нужный тариф. Если у вас включено автопродление, подписка продлится автоматически."
          />
          <FAQItem
            question="Как работают рефералы?"
            answer="Пригласите друга по вашей реферальной ссылке. Когда он оформит подписку, вы получите +3 дня к вашей подписке."
          />
          <FAQItem
            question="Что даёт программа лояльности?"
            answer="За каждый потраченный рубль вы получаете 1 балл. Накапливайте баллы и получайте скидки до 15% на все покупки."
          />
        </div>
      </div>

      {/* Bottom Info */}
      <div className="rounded-2xl bg-[#1A1A1A]/50 p-4 border border-white/5 text-center">
        <p className="text-sm text-[#6B7280]">
        shftsecure — сервис защищенного интернет-соединения
        </p>
        <p className="text-xs text-[#6B7280]/60 mt-1">
          © 2025-2026 shftsecure
        </p>
      </div>
    </div>
  );
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
  return (
    <details className="rounded-2xl bg-[#1A1A1A] border border-white/10 overflow-hidden group">
      <summary className="p-4 cursor-pointer list-none flex items-center justify-between">
        <span className="font-medium pr-4">{question}</span>
        <ChevronRight className="w-5 h-5 text-[#6B7280] transition-transform group-open:rotate-90 flex-shrink-0" />
      </summary>
      <div className="px-4 pb-4 text-sm text-[#6B7280] border-t border-white/5 pt-3 mt-1">
        {answer}
      </div>
    </details>
  );
}
