from bottle import route, run, template, response, request, abort, redirect
import urllib, re, httplib, urlparse
import xbmc
import xbmcgui
import urllib2
from pluginparser import PluginParser

directory_link = u'<li><a href=\"{0}\">{0}</a></li>\n'


def link(title):
    return u'<li><a href=\"{0}\">{1}</a></li>\n'.format(urllib.quote(title.encode('utf-8')), title)


@route('/')
def root():
    return link("Movies/"), link("TVShows/")


@route('/.nomedia')
def nomedia():
    abort(404)


@route('/Movies/')
def get_movies():
    movies = pp.get_movies()
    content = u""
    for movie in movies:
        content += link(u"{0} ({1}).avi".format(movie[0], movie[1])) if movie[1] else link(u"{0}.avi".format(movie[0]))
    return content


@route('/Movies/<movie>')
def get_movie(movie):
    xbmc.log('!!!!!!!!!!!!!!!')
    xbmc.log(request.method)
    label = movie.replace('.avi', '').split('(')
    title, year = label[0].strip().decode('utf8'), label[1].replace(')', '') if len(label) > 1 else ""
    url = pp.get_movie(title, year)
    if url is not None:
        if request.method != 'HEAD':
            redirect(url)
        else:
            abort(200)
    else:
        abort(404)

pp = PluginParser()
run(host='localhost', port=9909)
