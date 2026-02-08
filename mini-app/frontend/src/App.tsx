import { useState } from 'react';
import { Home, Award, ShoppingBag, Gift, Clock, HelpCircle } from 'lucide-react';
import { Toaster } from 'sonner';
import { Dashboard } from './components/Dashboard';
import { Loyalty } from './components/Loyalty';
import { Shop } from './components/Shop';
import { Gifts } from './components/Gifts';
import { History } from './components/History';
import { Support } from './components/Support';
import { haptic } from './lib/utils';

type Tab = 'dashboard' | 'loyalty' | 'shop' | 'gifts' | 'history' | 'support';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  const handleTabChange = (tab: Tab) => {
    haptic('light');
    setActiveTab(tab);
  };

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
      {/* Toast Notifications */}
      <Toaster 
        position="top-center" 
        toastOptions={{
          style: {
            background: '#1A1A1A',
            color: '#fff',
            border: '1px solid rgba(255,255,255,0.1)',
          },
        }}
      />
      
      <main className="pb-4">
        {renderContent()}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-[#1A1A1A]/95 backdrop-blur-xl border-t border-white/10 safe-area-bottom">
        <div className="max-w-md mx-auto px-1 py-2">
          <div className="grid grid-cols-6 gap-0">
            <TabButton
              icon={<Home className="w-[18px] h-[18px]" />}
              label="Главная"
              active={activeTab === 'dashboard'}
              onClick={() => handleTabChange('dashboard')}
            />
            <TabButton
              icon={<Award className="w-[18px] h-[18px]" />}
              label="Статус"
              active={activeTab === 'loyalty'}
              onClick={() => handleTabChange('loyalty')}
            />
            <TabButton
              icon={<ShoppingBag className="w-[18px] h-[18px]" />}
              label="Магазин"
              active={activeTab === 'shop'}
              onClick={() => handleTabChange('shop')}
            />
            <TabButton
              icon={<Gift className="w-[18px] h-[18px]" />}
              label="Подарки"
              active={activeTab === 'gifts'}
              onClick={() => handleTabChange('gifts')}
            />
            <TabButton
              icon={<Clock className="w-[18px] h-[18px]" />}
              label="История"
              active={activeTab === 'history'}
              onClick={() => handleTabChange('history')}
            />
            <TabButton
              icon={<HelpCircle className="w-[18px] h-[18px]" />}
              label="Помощь"
              active={activeTab === 'support'}
              onClick={() => handleTabChange('support')}
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
      className={`flex flex-col items-center justify-center gap-0.5 px-1 py-2 rounded-lg transition-colors min-w-0 ${
        active ? 'text-[#6366F1]' : 'text-[#6B7280] hover:text-white'
      }`}
    >
      {icon}
      <span className="text-[9px] font-medium leading-tight text-center whitespace-nowrap overflow-hidden text-ellipsis max-w-full px-0.5">
        {label}
      </span>
    </button>
  );
}

