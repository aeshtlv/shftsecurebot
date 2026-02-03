import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import './types/telegram.d.ts';

// Инициализируем Telegram WebApp
if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready();
  window.Telegram.WebApp.expand();
  window.Telegram.WebApp.setHeaderColor?.('#0F0F0F');
  window.Telegram.WebApp.setBackgroundColor?.('#0F0F0F');
}

createRoot(document.getElementById('root')!).render(<App />);
