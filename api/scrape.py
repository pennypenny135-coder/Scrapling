from scrapling import Fetcher

def handler(request):
    # 攞 URL parameter
    url = request.args.get('url')
    
    if not url:
        return {'error': 'Missing url parameter'}, 400
    
    # 用 Scrapling 爬
    fetcher = Fetcher()
    response = fetcher.get(url)
    
    # 解析 Yahoo 新聞標題（selector 可能要調整）
    titles = response.css('h3 a').getall()
    links = response.css('h3 a').attribs('href').getall()
    
    # 組裝數據
    news = []
    for title, link in zip(titles, links):
        news.append({
            'title': title,
            'link': link
        })
    
    return {
        'status': 200,
        'data': news
    }
