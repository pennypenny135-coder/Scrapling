from scrapling import Fetcher
import json

def handler(scope, receive, send):
    """ASGI handler for Vercel"""
    async def run():
        # 只處理 GET request
        if scope['type'] == 'http' and scope['method'] == 'GET':
            # 攞 query string
            query_string = scope.get('query_string', b'').decode()
            url_param = ''
            for param in query_string.split('&'):
                if param.startswith('url='):
                    url_param = param[4:]
            
            if not url_param:
                body = json.dumps({'error': 'Missing url parameter'})
                status = 400
            else:
                try:
                    fetcher = Fetcher()
                    response = fetcher.get(url_param)
                    
                    titles = response.css('h3 a').getall()
                    links = response.css('h3 a').attribs('href').getall()
                    
                    news = []
                    for t, l in zip(titles, links):
                        if t and l:
                            news.append({'title': t, 'link': l})
                    
                    body = json.dumps({'status': 200, 'data': news})
                    status = 200
                except Exception as e:
                    body = json.dumps({'error': str(e)})
                    status = 500
            
            # 送 response
            await send({
                'type': 'http.response.start',
                'status': status,
                'headers': [[b'content-type', b'application/json']],
            })
            await send({
                'type': 'http.response.body',
                'body': body.encode(),
            })
    
    return run()
