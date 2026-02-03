import { MessageCircle, FileText, Globe, Shield, ChevronRight, ExternalLink } from 'lucide-react';
import { haptic } from '../lib/utils';

const supportLinks = [
  {
    id: 'chat',
    icon: <MessageCircle className="w-5 h-5" />,
    title: 'Написать в поддержку',
    description: 'Ответим в течение 15 минут',
    url: 'https://t.me/shftsup_bot',
    highlight: true,
  },
  {
    id: 'faq',
    icon: <FileText className="w-5 h-5" />,
    title: 'Частые вопросы',
    description: 'Ответы на популярные вопросы',
    url: '#faq',
  },
  {
    id: 'docs',
    icon: <Globe className="w-5 h-5" />,
    title: 'Инструкции',
    description: 'Настройка на всех устройствах',
    url: '#docs',
  },
];

const faqItems = [
  {
    question: 'Как подключить VPN?',
    answer: 'Скопируйте конфигурацию из раздела "Главная" и вставьте её в приложение V2Ray или Outline.',
  },
  {
    question: 'Сколько устройств можно подключить?',
    answer: 'К одной подписке можно подключить до 5 устройств одновременно.',
  },
  {
    question: 'Как продлить подписку?',
    answer: 'Перейдите в раздел "Магазин" и выберите нужный тариф. Если включено автопродление, подписка продлится автоматически.',
  },
  {
    question: 'Что делать, если VPN не работает?',
    answer: 'Попробуйте переподключиться или сменить сервер. Если проблема сохраняется, напишите в поддержку.',
  },
  {
    question: 'Как подарить подписку?',
    answer: 'В разделе "Подарки" выберите срок подписки и нажмите "Купить подарок". Вы получите код, который можно передать другу.',
  },
];

export function Support() {
  const handleLinkClick = (url: string) => {
    haptic('light');
    if (url.startsWith('http')) {
      window.open(url, '_blank');
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 pt-6 pb-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-1">Помощь</h1>
        <p className="text-sm text-[#6B7280]">Мы всегда готовы помочь</p>
      </div>

      {/* Support Links */}
      <div className="space-y-3">
        {supportLinks.map((link) => (
          <button
            key={link.id}
            onClick={() => handleLinkClick(link.url)}
            className={`w-full rounded-2xl p-5 border transition-all text-left flex items-center gap-4 ${
              link.highlight
                ? 'bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 border-[#6366F1] hover:border-[#6366F1]'
                : 'bg-[#1A1A1A] border-white/10 hover:border-white/20'
            }`}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              link.highlight ? 'bg-[#6366F1]' : 'bg-[#2A2A2A]'
            }`}>
              {link.icon}
            </div>
            <div className="flex-1">
              <p className="font-semibold">{link.title}</p>
              <p className="text-sm text-[#6B7280]">{link.description}</p>
            </div>
            {link.url.startsWith('http') ? (
              <ExternalLink className="w-5 h-5 text-[#6B7280]" />
            ) : (
              <ChevronRight className="w-5 h-5 text-[#6B7280]" />
            )}
          </button>
        ))}
      </div>

      {/* FAQ */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#6B7280] uppercase tracking-wide">
          Частые вопросы
        </h3>
        <div className="space-y-3">
          {faqItems.map((item, idx) => (
            <details
              key={idx}
              className="group rounded-2xl bg-[#1A1A1A] border border-white/10 overflow-hidden"
            >
              <summary className="flex items-center justify-between p-5 cursor-pointer list-none">
                <span className="font-semibold pr-4">{item.question}</span>
                <ChevronRight className="w-5 h-5 text-[#6B7280] transition-transform group-open:rotate-90" />
              </summary>
              <div className="px-5 pb-5 text-sm text-[#6B7280] leading-relaxed">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>

      {/* Privacy & Terms */}
      <div className="rounded-2xl bg-[#1A1A1A] p-5 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-[#6366F1]" />
          <h3 className="font-semibold">Правовая информация</h3>
        </div>
        <div className="space-y-2 text-sm">
          <button className="flex items-center justify-between w-full text-[#6B7280] hover:text-white transition-colors">
            <span>Политика конфиденциальности</span>
            <ExternalLink className="w-4 h-4" />
          </button>
          <button className="flex items-center justify-between w-full text-[#6B7280] hover:text-white transition-colors">
            <span>Условия использования</span>
            <ExternalLink className="w-4 h-4" />
          </button>
          <button className="flex items-center justify-between w-full text-[#6B7280] hover:text-white transition-colors">
            <span>Политика возврата</span>
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Version */}
      <p className="text-center text-xs text-[#6B7280]">
        shftsecure Mini App v1.0.0
      </p>
    </div>
  );
}

