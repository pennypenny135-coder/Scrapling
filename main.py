from scrapling import Fetcher

def GET(request):
    url = request.args.get('url')
    
    if not url:
        return {'error': 'Missing url parameter'}, 400
    
    try:
        fetcher = Fetcher()
        response = fetcher.get(url)
        
        titles = response.css('h3 a').getall()
        links = response.css('h3 a').attribs('href').getall()
        
        news = []
        for t, l in zip(titles, links):
            if t and l:
                news.append({'title': t, 'link': l})
        
        return {'status': 200, 'data': news}
    
    except Exception as e:
        return {'error': str(e)}, 500
