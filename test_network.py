import urllib.request
import concurrent.futures

ips = ['172.20.10.' + str(i) for i in range(1, 15)]

def check(ip):
    try:
        req = urllib.request.urlopen('http://' + ip + '/', timeout=2)
        if req.getcode() == 200:
            return ip + ' SUCCESS: ' + req.read().decode('utf-8')[:20]
    except Exception as e:
        return ip + ' FAILED: ' + str(e)
    return ip + ' NO MATCH'

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as e:
    for res in e.map(check, ips):
        print(res)
