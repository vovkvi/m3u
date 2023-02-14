#!/usr/bin/env python3
# coding : utf-8
'''
Класс для работы с плейлистами *.m3u и аудиофайлами.

Реализованы следующие функции:

-- проверка на работоспособность URL потоков в плейлисте;
-- создание плейлиста для папки с аудио файлами (mp3, m4a, flac);
-- копирование фалов на Mp3 плеер в порядке сортировки по дате
   изменения файла, т.е. копируються файлы на устройство начиная с
   новых и заканчивая старыми. Это обусловлено тем, что мой плеер
   сортирует песни в плейлисте не по имени файла, а как раз таки
   по дате их изменения (плеер Transcend MP330).

 (c) Vitalii Vovk, 2023
'''
import os
import shutil
import pathlib
import urllib.request


class M3U:

    def __init__(self):
        self.playlists = ('.m3u','.m3u8')
        self.songs = ('.mp3','.m4a','.flac')


    def get_valid_filename(self,src_str:str,rm_str:str ="%:/,\\[]<>*?") -> str:
        '''
        Форматирует строку в соответствии с допустимыми символами
        которые могут использоваться для названия файлов в системе

        :param:
            src_str (str) : исходная строка
            rm_str  (str) : строка с символами, которые будут удалены
                            из исходной строки

        :return:
            str : возвращает строку без недопустимых символов
        '''
        src_str = ''.join([c for c in src_str if c not in rm_str])
        return src_str.replace(' ', '-')


    def get_file_list(self,source:str,filetype:str='p') -> list:
        '''
        Получает список аудио файлов или плейлистов в указанной директории

        :param:
            source   (str) : полный путь к директории с файлами
            filetype (str) : тип искомых файлов:
                             p - файлы плейлистов;
                             s - аудио файлы.

        :return:
            list : возвращает список объектов Path
        '''
        files = []
        if filetype is None or filetype not in ('p','s'):
            print(f'[-] Не верно задан тип искомых файлов ({filetype})')
            return
        exts = self.playlists if filetype == 'p' else self.songs
        pth = pathlib.Path(source)
        if pth.is_dir():
            for ext in exts:
                files.extend(pth.glob(f'*{ext}'))
            if len(files) == 0:
                print(f'[-] Плейлисты не найдены в директории {source}')
        elif pth.is_file():
            if pth.suffix in exts:
                files = [source]
            else:
                print(f'[-] Файл не является плейлистом.')
        else:
            print(f'[-] Не верно задан путь ({source}).')
        return files


    def check_stream(self,url:str,timeout:int=10) -> bool:
        '''
        Проверяет работоспособность потока

        :param:
            url     (str) : ссылка на поток
            timeout (int) : время ожидания ответа от сервера

        :return:
            bool : равен ли код ответа сервера 200
        '''
        try:
            code = urllib.request.urlopen(url,timeout=timeout).getcode()
        except:
            code = 0
        return code == 200


    def check_urls(self,source:str, timeout:int=10):
        '''
        Проверяет активны ли ссылки на потоки в указанном плейлисте
        и выводит информационные сообщения если ссылка "битая".

        :param:
            source  (str) : полный путь к плейлисту
            timeout (int) : время ожидания ответа от сервера
        '''
        for f in self.get_file_list(source):
            print(f'Проверка файла "{f}" ...')
            with open(str(f), 'r', encoding='utf-8', errors='ignore') as pls:
                lines = pls.readlines()
            for i,v in enumerate(lines):
                if v.startswith('http') or v.startswith('rtps'):
                    if not self.check_stream(v, timeout):
                        print(f'[-] Ссылка на "{lines[i-1].split(",")[-1]}" не активна."')


    def create_playlist(self,source:str):
        '''
        Создает плейлист (*.m3u) для файлов указанной директории

        :param:
             source (str) : полный путь к директории с файлами
        '''
        pth = pathlib.Path(source)
        songs = self.get_file_list(source, 's')
        sort_songs = sorted(songs, key = lambda s: s.stat().st_mtime)
        sort_songs = [(i.name.replace(i.suffix, ''),i) for i in sort_songs]
        playlist_name = self.get_valid_filename(f'{pth.name}.m3u')
        with open(playlist_name, 'w+', encoding='utf-8', errors='ignore') as pls:
            pls.write('#EXTM3U\n')
            for i,s in enumerate(reversed(sort_songs)):
                pls.write(f'#EXTINF:{i},{s[0]}\n{s[1]}\n')
        print(f'Плейлист для директории "{pth.resolve()}" создан успешно.')


    def copy_sorted_songs(self,src_path:str,dest_path:str):
        '''
        Копирует аудио файлы на mp3 плеер в порядке соответствующем дате
        изменения файлов, т.е. копирование начиная с более новых файлов
        и заканчивая старыми.

        :param:
            src_path  (str) : полный путь к директории-источнику
            dest_path (str) : полный путь к директории-премнику
        '''
        if not os.path.exists(dest_path):
            os.mkdir(dest_path)
        pth = pathlib.Path(src_path)
        songs = self.get_file_list(src_path, 's')
        sort_songs = sorted(songs, key = lambda s: s.stat().st_mtime)
        print(f'Начинаю копированрие файлов в "{pth.resolve()}":')
        for s in sort_songs:
            dest_file = f'{dest_path}//{s.name}.{s.suffix}'
            print(f'Копирую файл: {s.name} ...')
            if os.path.exists(dest_file):
                continue
            shutil.copyfile(s.resolve(), dest_file)
        print('Копирование завершено.')
