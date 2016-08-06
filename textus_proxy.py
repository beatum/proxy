#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Created by Ivan Semernyakov 06.08.16
"""
import SocketServer
import requests
import sys
import webbrowser
from bs4 import BeautifulSoup

# change if need
url = 'http://habrahabr.ru/company/yandex/blog/258673/'

try:
    r = requests.get(url)
    if not r.encoding == "UTF-8":
        r.encoding = 'UTF-8'
        print('SET NEW ENCODING', r.encoding)
    html = r.content  # возвращаем бинарные данные
except requests.exceptions.RequestException as e:
    print('RequestException:', e)
    sys.exit(1)
finally:
    r.close()

# передаём бинарные данные в soup, для обработки
soup = BeautifulSoup(html, 'html.parser')

# выбираем тег с основным контентом, в этой строке
# вы можете указать другие данные например, attrs={'id': 'some_id'},
# или tag = soup.body.find_all('div')
# в зависимости от содержания парсируемой страницы
tag = soup.body.find(attrs={'class': 'content html_format'})

all_string = []

for string in tag.stripped_strings:
    # убираем лишнее
    all_string.append(string)

string = "".join(all_string)

# разбиваем текст по словам, и через каждое 6-ое слово вставляем символ TM
formatted = ['{} {}'.format(x, '<sup>TM</sup>' if (enum % 6) == 0 else '')
             for enum, x in enumerate(string.split(), start=1)]

# возвращаем полученны результат в структуру документа
tag.string = " ".join(formatted)


class EchoHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print("Connected from", self.client_address)
        while True:
            data = self.request.recv(8192)
            if not data:
                break
            self.request.sendall(str(soup))
        self.request.close()
        print("Disconnected from", self.client_address)


if __name__ == '__main__':
    srv = SocketServer.ThreadingTCPServer(('localhost', 8080), EchoHandler)
    srv.allow_reuse_address = True
    url = 'http://localhost:8080'
    # открываем новую вкладку в браузере
    webbrowser.open(url, new=0, autoraise=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(1)
        print("Ctrl C - Cервер остановлен")
