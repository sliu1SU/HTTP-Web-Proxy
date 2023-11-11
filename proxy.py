import sys
import socket
from urllib.parse import urlparse
from pathlib import Path

"""
Project 1: Project #1: Web Proxy

*   A proxy server is created to handle GET request from clients.
*   Proxy server will run indefinitely until admin user terminates it manually.
*   Proxy server can only handle GET request at http/1.1 standard.
*   Proxy server will only store/cache requests with status code of 200.
*   If the response status code from origin server is not 200 or 404, proxy server will 
    override the status code from response to 500 and send it to clients (for example,
    http://google.com will respond with 301 status code, which will be overwritten to 500). 
*   If client request is invalid, proxy will send 500 status code to client.
*   Proxy server will terminate client connection if: (a) client request is malformed, (b) if 
    url provided by client is invalid or/and inaccessible (which will raise exception), and (c) 
    if client request is longer than 4096 bytes.
*   User request url must start with 'http://'
*   User request method must be 'GET'
*   User request http version must be 'HTTP/1.1'

Authors: Sizhe Liu
Version: April 19, 2023
"""


# function to validate client request/input
def validateClientRequest(client_msg):
    """
        function to validate client request/input

        :param client_msg: client request in string format
        :return: False if client request is invalid. True otherwise
    """
    split_msg = client_msg.split()
    if len(split_msg) != 3:
        return False
    if split_msg[0] != 'GET':
        return False
    if split_msg[1][0:7].lower() != 'http://':
        return False
    if split_msg[2] != 'HTTP/1.1':
        return False
    return True


# function to turn url into filename
def turnUrlToFilename(url):
    """
        function to turn url into filename

        :param url: client request url
        :return: filename in string format
    """
    fileName = ''
    for ele in url:
        if ele == '/' or ele == ':' or ele == '.':
            ele = '-'
        fileName += ele
    return fileName


# function to create cache main folder
def createMainFolder(folderName):
    """
        function to create cache folder

        :param folderName: desired folder name
    """
    if Path(folderName).exists() == False:
        Path(folderName).mkdir()
        print(f'main folder: {folderName} is created.')
    else:
        print(f'main folder: {folderName} already exists.')


# function to create cache sub folder
def createSubFolder(mainfolderName, subfolderName):
    """
        function to create cache sub folder

        :param mainfolderName: the main folder name defined by admin user
        :param subfolderName: the subfolder name, use lower case host name here
    """
    sub_path = f'{mainfolderName}/{subfolderName}'
    if Path(sub_path).exists() == False:
        Path(sub_path).mkdir()
        print(f'sub folder: {sub_path} is created.')
    else:
        print(f'sub folder: {mainfolderName}/{subfolderName} already exists.')


# function to create cache file
def createCacheFile(path_to_file, origin_resp):
    """
        function to create cache file, write content to file

        :param path_to_file: relative file path
        :param origin_resp: raw response from origin server
    """
    # handle file checking and creating
    if (not Path(path_to_file).is_file()):
        body = origin_resp.split(b'\r\n\r\n', 1)[1]
        # write payload to file in bytes
        with open(path_to_file, "wb") as file:
            file.write(body)
        print(path_to_file + ' created...')
    else:
        print(path_to_file + ' already exists...')


# function to check the status code from origin server response
def checkStatusCode(lines):
    """
        function to check status code from origin server response

        :param lines: list of lines from origin server response
        :return: status code in int format
    """
    code = lines[0].split()[1]
    if code == b'200':
        return 200
    elif code == b'404':
        return 404
    return 500


# functions to create the request to origin server
def createReqToOrigin(method, path, http_version, host):
    """
        function to create request to origin server

        :param method: 'GET'
        :param path: absolute path in url
        :param http_version: 'HTTP/1.1'
        :param host: host of url
        :return: request itself
    """
    # contracting request
    request = f'{method} {path} {http_version}\r\n'
    request += f'Host: {host}\r\n'
    request += 'Connection: close\r\n'
    request += '\r\n'
    return request


# function to modify response from origin server (cache hit & status code)
def modifyResponse(response):
    """
        function to modified origin server response before replaying it to client

        :param response: raw response from origin server
        :return: the modified response
    """
    cache_header = b'\r\ncache hit: 0\r\n'
    res_list = response.split(b'\r\n', 1)
    code = res_list[0].split()[1]
    if code != b'200' and code != b'404' and code != b'500':
        # modify header
        res_list[0] = b'HTTP/1.1 500 Internal Server Error'
    return res_list[0] + cache_header + res_list[1]


# validate grader input - only one argument - port/socket number is allowed when
# the proxy.py is invoked in command line
if len(sys.argv) != 2:
    print('invalid commandline argument! program terminated.')
    exit(1)
if not sys.argv[1].isnumeric():
    print('invalid port number! program terminated.')
    exit(1)
