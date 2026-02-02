import React, { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { Loyalty } from './components/Loyalty';
import { Shop } from './components/Shop';
import { Gifts } from './components/Gifts';
import { History } from './components/History';
import { Support } from './components/Support';
import { Home, Award, ShoppingBag, Gift, Clock, HelpCircle } from 'lucide-react';

type Tab = 'dashboard' | 'loyalty' | 'shop' | 'gifts' | 'history' | 'support';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'loyalty':
        return <Loyalty />;
      case 'shop':
        return <Shop />;
      case 'gifts':
        return <Gifts />;
      case 'history':
        return <History />;
      case 'support':
        return <Support />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F0F] text-white pb-20">
      {/* Content */}
      <main className="pb-4">
        {renderContent()}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-[#1A1A1A]/95 backdrop-blur-xl border-t border-white/10">
        <div className="max-w-md mx-auto px-2 py-3">
          <div className="flex items-center justify-around">
            <TabButton
              icon={<Home className="w-5 h-5" />}
              label="Главная"
              active={activeTab === 'dashboard'}
              onClick={() => setActiveTab('dashboard')}
            />
            <TabButton
              icon={<Award className="w-5 h-5" />}
              label="Лояльность"
              active={activeTab === 'loyalty'}
              onClick={() => setActiveTab('loyalty')}
            />
            <TabButton
              icon={<ShoppingBag className="w-5 h-5" />}
              label="Магазин"
              active={activeTab === 'shop'}
              onClick={() => setActiveTab('shop')}
            />
            <TabButton
              icon={<Gift className="w-5 h-5" />}
              label="Подарки"
              active={activeTab === 'gifts'}
              onClick={() => setActiveTab('gifts')}
            />
            <TabButton
              icon={<Clock className="w-5 h-5" />}
              label="История"
              active={activeTab === 'history'}
              onClick={() => setActiveTab('history')}
            />
            <TabButton
              icon={<HelpCircle className="w-5 h-5" />}
              label="Помощь"
              active={activeTab === 'support'}
              onClick={() => setActiveTab('support')}
            />
          </div>
        </div>
      </nav>
    </div>
  );
}

function TabButton({ icon, label, active, onClick }: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
        active ? 'text-[#6366F1]' : 'text-[#6B7280] hover:text-white'
      }`}
    >
      {icon}
      <span className="text-[10px] font-medium">{label}</span>
    </button>
  );
}
