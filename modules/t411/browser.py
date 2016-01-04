# -*- coding: utf-8 -*-

# Copyright(C) 2015 Julien Veyssier
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


from weboob.deprecated.browser import Browser, BrowserIncorrectPassword

from .pages.index import HomePage
from .pages.torrents import TorrentPage, SearchPage


__all__ = ['T411Browser']


class T411Browser(Browser):
    PAGES = {'https?://www.t411.in/?':  HomePage,
             'https?://www.t411.in/torrents/search/\?.*':    SearchPage,
             'https?://www.t411.in/torrents/[^/]*': TorrentPage,
            }

    def __init__(self, protocol, *args, **kwargs):
        self.PROTOCOL = protocol
        self.DOMAIN = 'www.t411.in'
        Browser.__init__(self, *args, **kwargs)

    def login(self):
        if not self.is_on_page(HomePage):
            self.location('%s://%s'%(self.PROTOCOL, self.DOMAIN), no_login=True)
        self.page.login(self.username, self.password)

        if not self.is_logged():
            raise BrowserIncorrectPassword()

    def is_logged(self):
        if not self.page:
            return False
        else:
            return self.page.is_logged()

    def home(self):
        return self.location('%s://%s/' % (self.PROTOCOL, self.DOMAIN))

    def iter_torrents(self, pattern):
        self.location('%s://%s/torrents/search/?search=%s&order=seeders&type=desc'%(
                                                            self.PROTOCOL,
                                                            self.DOMAIN,
                                                            pattern.encode('utf-8')))

        assert self.is_on_page(SearchPage)
        return self.page.iter_torrents()

    def get_torrent(self, fullid):
        self.location('%s://%s/t/%s'%(self.PROTOCOL,
                                             self.DOMAIN,
                                             fullid))

        assert self.is_on_page(TorrentPage)
        return self.page.get_torrent(fullid)