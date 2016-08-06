#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Created by Ivan Semernyakov 06.08.16 <direct@beatum-group.ru>
"""
import asyncore
import socket
import sys

buffer_size = 4096  # 8192


class Server(asyncore.dispatcher):
    def __init__(self, port, destaddr, bindaddr="127.0.0.1"):
        asyncore.dispatcher.__init__(self)
        self.destaddr = destaddr
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((bindaddr, port))
        self.listen(10)
        self.session = 0
        print(">>", "Listening: %s:%d" % (bindaddr, port))
        return

    def handle_accept(self):
        (conn, (addr, port)) = self.accept()
        print("Accepted:", addr)
        Proxy(conn, self.session).connect_remote(self.destaddr)
        self.session += 1
        return


class Proxy(asyncore.dispatcher):
    def __init__(self, sock, session):
        self.session = session
        self.send_to_buffer = ""
        self.client = None
        self.disp("BEGIN")
        asyncore.dispatcher.__init__(self, sock)
        return

    def handle_request(self, s):
        print("<<<", "%r" % s)
        return s

    # overridable methods
    def local_to_remote(self, s):
        self.handle_request(s)
        print(">>>", "%r" % s)
        return s

    def remote_to_local(self, s):
        print("<<<", "%r" % s)
        return s

    def connect_remote(self, addr):
        assert not self.client, "already connected"
        self.addr = addr
        self.disp("Connecting to %s:%d" % self.addr)
        self.client = Client(self)
        self.client.connect(addr)
        return

    def disconnect_remote(self):
        assert self.client, "Not connected"
        self.client.close()
        self.client = None
        return

    def disp(self, s):
        print(">>", "Session %s:" % self.session, s)
        return

    def remote_connected(self):
        self.disp("Connected to remote %s:%d" % self.addr)
        return

    def remote_closed(self):
        self.disp("Closed by remote %s:%d" % self.addr)
        self.client = None
        if not self.send_to_buffer:
            self.handle_close()
        return

    def remote_error(self):
        self.disp("Error by remote %s:%d" % self.addr)
        return

    def remote_read(self, data):
        if data:
            data = self.remote_to_local(data)
            if data:
                self.send_to_buffer += data
        return

    def handle_read(self):
        data = self.recv(buffer_size)
        if data:
            data = self.local_to_remote(data)
            if data and self.client:
                self.client.remote_write(data)
        return

    def writable(self):
        return 0 < len(self.send_to_buffer)

    def handle_write(self):
        n = self.send(self.send_to_buffer)
        self.send_to_buffer = self.send_to_buffer[n:]
        if not self.send_to_buffer and not self.client:
            self.handle_close()
        return

    def handle_close(self):
        if self.client:
            self.disp("Closed by local")
            self.disconnect_remote()
        self.close()
        self.disp("END")
        return


class Client(asyncore.dispatcher):
    def __init__(self, proxy):
        self.proxy = proxy
        self.send_to_buffer = ""
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        return

    def handle_connect(self):
        self.proxy.remote_connected()
        return

    def handle_close(self):
        self.proxy.remote_closed()
        self.close()
        return

    def handle_error(self):
        self.proxy.remote_error()
        return

    def handle_read(self):
        self.proxy.remote_read(self.recv(buffer_size))

        return

    def remote_write(self, data):
        self.send_to_buffer += data
        return

    def writable(self):
        return 0 < len(self.send_to_buffer)

    def handle_write(self):
        n = self.send(self.send_to_buffer)
        self.send_to_buffer = self.send_to_buffer[n:]
        return

    def handle_data(self):
        data = self.data
        print(repr(data.head))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(">>", sys.stderr, "Use: python asynserver.py "
                                "local_port remote_host remote_port")
        sys.exit(2)
    Server(int(sys.argv[1]), (sys.argv[2], int(sys.argv[3])))
    asyncore.loop()
