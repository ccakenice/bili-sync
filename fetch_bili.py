import json, hashlib, time, urllib.request, urllib.parse, sys

UID = '3546373951588920'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
]

def basename(url):
    p = url.rsplit('/', 1)[-1]
    return p.rsplit('.', 1)[0] if '.' in p else p

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')

def get_buvid3():
    try:
        raw = http_get('https://api.bilibili.com/x/frontend/finger/spi', {'User-Agent': UA, 'Referer': 'https://www.bilibili.com/'})
        j = json.loads(raw)
        return j.get('data', {}).get('b_3', '') or ''
    except Exception:
        return ''

def get_mixin_key(buvid3):
    headers = {'User-Agent': UA, 'Referer': 'https://www.bilibili.com/'}
    if buvid3:
        headers['Cookie'] = 'buvid3=' + buvid3
    raw = http_get('https://api.bilibili.com/x/web-interface/nav', headers)
    j = json.loads(raw)
    img = basename(j['data']['wbi_img']['img_url'])
    sub = basename(j['data']['wbi_img']['sub_url'])
    s = img + sub
    return ''.join(s[i] for i in MIXIN_KEY_ENC_TAB)[:32]

def sign(params, mixin):
    p = dict(params)
    p['wts'] = int(time.time())
    q = '&'.join(k + '=' + urllib.parse.quote(str(v), safe='') for k, v in sorted(p.items()))
    wrid = hashlib.md5((q + mixin).encode('utf-8')).hexdigest()
    return q + '&w_rid=' + wrid

def main():
    buvid3 = get_buvid3()
    mixin = get_mixin_key(buvid3)
    q = sign({'mid': UID, 'ps': '8', 'pn': '1'}, mixin)
    url = 'https://api.bilibili.com/x/space/arc/search?' + q
    headers = {'User-Agent': UA, 'Referer': 'https://space.bilibili.com/' + UID}
    if buvid3:
        headers['Cookie'] = 'buvid3=' + buvid3
    raw = http_get(url, headers)
    d = json.loads(raw)
    if d.get('code') != 0:
        print('API error:', raw[:300])
        sys.exit(1)
    vlist = d['data']['list']['vlist'][:8]
    items = [{
        'title': v.get('title', ''),
        'link': 'https://www.bilibili.com/video/' + v.get('bvid', ''),
        'pubDate': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(v.get('created', 0))),
        'media': {'thumbnail': v.get('pic', '')},
        'description': v.get('description', '')
    } for v in vlist]
    with open('latest.json', 'w', encoding='utf-8') as f:
        json.dump({'code': 0, 'data': items}, f, ensure_ascii=False, indent=2)
    print('updated', len(items), 'videos')

if __name__ == '__main__':
    main()
