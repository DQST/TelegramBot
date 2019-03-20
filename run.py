import asyncio
import logging.config
from typing import Tuple, Any, Optional

import aiohttp
from aiohttp import web

from settings import (
    BASE_URL, HEADERS, TOKEN,
    SITES_FOR_CHECK, HOST, PORT,
    LOGGING, COMMANDS, WEB_HOOK_URL,
)

DELAY = 3600

logger = logging.getLogger(__name__)
logging.config.dictConfig(LOGGING)


class Bot(web.Application):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)
        self.tcp_connector = aiohttp.TCPConnector(verify_ssl=False, limit=1)
        self.session = aiohttp.ClientSession(headers=HEADERS, connector=self.tcp_connector)

    async def _call_method(self, method: str, data: Optional[dict] = None) -> Any:
        async with self.session.post(url=f'{BASE_URL}{method}', json=data or {}) as res:
            return await res.json()

    async def send_message(self, chat_id: int, message: str):
        data = {
            'chat_id': chat_id,
            'text': message,
        }
        return await self._call_method(method='sendMessage', data=data)

    async def set_web_hook(self):
        return await self._call_method('setWebhook', {'url': WEB_HOOK_URL})

    async def delete_web_hook(self):
        return await self._call_method('deleteWebhook')

    async def is_site_available(self, url: str) -> Tuple[str, bool]:
        try:
            async with self.session.get(url) as res:
                return url, res.status == 200
        except aiohttp.ClientConnectionError:
            pass
        return url, False

    async def monitoring(self):
        while True:
            tasks = [
                self.loop.create_task(self.is_site_available(url))
                for url in self['sites_for_checks']
            ]
            res = await asyncio.gather(*tasks)
            for url, status in res:
                if not status:
                    logger.info(f'Site {url} not available.')
                    message = f'Site {url} not available ;('
                    await self.send_message(chat_id=305144318, message=message)
                else:
                    logger.info(f'Site {url} available.')
                await asyncio.sleep(DELAY)

    async def handle(self, request):
        if request.match_info.get('token') == TOKEN:
            data = await request.json()
            logging.info(data)
            data = data['message']
            text = data['text']
            if text.startswith('/'):
                command, *args = text[1:].split(' ')
                chat_id = data['chat']['id']
                if command in COMMANDS:
                    res = COMMANDS[command](*args)
                    await self.send_message(chat_id=chat_id, message=res)
                else:
                    await self.send_message(chat_id=chat_id, message='Unknown command')

        return web.json_response(data={'status': 'ok'})

    async def startup(self):
        await self.delete_web_hook()
        await self.set_web_hook()
        self['sites_for_checks'] = SITES_FOR_CHECK
        self['monitoring_task'] = self.loop.create_task(self.monitoring())

    async def cleanup(self):
        self['monitoring_task'].cancel()
        await self.session.close()
        await self.tcp_connector.close()


def main():
    bot = Bot()
    bot.router.add_post('/{token}/', bot.handle)
    web.run_app(bot, host=HOST, port=PORT)


if __name__ == '__main__':
    main()
