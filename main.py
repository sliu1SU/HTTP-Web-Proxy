# This is a sample Python script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import sys
import socket
from urllib.parse import urlparse
from pathlib import Path

def checkURLInCache(url, dic):
    if url in dic:
        return True
    return False

def turnUrlToFilename(url):
    fileName = ''
    for ele in url:
        if ele == '/' or ele == ':' or ele == '.':
            ele = '-'
        fileName += ele
    return fileName

def validateClientRequest(msg):
    split_msg = msg.split()
    if split_msg[0] != 'GET':
        return False
    if split_msg[2] != 'HTTP/1.1':
        return False
    return True

# test spliting string
print('testing spliting string...')
url = b" ssss GET  \nhttp://css1.seattleu.edu/~lundeenk/CPSC5510/valid.html  HTTP/1.1 \n"
clientRequest = b"GET http://css1.seattleu.edu/~lundeenk/CPSC5510/valid.html HTTP/1.1"
clientRequest = str(clientRequest, 'utf-8')
print(type(clientRequest))
url = url.decode('utf-8')
split_url = url.split()
print(split_url)
print(validateClientRequest(url))


# practice creating, checking, writing, and saving a file
print('\ntesting creating, writing, and save txt files...')
path_to_file = 'proxy_cache.txt' # this should be the title of html file coming from the url client
# send over
path = Path(path_to_file)
# check if this cache file exist in the project folder
if path.is_file() == False:
    cache = open(path_to_file, "x")

cache = open("proxy_cache.txt", "w")
cache.write("now the file has more content!" + "\n")
cache.write("testing writing feature" + "\n")
cache.close()
cache = open("proxy_cache.txt", "r")
print(cache.read())


# # test create and write html file
# print('\ntesting create, write, save html file...')
# url = "GET http://css1.seattleu.edu/~lundeenk/CPSC5510/valid.html HTTP/1.1"
# cacheFileName = turnUrlToFilename(url.split()[1])
# print('turn url into file name: '+ cacheFileName)
#
# path_to_file = 'cache/' + cacheFileName + '.html' # this is URL given by client input
# path = Path(path_to_file)
# if path.is_file() == False:
#     htmlFile1 = open(path_to_file, "w")
#     htmlFile1.write("<html>\n<head>\n<title> \nOutput Data in an HTML file \
#                </title>\n</head> <body><h1>Welcome to <u>GeeksforGeeks</u></h1>\
#                \n<h2>A <u>CS</u> Portal for Everyone</h2> \n</body></html>")
#     htmlFile1.close()
# else:
#     print('file \"' + path_to_file + '\" already exists...')
# #trying to print the html file on console
# htmlFile = codecs.open('GFG1.html', "r", "utf-8")
# print(htmlFile.read())
# htmlFile.close()


# test create folder
print('\ntesting create folder...')
folderName = 'cache'
if (Path(folderName).exists() == False):
    Path(folderName).mkdir()
    print('create folder \" ' + folderName + "\" is successful")
else:
    print("folder \"" + folderName + '\" alreadt exits')

# test user request validation - after connection has been established with a client



# test parsing URL
request = "GET http://css1.seattleu.edu/~lundeenk/CPSC5510/valid.html HTTP/1.1"
split_msg = request.split()
method = split_msg[0]
url = split_msg[1]
version = split_msg[2]
print('method: ' + method + "; url: " + url + "; version: " + version)
print('\nhere to test parsing url...')
obj = urlparse(request)
print('result after parsing the url: ')
url = obj.geturl()
print(url)
print(obj)
print(type(obj))
# print('scheme: ' + obj.scheme)
# print('netloc: ' + obj.netloc)
# print('hostname: ' + obj.hostname)
# print("url: " + obj.geturl())
# print("port: " + str(obj.port))
# print("path: " + obj.path)


# for now lets assume a client msg
print('\ntesting encoding and decoding here...')
clientMsg = (b'GET http://css1.seattleu.edu/~lundeenk/CPSC5510/valid.html HTTP/1.1')
print(type(clientMsg))
print(clientMsg)
clientMsg = str(clientMsg, 'utf-8')
print(type(clientMsg))
print(clientMsg)
address = ('127.0.0.1', 50116)
print('Received a client connection from', address)

# test convert to upper case and lower case
lower_case = 'httP/1.1'
http_test = 'http://sdad/ss'
print(lower_case.upper())
print(http_test[:7])
