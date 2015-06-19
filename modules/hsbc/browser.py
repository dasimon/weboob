# -*- coding: utf-8 -*-

# Copyright(C) 2012-2013  Romain Bignon
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


import ssl
from datetime import timedelta

from weboob.tools.date import LinearDateGuesser
from weboob.exceptions import BrowserIncorrectPassword
from weboob.browser import LoginBrowser, URL, need_login
from .pages import AccountsPage, CBOperationPage, CPTOperationPage, LoginPage, AppGonePage


__all__ = ['HSBC']


class HSBC(LoginBrowser):
    BASEURL = 'https://client.hsbc.fr'
    app_gone = False

    connection =      URL(r'https://www.hsbc.fr/1/2/hsbc-france/particuliers/connexion', LoginPage)
    login =           URL(r'https://www.hsbc.fr/1/*', LoginPage)
    cptPage =         URL(r'/cgi-bin/emcgi.*\&Cpt=.*',
                          r'/cgi-bin/emcgi.*\&Epa=.*',
                          r'/cgi-bin/emcgi.*\&CPT_IdPrestation.*',
                          r'/cgi-bin/emcgi.*\&Ass_IdPrestation.*',
                          CPTOperationPage)
    cbPage =          URL(r'/cgi-bin/emcgi.*\&Cb=.*',
                          r'/cgi-bin/emcgi.*\&CB_IdPrestation.*',
                          CBOperationPage)
    appGone =     URL(r'/.*_absente.html',
                      r'/pm_absent_inter.html',
                        AppGonePage)
    accounts =        URL(r'/cgi-bin/emcgi', AccountsPage)

    def __init__(self, username, password, secret, *args, **kwargs):
        self.accounts_list = dict()
        self.secret = secret
        LoginBrowser.__init__(self, username, password, *args, **kwargs)

    def load_state(self, state):
        return

    def prepare_request(self, req):
        preq = super(HSBC, self).prepare_request(req)

        conn = self.session.adapters['https://'].get_connection(preq.url)
        conn.ssl_version = ssl.PROTOCOL_TLSv1

        return preq

    def do_login(self):
        self.connection.go()
        self.page.login(self.username)

        no_secure_key_link = self.page.get_no_secure_key()
        if not no_secure_key_link:
            raise BrowserIncorrectPassword()
        self.location(no_secure_key_link)

        self.page.login_w_secure(self.password, self.secret)
        self.page.useless_form()

        home_url = self.page.get_frame()
        if not home_url or not self.page.logged:
            raise BrowserIncorrectPassword()
        self.location(home_url)

    @need_login
    def get_accounts_list(self):
        self.update_accounts_list()
        for i,a in self.accounts_list.items():
            yield a

    @need_login
    def update_accounts_list(self):
        for a in list(self.accounts.stay_or_go().iter_accounts()):
            try:
                self.accounts_list[a.id]._link_id = a._link_id
            except KeyError:
                self.accounts_list[a.id] = a

    @need_login
    def get_history(self, account):
        if account._link_id is None:
            return

        if account._link_id.startswith('javascript'):
            raise NotImplementedError()

        self.location(self.accounts_list[account.id]._link_id)

        #If we relogin on hsbc, all link have change
        if self.app_gone:
            self.app_gone = False
            self.update_accounts_list()
            self.location(self.accounts_list[account.id]._link_id)


        if self.page is None:
            return

        if self.cbPage.is_here():
            guesser = LinearDateGuesser(date_max_bump=timedelta(45))
            return self.page.get_history(date_guesser=guesser)
        else:
            return self._get_history()

    def _get_history(self):
        for tr in self.page.get_history():
            yield tr
