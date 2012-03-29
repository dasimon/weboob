# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Julien Veyssier
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


from decimal import Decimal
import re

from weboob.tools.browser import BasePage
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction

class LoginPage(BasePage):
    def login(self, login, passwd):
        self.browser.select_form(nr=0)
        self.browser['_cm_user'] = login
        self.browser['_cm_pwd'] = passwd
        self.browser.submit()

class LoginErrorPage(BasePage):
    pass

class InfoPage(BasePage):
    pass

class TransfertPage(BasePage):
    pass

class UserSpacePage(BasePage):
    pass

class AccountsPage(BasePage):
    def get_list(self):
        l = []

        for tr in self.document.getiterator('tr'):
            first_td = tr.getchildren()[0]
            if first_td.attrib.get('class', '') == 'i g' or first_td.attrib.get('class', '') == 'p g':
                account = Account()
                account.label = u"%s"%first_td.find('a').text.strip().lstrip(' 0123456789')
                account._link_id = first_td.find('a').get('href', '')
                if account._link_id.startswith('POR_SyntheseLst'):
                    continue

                account.id = first_td.find('a').text.split(' ')[0]+first_td.find('a').text.split(' ')[1]

                if not account.id.isdigit():
                    continue

                s = tr.getchildren()[2].text
                if s.strip() == "":
                    s = tr.getchildren()[1].text
                balance = u''
                for c in s:
                    if c.isdigit() or c == '-':
                        balance += c
                    if c == ',':
                        balance += '.'
                account.balance = Decimal(balance)
                l.append(account)
            #raise NotImplementedError()
        return l

    def next_page_url(self):
        """ TODO pouvoir passer à la page des comptes suivante """
        return 0

class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^VIR(EMENT)? (?P<text>.*)'), FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^PRLV (?P<text>.*)'),        FrenchTransaction.TYPE_ORDER),
                (re.compile('^(?P<text>.*) CARTE \d+ PAIEMENT CB (?P<dd>\d{2})(?P<mm>\d{2}) ?(.*)$'),
                                                          FrenchTransaction.TYPE_CARD),
                (re.compile('^RETRAIT DAB (?P<dd>\d{2})(?P<mm>\d{2}) (?P<text>.*) CARTE \d+'),
                                                          FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^CHEQUE$'),                  FrenchTransaction.TYPE_CHECK),
                (re.compile('^COTIS\.? (?P<text>.*)'),    FrenchTransaction.TYPE_BANK),
                (re.compile('^REMISE (?P<text>.*)'),      FrenchTransaction.TYPE_DEPOSIT),
               ]


class OperationsPage(BasePage):
    def get_history(self):
        index = 0
        for tr in self.document.getiterator('tr'):
            tds = tr.getchildren()
            if len(tds) < 4:
                continue

            if tds[0].attrib.get('class', '') == 'i g' or \
               tds[0].attrib.get('class', '') == 'p g' or \
               tds[0].attrib.get('class', '').endswith('_c1 c _c1'):
                operation = Transaction(index)
                index += 1

                # Find different parts of label
                parts = []
                if len(tds[-3].findall('a')) > 0:
                    parts = [a.text.strip() for a in tds[-3].findall('a')]
                else:
                    parts.append(tds[-3].text.strip())
                    if tds[-3].find('br') is not None:
                        parts.append(tds[-3].find('br').tail.strip())

                # To simplify categorization of CB, reverse order of parts to separate
                # location and institution.
                if parts[0].startswith('PAIEMENT CB'):
                    parts.reverse()

                operation.parse(date=tds[0].text,
                                raw=u' '.join(parts))

                if tds[-1].text is not None and len(tds[-1].text) > 2:
                    s = tds[-1].text.strip()
                elif tds[-1].text is not None and len(tds[-2].text) > 2:
                    s = tds[-2].text.strip()
                else:
                    s = "0"
                balance = u''
                for c in s:
                    if c.isdigit() or c == "-":
                        balance += c
                    if c == ',':
                        balance += '.'
                operation.amount = Decimal(balance)
                yield operation

    def next_page_url(self):
        """ TODO pouvoir passer à la page des opérations suivantes """
        return 0
