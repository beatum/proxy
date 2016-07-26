#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created by Ivan Semernyakov 26.07.16
"""
import select
import socket
import sys
import time
import webbrowser

buffer_size = 4096
delay = 0.0001
forward_to = ('ekabu.ru', 80)


class Proxy:
    def __init__(self):
        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.proxy.connect((host, port))
            return self.proxy
        except socket.error as e:
            print e
            return False


class Server:
    input_list = []
    channel = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(10)
        self.total_data = []

    def loop(self):
        self.input_list.append(self.server)
        while 1:
            time.sleep(delay)
            sel = select.select
            r, o, e = sel(self.input_list, [], [])
            for self.s in r:
                if self.s == self.server:
                    self.is_accept()
                    break

                self.data = self.s.recv(buffer_size)

                if len(self.data) == 0:
                    self.is_close()
                    break
                else:
                    self.is_recv()

    def is_accept(self):
        proxy = Proxy().start(forward_to[0], forward_to[1])
        conn, addr = self.server.accept()
        if proxy:
            print "Установлено соединение: %s" %  str(addr)
            self.input_list.append(conn)
            self.input_list.append(proxy)
            self.channel[conn] = proxy
            self.channel[proxy] = conn
        else:
            print "Соединение с разорвано: %s" % str(addr)
            conn.close()

    def is_close(self):
        print self.s.getpeername(), "Разьединение"
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        self.channel[out].close()
        self.channel[self.s].close()
        del self.channel[out]
        del self.channel[self.s]

    def is_recv(self):
        data = self.data
        self.channel[self.s].send(data)

if __name__ == '__main__':
        server = Server('', 9090)
        url = 'http://localhost:9090'
        webbrowser.open(url, new=0, autoraise=True)
        try:
            server.loop()
        except KeyboardInterrupt:
            print "Ctrl C - Cервер остановлен"
            sys.exit(1)