import React, { useState } from 'react';
import { 
  HelpCircle, 
  ChevronDown, 
  MessageCircle,
  Send
} from 'lucide-react';

const faqItems = [
  {
    id: 1,
    question: 'Как настроить защищенное соединение на устройстве?',
    answer: 'После покупки подписки вы получите конфигурационный файл. Скачайте приложение WireGuard для вашей платформы, импортируйте конфиг и нажмите "Подключиться". Ваше соединение будет защищено.'
  },
  {
    id: 2,
    question: 'Можно ли использовать одну подписку на нескольких устройствах?',
    answer: 'Да, одна подписка позволяет использовать до 5 устройств одновременно. Просто импортируйте конфигурацию на каждое устройство.'
  },
  {
    id: 3,
    question: 'Как работает программа лояльности?',
    answer: 'За каждый потраченный рубль вы получаете 1 балл. Накопленные баллы повышают ваш уровень и дают постоянную скидку на все покупки: Silver (5%), Gold (10%), Platinum (15%).'
  },
  {
    id: 4,
    question: 'Что делать, если соединение не устанавливается?',
    answer: 'Проверьте интернет-соединение, убедитесь что у вас активная подписка. Попробуйте переключиться на другой сервер. Если проблема сохраняется, напишите в поддержку.'
  },
  {
    id: 5,
    question: 'Можно ли вернуть деньги?',
    answer: 'Возврат возможен в течение 7 дней с момента покупки, если использовано менее 10% трафика. Свяжитесь с поддержкой для оформления возврата.'
  },
  {
    id: 6,
    question: 'Какие страны доступны для подключения?',
    answer: 'Мы предоставляем серверы в 15+ странах: Нидерланды, Германия, США, Великобритания, Сингапур, Япония и другие. Список постоянно расширяется.'
  },
  {
    id: 7,
    question: 'Как работают подарочные коды?',
    answer: 'Купите подписку в подарок в магазине, получите уникальный код и поделитесь им с другом. Получатель активирует код в разделе "Подарки" и получает полный доступ к сервису.'
  },
  {
    id: 8,
    question: 'Что такое автопродление?',
    answer: 'При включенном автопродлении подписка автоматически продлевается после окончания. Деньги списываются с выбранного способа оплаты. Вы можете отключить автопродление в любой момент.'
  }
];

export function Support() {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Поддержка</h1>
        <p className="text-sm text-[#6B7280]">Ответы на вопросы и помощь</p>
      </div>

      {/* Contact Support */}
      <div className="rounded-2xl bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 p-6 border border-[#6366F1]/30">
        <div className="flex items-start gap-4 mb-4">
          <div className="w-12 h-12 rounded-full bg-[#6366F1] flex items-center justify-center">
            <MessageCircle className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold mb-1">Нужна помощь?</h3>
            <p className="text-sm text-[#6B7280]">
              Наша команда поддержки ответит в течение 2 часов
            </p>
          </div>
        </div>
        <button className="w-full py-3 rounded-xl bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] font-semibold hover:shadow-lg hover:shadow-[#6366F1]/50 transition-shadow flex items-center justify-center gap-2">
          <Send className="w-4 h-4" />
          Написать в поддержку
        </button>
      </div>

      {/* FAQ */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-[#6366F1]" />
          <h3 className="text-lg font-semibold">Часто задаваемые вопросы</h3>
        </div>
        <div className="space-y-2">
          {faqItems.map((item) => {
            const isExpanded = expandedFaq === item.id;
            return (
              <div
                key={item.id}
                className="rounded-2xl bg-[#1A1A1A] border border-white/10 overflow-hidden"
              >
                <button
                  onClick={() => setExpandedFaq(isExpanded ? null : item.id)}
                  className="w-full p-4 flex items-center justify-between text-left hover:bg-[#2A2A2A] transition-colors"
                >
                  <span className="font-medium pr-4">{item.question}</span>
                  <ChevronDown
                    className={`w-5 h-5 flex-shrink-0 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {isExpanded && (
                  <div className="px-4 pb-4">
                    <p className="text-sm text-[#6B7280] leading-relaxed">
                      {item.answer}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Social Links */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Мы в соцсетях
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <SocialButton icon="📱" label="Telegram канал" sublabel="Новости и обновления" />
          <SocialButton icon="💬" label="Telegram чат" sublabel="Сообщество" />
          <SocialButton icon="𝕏" label="Twitter/X" sublabel="@shftsecure" />
          <SocialButton icon="📧" label="Email" sublabel="support@shftsecure.ru" />
        </div>
      </div>

      {/* Guides */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Инструкции
        </h3>
        <div className="space-y-2">
          <GuideButton label="Настройка на iPhone/iPad" />
          <GuideButton label="Настройка на Android" />
          <GuideButton label="Настройка на Windows" />
          <GuideButton label="Настройка на macOS" />
          <GuideButton label="Настройка на Linux" />
        </div>
      </div>

      {/* Additional Info */}
      <div className="rounded-2xl bg-[#1A1A1A] p-4 border border-white/10 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-[#6B7280]">Версия приложения</span>
          <span className="font-mono">1.2.0</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-[#6B7280]">Последнее обновление</span>
          <span className="font-mono">02.02.2026</span>
        </div>
        <div className="h-px bg-white/5 my-2" />
        <div className="flex flex-col gap-2 text-xs text-[#6B7280]">
          <a href="#" className="hover:text-white transition-colors">
            Политика конфиденциальности
          </a>
          <a href="#" className="hover:text-white transition-colors">
            Условия использования
          </a>
          <a href="#" className="hover:text-white transition-colors">
            Лицензионное соглашение
          </a>
        </div>
      </div>
    </div>
  );
}

function SocialButton({ icon, label, sublabel }: { icon: string; label: string; sublabel: string }) {
  return (
    <button className="p-4 rounded-xl bg-[#1A1A1A] border border-white/10 hover:bg-[#2A2A2A] hover:border-white/20 transition-all flex flex-col items-start gap-2">
      <span className="text-2xl">{icon}</span>
      <div className="text-left">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-[#6B7280]">{sublabel}</p>
      </div>
    </button>
  );
}

function GuideButton({ label }: { label: string }) {
  return (
    <button className="w-full p-4 rounded-xl bg-[#1A1A1A] border border-white/10 hover:bg-[#2A2A2A] hover:border-white/20 transition-all flex items-center justify-between">
      <span className="font-medium">{label}</span>
      <ChevronDown className="w-5 h-5 rotate-[-90deg] text-[#6B7280]" />
    </button>
  );
}