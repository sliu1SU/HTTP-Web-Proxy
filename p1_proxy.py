"""
CPSC 5510, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Kevin Lundeen
:Version: s23
"""
from socket import *
import sys
from urllib.parse import urlparse
from pathlib import Path

# status codes
OK = 200
NOT_FOUND = 404
ERROR = 500
ERROR_STATUS = (ERROR, 'Internal Error')

# communication constants
BUF_SIZE = 4096
CODEC = 'UTF-8'
END_L = '\r\n'

# HTTP protocol
VERSION_1_1 = 'HTTP/1.1'
VERSION_1_0 = 'HTTP/1.0'
DEFAULT_PORT = 80


class ParseError(Exception):
    """This class is used for raising errors from the message parser"""
    pass


class Proxy(object):
    """
    This is the main class for the HTTP proxy
    """

    def __init__(self, port):
        """
        Proxy constructor
        :param port: listening port for proxy
        """
        self.listener = self.start_listener(port)
        return

    @staticmethod
    def start_listener(port):
        """
        start a listening socket
        :param port: at this port
        :return: listening socket

        >>> str(Proxy.start_listener(9999))[21:]
        "family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('0.0.0.0', 9999)>"
        """
        s = socket(AF_INET, SOCK_STREAM)
        s.bind(('', port))
        s.listen()
        return s

    @staticmethod
    def to_bytes(text):
        """convenience method string to bytes
        >>> Proxy.to_bytes('abc')
        b'abc'
        """
        return bytes(text, CODEC)

    @staticmethod
    def from_bytes(b_str):
        """convenience method bytes to string
        >>> Proxy.from_bytes(b'abc')
        'abc'
        """
        return str(b_str, CODEC)

    def get_from_origin(self, host, port, path):
        """
        Get the page from the given location
        :param host: origin
        :param port: port number
        :param path: location of object
        :return: (status, headers, content)
        >>> x = Proxy(0).get_from_origin('gaia.cs.umass.edu', 80, '/')
        Sending the following message from proxy to server:
        GET / HTTP/1.1
        host: gaia.cs.umass.edu
        Connection: close
        >>> (x[0], len(x[1]), len(x[2]))
        ((200, 'OK'), 8, 2651)
        """
        message = 'GET {} {}{}'.format(path, VERSION_1_1, END_L)
        message += 'host: {}{}'.format(host, END_L)
        message += 'Connection: close' + END_L
        message += END_L
        with socket(AF_INET, SOCK_STREAM) as origin:
            print('Sending the following message from proxy to server:')
            print(message.replace(END_L, '\n').strip())  # no \r for doctest
            try:
                origin.connect((host, port))
                origin.sendall(self.to_bytes(message))
            except OSError as err:
                return ERROR_STATUS, None, str(err)

            # get first packet from origin (including Content-Length header)
            response = self.from_bytes(origin.recv(BUF_SIZE))
            try:
                while END_L + END_L not in response:
                    response += self.from_bytes(origin.recv(BUF_SIZE))
                beginning, entity_body = response.split(END_L + END_L, 1)
                lines = beginning.splitlines()
                version, code, phrase = lines[0].split(' ', 2)
                code = int(code)
                status = (code, phrase)
                headers = lines[1:]
                if version not in (VERSION_1_0, VERSION_1_1):
                    return (ERROR_STATUS, None,
                            "Don't support origin's version: " + version)
            except (ValueError, TypeError) as err:
                return (500, 'Internal error'), None, str(err)

            # look for Content-Length
            target_length = 0
            for header in headers:
                name, value = [s.strip() for s in header.split(':', 1)]
                if name == 'Content-Length':
                    target_length = int(value)
                    break

            # get any additional parts of entity_body
            entity_body = self.to_bytes(entity_body)
            while len(entity_body) < target_length:
                print('getting more entity body (looking for {} more '
                      'bytes)'.format(target_length - len(entity_body)))
                entity_body += origin.recv(BUF_SIZE)

        return status, headers, entity_body

    def parse_message(self, message):
        """
        Parse the incoming HTTP protocol
        :param message:
        :return: host, port, path
        >>> p = Proxy(0)
        >>> p.parse_message(b'GET http://foo.bar/xyz HTTP/1.1')
        ('foo.bar', 80, '/xyz')
        >>> p.parse_message(b'GET http://foo.bar HTTP/1.1')
        ('foo.bar', 80, '/')
        >>> p.parse_message(b'GET http://foo.bar:909/xyz/ff HTTP/1.1')
        ('foo.bar', 909, '/xyz/ff')
        >>> p.parse_message(b'GET http://foo.bar:garbage/xyz/ff HTTP/1.1')
        ('foo.bar', 80, '/xyz/ff')
        >>> p.parse_message(b'')
        Traceback (most recent call last):
            ...
        proxy.ParseError: no message!
        >>> p.parse_message(b'GET http://foo.bar/xyz')
        Traceback (most recent call last):
            ...
        proxy.ParseError: expected GET <URL> HTTP/1.1 but got: GET http://foo.bar/xyz
        >>> p.parse_message(b'GET http://foo.bar/xyz HTTP/2')
        Traceback (most recent call last):
            ...
        proxy.ParseError: expected GET <URL> HTTP/1.1 but got: GET http://foo.bar/xyz HTTP/2
        >>> p.parse_message(b'POST http://foo.bar/xyz HTTP/1.1')
        Traceback (most recent call last):
            ...
        proxy.ParseError: expected GET <URL> HTTP/1.1 but got: POST http://foo.bar/xyz HTTP/1.1
        >>> p.parse_message(b'GET https://foo.bar/xyz&x=1 HTTP/1.1')
        Traceback (most recent call last):
            ...
        proxy.ParseError: proxy can only handle http scheme, not https
        """
        s = self.from_bytes(message)
        lines = s.splitlines()
        if len(lines) == 0:
            raise ParseError('no message!')
        first_line = lines[0]
        fields = first_line.split()
        if (len(fields) != 3 or fields[2] not in (VERSION_1_0, VERSION_1_1)
                or fields[0] != 'GET'):
            raise ParseError(
                'expected GET <URL> ' + VERSION_1_1 + ' but got: ' +
                first_line)
        pieces = urlparse(self.to_bytes(fields[1]))
        if pieces.scheme != b'http':
            raise ParseError('proxy can only handle http scheme, not '
                             + self.from_bytes(pieces[0]))
        if pieces[3:] != (b'', b'', b''):
            raise ParseError('proxy can only handle URLs without params, '
                             'query, or fragment')
        netloc = self.from_bytes(pieces.netloc)
        host_and_port = netloc.split(':')
        if len(host_and_port) == 1:
            host = netloc
            port = DEFAULT_PORT
        else:
            host, port = host_and_port[:2]
            try:
                port = int(port)
            except ValueError:
                port = 80  # silently use 80 if they have something weird
        path = self.from_bytes(pieces.path)
        if len(path) == 0:
            path = '/'  # root path is implied if path is absent
        return host, port, path

    @staticmethod
    def construe_path(host, port, path):
        """Convenience method for forming relative path
        >>> Proxy.construe_path('test', 80, 'b')
        PosixPath('cache/test/80/b')
        """
        return Path('cache/{}/{}/{}'.format(host, port, path))

    def get_from_cache(self, host, port, path):
        """
        Retrieve content from cache or return 404
        :return: status, headers, content
        >>> Proxy(0).get_from_cache('a', 80, 'test/a/foo.html')
        ((404, 'Not found'), ['Cache-Hit: 0'], None)

        More tests in put_in_cache
        """
        p = self.construe_path(host, port, path)
        if not p.exists() and not p.is_dir():
            headers = ['Cache-Hit: 0']
            return (NOT_FOUND, 'Not found'), headers, None
        content = self.to_bytes(p.read_text(CODEC))
        headers = ['Content-Length: ' + str(len(content)),
                   'Cache-Hit: 1']
        return (OK, 'OK'), headers, content

    def put_in_cache(self, host, port, path, content):
        """Cache a file
        >>> pr = Proxy(0)
        >>> pr.get_from_cache('who.foo.com', 1030, 'a/b/c.html')
        ((404, 'Not found'), ['Cache-Hit: 0'], None)
        >>> pr.put_in_cache('who.foo.com', 1030, 'a/b/c.html', b'hello!')
        >>> pr.get_from_cache('who.foo.com', 1030, 'a/b/c.html')
        ((200, 'OK'), ['Content-Length: 6', 'Cache-Hit: 1'], b'hello!')
        >>> path = Path('cache/who.foo.com/1030/a/b/c.html')  #cleanup test
        >>> path.unlink(); path.parent.rmdir(); path.parent.parent.rmdir()
        >>> path.parent.parent.parent.rmdir()
        >>> path.parent.parent.parent.parent.rmdir()
        """
        p = self.construe_path(host, port, path)
        p.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        try:
            p.write_text(self.from_bytes(content))
        except IsADirectoryError:
            return
        return

    def reply(self, client, status, headers=None, entity_body=None):
        """
        reply to client with result
        :param client: client socket
        :param status: status pair to return, e.g., (404, 'Not found')
        :param headers: optional list of header strings to send
        :param entity_body: optional byte-string to send after headers
        """
        code, text = status
        message = VERSION_1_1 + ' ' + str(code) + ' ' + text + END_L
        if headers is None:
            headers = ['Cache-Hit: 0']
        for header in headers:
            message += header + END_L
        message += END_L
        message = self.to_bytes(message)
        if entity_body is not None:
            message += entity_body
        try:
            client.sendall(message)
        except OSError:
            return

    def serve_forever(self):
        """main loop"""
        while True:
            print('\n' * 2, '*' * 20, 'Ready to serve', '*' * 20)

            # connect and get the HTTP message
            try:
                client, addr = self.listener.accept()
                print('Received a client connection from', addr)
                message = client.recv(BUF_SIZE)
                print('Received a message from this client:', message)
            except OSError as err:
                print('Got error from TCP, so canceling:', err)
                continue

            # parse the message
            try:
                host, port, path = self.parse_message(message)
            except ParseError as err:
                print('Parse error; responding 500 to client: ', err)
                self.reply(client, (ERROR, str(err)))
                client.close()
                continue

            # first try cache
            result = self.get_from_cache(host, port, path)
            status, headers, content = result
            status_code, status_text = status

            # otherwise go to origin server
            if status_code == NOT_FOUND:
                print('Oops! No cache hit! Requesting origin server for the '
                      'file...')
                result = self.get_from_origin(host, port, path)
                status, more_headers, content = result
                headers.extend(more_headers)
                status_code, status_text = status
                if status_code == OK:
                    print('Response received from server, and status code is '
                          '200! Write to cache, save time next time...')
                    self.put_in_cache(host, port, path, content)
                else:
                    print('Response received from server, but status code is '
                          'not 200! No cache writing...')
            else:
                print('Yay! The requested file is in the cache...')

            print('Now responding to the client...')
            self.reply(client, status, headers, content)
            print('All done! Closing socket...')
            client.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 proxy.py LISTEN_PORT")
        exit(1)
    Proxy(int(sys.argv[1])).serve_forever()
