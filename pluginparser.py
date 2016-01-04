import xbmc, xbmcgui
import urllib
import json
from dbworker import DBWorker
import urllib2
import re

class PluginParser:
    movies = []
    tvshows = []
    plugin_name = 'plugin.video.fs.ua'
    dbworker = DBWorker()

    # def __init__(self):
        
    
    # def __del__(self):
    def get_original_title_and_year(self, root):
        pattern = ".+video%2F.+%2F([^-]+).+"
        id = re.match(pattern, root).groups()[0]
        xbmc.log(id)

        url = "http://fs.to/video/films/iframeplayer/{0}"
        headers = { 'X-Requested-With' : 'XMLHttpRequest' }
        req = urllib2.Request(url.format(id), None, headers)
        response = urllib2.urlopen(req)
        try:
            data = json.loads(response.read())
            original_title = data['coverData']['title_origin']
            year = data['coverData']['year'][0]['title']
        except ValueError:
            return (None, None)
        return (original_title, year)

    def get_movies_from_source(self):
        request = '{ "jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "plugin://plugin.video.fs.ua/?section=video&page=%d&type=favorites&mode=readfavorites&subsection=film"},"id": 1 }'
        page = 0
        while True:
            response = json.loads(xbmc.executeJSONRPC(request % page))
            if 'error' in response.keys():
                break
            for file in response['result']['files']:
                #xbmc.log(str(file))
                if not file['label'].startswith('['):
                    root = file['file']
                    title, year = self.get_original_title_and_year(root)
                    label = file['label'].split(' / ')[-1]
                    if title is None:
                        title = label.split('(')[0].replace(')', '')
                    if year is None:
                        year = label.split('(')[1] if len(label.split('('))>1 else ""
                    self.movies.append({'title':title, 'year':year, 'root':root})
            page += 1

    def get_movie_links_from_root(self, root):
        request = '{ "jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s"},"id": 1 }'
        links = {}
        response = json.loads(xbmc.executeJSONRPC(request % root))
        xbmc.log(str(response))
        xbmc.log(request % root)
        lang_dirs = response['result']['files']
        for lang_dir in lang_dirs:
            if lang_dir['file'].endswith('quality=None'):
                lang = lang_dir['label']
                quality_dirs = json.loads(xbmc.executeJSONRPC(request % lang_dir['file']))['result']['files']
                qualities = {}
                for quality_dir in quality_dirs:
                    if quality_dir['filetype'] == 'directory':
                        qualities[quality_dir['label']] = quality_dir['file']
                links[lang] = qualities
        return links

    def get_direct_link_from_source(self, title, year, source):
        request = '{ "jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s"},"id": 1 }'
        response = json.loads(xbmc.executeJSONRPC(request % source))
        xbmc.log(str(response))
        xbmc.log(request % source)

        direct_link = response['result']['files'][0]['file']
        if urllib.urlopen(direct_link).getcode() == 200:
            self.dbworker.update_link(title, year, self.plugin_name, direct_link, source)
        return direct_link

    def get_movies(self):
        self.get_movies_from_source()
        xbmc.log(str(self.movies))
        for movie in self.movies:
            self.dbworker.add_movie(movie['title'], movie['year'], self.plugin_name, movie['root'])

        return self.dbworker.read_movies(self.plugin_name)

    def get_movie(self, title, year):
        movie = self.dbworker.get_movie_link(title, year, self.plugin_name)
        if movie is None:
            return None

        if movie['link'] != '':
            if urllib.urlopen(movie['link']).getcode() == 200:
                return movie['link']
            else:
                return self.get_direct_link_from_source(title, year, movie['source'])
        else:
            links = self.get_movie_links_from_root(movie['root'])
            lang = links.keys()[xbmcgui.Dialog().select(title, links.keys())]
            source = links[lang].values()[xbmcgui.Dialog().select(lang, links[lang].keys())]
            return self.get_direct_link_from_source(title, year, source)