if int(sys.argv[1]) > 65535 or int(sys.argv[1]) < 1:
    print('invalid port number! program terminated.')
    exit(1)

# create/check main cache folder
fileExtension = '.txt'
mainfolderName = 'cache'
createMainFolder(mainfolderName)

# extract port number from command line argument
portNum = int(sys.argv[1])
# create socket to listen
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket/port number to local host
server.bind(('', portNum))
# turn server on - listening any request
server.listen(1)

# when client establish connection with the proxy server
while True:
    print('********************** proxy is ready ****************************')
    print(f'proxy listening at port: {portNum}')

    # create a socket to talk to the client, store client socket address and ip address
    socClient, address = server.accept()
    print('Received a client connection from', address)

    # receive request from client (bytestream)
    # be CAREFUL here... may get infinite loop
    clientRequest = socClient.recv(4096)
    print('Received a message from this client:', clientRequest)
    clientRequest = str(clientRequest, 'utf-8')

    # validate client request, make sure it is not gibberish
    if validateClientRequest(clientRequest) == False:
        errorMsg = f'HTTP/1.1 500 Internal Server Error\ninvalid client request\n'
        socClient.sendall(bytes(errorMsg, 'utf-8'))
        socClient.close()
        print('invalid client request... connection is closed')
    else:
        # if client request is valid - lets handle the request
        # split client request
        split_client_request = clientRequest.split()
        url = split_client_request[1]

        # create & check if subfolder already exists
        subfolderName = urlparse(url).netloc.split(':')[0].lower()  # get rid of potential port#
        createSubFolder(mainfolderName, subfolderName)

        # convert url to file name and create path to file
        fileName = turnUrlToFilename(url)
        path_to_file = f'{mainfolderName}/{subfolderName}/{fileName}{fileExtension}'

        # check if the file exists in cache
        # case: file is not in cache
        if Path(path_to_file).is_file() == False:
            # file does not exist, need to fetch from original server
            print('the file requested is NOT in cache... fetching from the origin server...')

            # prepare request to origin server - need url, host name, and connection header
            # parse url to get useful info
            parseUrlObj = urlparse(url)
            method = split_client_request[0]
            path = ''
            if len(parseUrlObj.path) == 0:
                path = '/'
            else:
                path = parseUrlObj.path
            http_version = split_client_request[2]
            host = parseUrlObj.netloc.split(':', 1)[0]  # strip port number from url if needed

            # prepare request to origin server - string form
            request_to_origin = createReqToOrigin(method, path, http_version, host)

            # request is ready, lets establish connection with the origin server
            socOriginServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            port = 80
            try:
                socOriginServer.connect((host, port))
            except:
                # handle exception - unable to connect to url provided by client
                errorMsg = f'HTTP/1.1 500 Internal Server Error\n' \
                           f'failed to connect to: {url}! url may be invalid!\n' \
                           f'socket.gaierror: [Errno 11001] getaddrinfo failed\n'
                socClient.sendall(bytes(errorMsg, 'utf-8'))
                socClient.close()
                print('exception encounter... unable to connect to client URL...'
                      ' closing socket...')
                continue

            # & forward client request to the origin server
            print('Sending the following message to proxy to server:')
            print(request_to_origin)
            socOriginServer.sendall(bytes(request_to_origin, 'utf-8'))

            # let's receive the data from the origin server
            response = b''
            while True:
                packet = socOriginServer.recv(4096)
                response += packet
                if len(packet) == 0:
                    # data xfer is done
                    break
            socOriginServer.close()

            # split response into a list of lines (in bytes)
            lines = response.splitlines()

            # check the response code - only 200 will be saved to cache
            code = checkStatusCode(lines)
            if code == 200:
                print('response received from server, and status code is 200! writing to cache...')
                createCacheFile(path_to_file, response)
            else:
                print('response received from server, but status code is not 200! No cache writing...')
                print('relaying response to client...')

            # modify response from origin server (add 'cache hit' header & modify status code if needed)
            # before replaying it back to client
            modified_resp = modifyResponse(response)

            # send the modified response back to client
            socClient.sendall(modified_resp)
            print("job done... closing socket...")
            socClient.close()
        else:
            # file in cache, send it over to the client
            # read content of cache file
            print('the file requested is in the cache! sending it over now...')
            file = open(path_to_file, "rb")
            data = file.read()
            file_len = len(data)

            # prepare custom header
            header = f'HTTP/1.1 200 OK\r\nContent-Length: {file_len}\r\nConnection: close\r\n' \
                     f'Cache-Hit: 1\r\n\r\n'

            # send header, file data, ending msg to client
            socClient.sendall(bytes(header, 'utf-8'))
            socClient.sendall(data)
            file.close()
            socClient.close()
            print("job done...closing socket...")
