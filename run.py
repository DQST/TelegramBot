import asyncio
import logging
import logging.config
from typing import Tuple, Any

import aiohttp
from aiohttp import web

from settings import BASE_URL, HEADERS, TOKEN, SITES_FOR_CHECK, HOST, PORT, LOGGING

DELAY = 3600

logger = logging.getLogger(__name__)


async def send_request(session: aiohttp.ClientSession, method: str, json_data: dict) -> Any:
    async with session.post(url=f'{BASE_URL}{method}', json=json_data) as res:
        return await res.json()


async def is_site_available(session: aiohttp.ClientSession, url: str) -> Tuple[str, bool]:
    try:
        async with session.get(url) as res:
            return url, res.status == 200
    except aiohttp.ClientConnectionError:
        pass
    return url, False


async def monitoring(app: web.Application):
    tcp_connector = aiohttp.TCPConnector(verify_ssl=False, limit=1)
    async with aiohttp.ClientSession(headers=HEADERS,
                                     connector=tcp_connector) as session:
        await send_request(session, 'deleteWebhook', {})
        await send_request(session, 'setWebhook', {'url': f'https://bot.erc20crawler.com/{TOKEN}/'})
        while True:
            tasks = [
                app.loop.create_task(is_site_available(session, url))
                for url in app['sites_for_checks']
            ]
            res = await asyncio.gather(*tasks)
            for url, status in res:
                if not status:
                    logger.info(f'Site {url} not available.')
                    json_data = {
                        'chat_id': '305144318',
                        'text': f'Site {url} not available ;(',
                    }
                    await send_request(session, method='sendMessage', json_data=json_data)
                else:
                    logger.info(f'Site {url} available.')
                await asyncio.sleep(DELAY)


async def handle(request):
    if request.match_info.get('token') == TOKEN:
        res = await request.json()
        logger.info(res)
    return web.json_response({'status': 'ok'})


async def on_startup(app: web.Application):
    app['sites_for_checks'] = SITES_FOR_CHECK
    app['monitoring_task'] = app.loop.create_task(monitoring(app))


async def on_cleanup(app):
    app['monitoring_task'].cancel()


def main():
    logging.config.dictConfig(LOGGING)
    app = web.Application()
    app.router.add_post('/{token}/', handle)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host=HOST, port=PORT)


if __name__ == '__main__':
    main()
