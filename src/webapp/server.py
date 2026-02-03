"""
HTTP сервер для Mini App API.
"""
import asyncio
from aiohttp import web
from typing import Optional

from .routes import setup_routes
from src.utils.logger import logger


class WebAppServer:
    """Управляет HTTP сервером для Mini App."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
    
    async def start(self, bot_token: str, bot_instance=None):
        """
        Запускает HTTP сервер.
        
        Args:
            bot_token: Токен бота для валидации initData
            bot_instance: Экземпляр aiogram Bot
        """
        self.app = web.Application()
        
        # Настраиваем маршруты Mini App
        setup_routes(self.app, bot_token, bot_instance)
        
        # Запускаем сервер
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f'🌐 Mini App API server started on http://{self.host}:{self.port}')
    
    async def stop(self):
        """Останавливает HTTP сервер."""
        if self.runner:
            await self.runner.cleanup()
            logger.info('🌐 Mini App API server stopped')


# Глобальный экземпляр сервера
_server: Optional[WebAppServer] = None


async def start_webapp_server(bot_token: str, bot_instance=None, port: int = 8080) -> WebAppServer:
    """
    Запускает Mini App API сервер.
    
    Args:
        bot_token: Токен бота
        bot_instance: Экземпляр aiogram Bot
        port: Порт сервера
    
    Returns:
        WebAppServer instance
    """
    global _server
    _server = WebAppServer(port=port)
    await _server.start(bot_token, bot_instance)
    return _server


async def stop_webapp_server():
    """Останавливает Mini App API сервер."""
    global _server
    if _server:
        await _server.stop()
        _server = None

