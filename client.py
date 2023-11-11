import sys
import socket
from urllib.parse import urlparse
from pathlib import Path

#url = 'http://google.com'
url = 'htTP://gaia.cs.umass.edu/'
#url = 'http://frontier.userland.com/stories/storyReader$2159'
#url = 'http://dumbass/ff'
#url = 'httP://css1.seattleu.edu/~lundeenk/CPSC5510/valid.html'
#url = 'http://css1.seattleu.edu/~lundeenk/CPSC5510/404.html'
#url = 'hTtP://css1.seattleU.edu/~lundeenk/CPSC5510/500.php'
#myRequest = f'GET {url} HTTP/1.1'
myRequest = f'GET {url} HTTP/1.1'
myRequest = myRequest.encode('utf-8')

port = 9878 # proxy server listening at this port
address = (socket.gethostname(), port)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)
s.sendall(myRequest)

response = b''
while True:
    msg = s.recv(256)
    if len(msg) <= 0: break
    response += msg
response = response.decode('utf-8')
print(response)
