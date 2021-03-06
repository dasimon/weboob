# -*- coding: utf-8 -*-

# Copyright(C) 2016       Baptiste Delpey
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

import re

from weboob.browser.pages import HTMLPage, LoggedPage, pagination
from weboob.browser.elements import ListElement, ItemElement, method, TableElement, SkipItem
from weboob.browser.filters.standard import CleanText, CleanDecimal, Field, TableCell, Regexp, Date, AsyncLoad, Async, Eval
from weboob.browser.filters.html import Attr, Link
from weboob.capabilities.bank import Account, Investment
from weboob.capabilities.base import NotAvailable
from weboob.tools.capabilities.bank.transactions import FrenchTransaction
from weboob.tools.value import Value
from weboob.tools.date import parse_french_date
from weboob.exceptions import BrowserQuestion, BrowserIncorrectPassword


class BrowserAuthenticationCodeMaxLimit(BrowserIncorrectPassword):
    pass

class IncidentPage(HTMLPage):
    pass

class AuthenticationPage(HTMLPage):
    def authenticate(self):
        self.logger.info('Using the PIN Code %s to login', self.browser.config['pin_code'].get())
        self.logger.info('Using the auth_token %s to login', self.browser.auth_token)

        form = self.get_form()
        form['otp_confirm[otpCode]'] = self.browser.config['pin_code'].get()
        form['flow_secureForm_instance'] = self.browser.auth_token
        form['otp_confirm[validate]'] = ''
        form['flow_secureForm_step'] = 2
        form.submit()

        self.browser.auth_token = None

    def sms_first_step(self):
        """
        This function simulates the registration of a device on
        boursorama two factor authentification web page.
        @param device device name to register
        @exception BrowserAuthenticationCodeMaxLimit when daily limit is consumed
        """
        form = self.get_form()
        form.submit()

    def sms_second_step(self):
        # <div class="form-errors"><ul><li>Vous avez atteint le nombre maximal de demandes pour aujourd&#039;hui</li></ul></div>
        error = CleanText('//div[has-class("form-errors")]')(self.doc)
        if len(error) > 0:
            raise BrowserIncorrectPassword(error)

        form = self.get_form()
        self.browser.auth_token = form['flow_secureForm_instance']
        form['otp_prepare[receiveCode]'] = ''
        form.submit()

        raise BrowserQuestion(Value('pin_code', label='Enter the PIN Code'))


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile(u'^CHQ\. (?P<text>.*)'),        FrenchTransaction.TYPE_CHECK),
                (re.compile('^(ACHAT|PAIEMENT) CARTE (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^(PRLV SEPA |PRLV |TIP )(?P<text>.*)'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^RETRAIT DAB (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^VIR( SEPA)? (?P<text>.*)'), FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^AVOIR (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) (?P<text>.*)'),   FrenchTransaction.TYPE_PAYBACK),
                (re.compile('^REM CHQ (?P<text>.*)'), FrenchTransaction.TYPE_DEPOSIT),
               ]


class VirtKeyboardPage(HTMLPage):
    symbols = {'0': 'gGCQotikafNwAAASxJREFUWMPtlrtKxEAUhicGJYVoYSMsRFNoYS9YipWNhWDpW/gCW1go+AqWVr6AIGi7nYWkiiBEUCxW2Q',
               '1': 'gGCQsrej4LQwAAAJRJREFUWMPt07ENAjEMhWE7do+EYANoKGhuBZZgTyp0DESBRJs4sWmYABLpTnrfANYvWyYCAPiZmU3u/o',
               '2': 'gGCQUMQbeTpgAAAlhJREFUWMPtl79rFEEUx++SE3+E+Au0NhYG/wQRUgha2YqFhZg0ghDQQgTBOoWRdEYbU0SLVRFB7JQN4g',
               '3': 'gGCQY6pSBV/AAAAh1JREFUWMPtlz2IE0EUx98bEy4fch6IMSpXiWDhB1ZqZ2FpaSmIYOF1lndWQUG46rAR7OwELTwUwTKVaJ',
               '4': 'sCBjU5C9zLzAAAAaVJREFUWMPtlzFLAzEYhpOgVKsgjoI4Skf/hZubs9V/oD9BXARB/QW1g0sXBx3EQRQEN8WhYHGSaimlQi',
               '5': 'gGCQgI83Qp8gAAAflJREFUWMPtmM9rE1EQx+fFbEhIoJQiUtCLKdKDCN71IBavPRXBs4L1D/DgyVuv/gNiD4ISrCB6KPiDtO',
               '6': 'gGCQgltqt1hwAAAqRJREFUWMPtl71rFEEYh+fUg8MYTUDwA22MQWwM2FgKKlgogpUW+gdooQkIRgs9EBu19A/wAwQLEQxKDA',
               '7': 'gGCQkLc2ZJCQAAAptJREFUWMPtlz9oFEEUxnfPRENE0ymIYCUWohYKkl4LCyFaWAi2NkFI0ErQXCE2URREFKsoKhIQ/INgLP',
               '8': 'gGCQkzW2TxlwAAAj9JREFUWMPtmD9oFEEUxuf2EA4haKOIRtHSItqKYCGCksJGEEyhWIudiO2VksZGG60uaOE1Aa8wXUwjQq',
               '9': 'gGCQobRfwKrgAAAzBJREFUWMPtl02oFEcQx8f18yASBE00qAcTgmDQQyAaPAgSCXqLAQkSJJCDYoKXQPArvPhxUhH14i05GD',}

    def get_code(self, password):
        code = ''
        for i, d in enumerate(password):
            if i > 0:
                code += '|'
            code += Attr(self.doc.xpath('//span[img[contains(@src, "%s")]]' % self.symbols[d]), 'data-matrix-key')(self)
        return code


class LoginPage(HTMLPage):
    def login(self, login, password):
        form = self.get_form()
        code = self.browser.keyboard.open().get_code(password)
        form['form[login]'] = login
        form['form[fakePassword]'] = len(password) * '•'
        form['form[password]'] = code
        form.submit()


class AccountsPage(LoggedPage, HTMLPage):
    ACCOUNT_TYPES = {u'Comptes courants':      Account.TYPE_CHECKING,
                        u'Comptes épargne':       Account.TYPE_SAVINGS,
                        u'Comptes bourse':        Account.TYPE_MARKET,
                        u'Assurances Vie':        Account.TYPE_LIFE_INSURANCE,
                        u'Mes crédits':           Account.TYPE_LOAN,
                    }

    @method
    class iter_accounts(ListElement):
        item_xpath = '//table[@class="table table--accounts"]/tr[has-class("table__line--account") and count(descendant::td) > 1]'

        class item(ItemElement):
            klass = Account

            load_details = Field('_link') & AsyncLoad

            obj_id = Async('details') & Regexp(CleanText('//h3[has-class("account-number")]'), r'(\d+)')
            obj_label = CleanText('.//a[@class="account--name"] | .//div[@class="account--name"]')
            obj_balance = CleanDecimal('.//a[has-class("account--balance")]', replace_dots=True)
            obj_currency = FrenchTransaction.Currency('.//a[has-class("account--balance")]')
            obj_valuation_diff = Async('details') & CleanDecimal('//li[h4[text()="Total des +/- values"]]/h3 |\
                        //li[span[text()="Total des +/- values latentes"]]/span[has-class("overview__value")]', replace_dots=True, default=NotAvailable)
            obj_coming = Async('details') & CleanDecimal(u'//li[h4[text()="Mouvements à venir"]]/h3', replace_dots=True, default=NotAvailable)
            obj__card = Async('details') & Attr('//a[@data-modal-behavior="credit_card-modal-trigger"]', 'href', default=NotAvailable)
            obj__holder = None
            obj__webid = None

            def obj_type(self):
                return self.page.ACCOUNT_TYPES.get(CleanText('./preceding-sibling::tr[has-class("list--accounts--master")]//h4')(self), Account.TYPE_UNKNOWN)

            def obj__link(self):
                link = Attr('.//a[@class="account--name"] | .//a[2]', 'href', default=NotAvailable)(self)
                if not self.page.browser.webid:
                    self.page.browser.webid = re.search('\/([^\/|?|$]{32})(\/|\?|$)', link).group(1)
                return link

            # We do not yield other banks accounts for the moment.
            def validate(self, obj):
                return not Async('details', CleanText(u'//h4[contains(text(), "Établissement bancaire")]'))(self)


class HistoryPage(LoggedPage, HTMLPage):
    @method
    class iter_history(ListElement):
        item_xpath = '//ul[has-class("list__movement")]/li[div and not(contains(@class, "summary")) \
                                                               and not(contains(@class, "graph")) \
                                                               and not (contains(@class, "separator"))]'

        class item(ItemElement):
            klass = Transaction

            obj_id = Attr('.', 'data-id', default=NotAvailable) or Attr('.', 'data-custom-id')
            obj_raw = Transaction.Raw(CleanText('.//div[has-class("list__movement__line--label__name")]'))
            obj_date = Date(Attr('.//time', 'datetime'))
            obj_amount = CleanDecimal('.//div[contains(@class, "amount")]', replace_dots=True)
            obj_category = CleanText('.//div[contains(@class, "desc")]')


            def obj_rdate(self):
                s = Regexp(Field('raw'), ' (\d{2}/\d{2}/\d{2}) | (?!NUM) (\d{6}) ', default=NotAvailable)(self)
                if not s:
                    return Field('date')(self)
                s = s.replace('/', '')
                return Date(dayfirst=True).filter('%s%s%s%s%s' % (s[:2], '-', s[2:4], '-', s[4:]))

            def obj__is_coming(self):
                return len(self.xpath(u'.//span[@title="Mouvement à débit différé"]'))


class Myiter_investment(TableElement):
    item_xpath = '//table[contains(@class, "operations")]/tbody/tr'
    head_xpath = '//table[contains(@class, "operations")]/thead/tr/th'

    col_value = u'Valeur'
    col_quantity = u'Quantité'
    col_unitprice = u'Px. Revient'
    col_unitvalue = u'Cours'
    col_valuation = u'Montant'
    col_diff = u'+/- latentes'


class Myitem(ItemElement):
    klass = Investment

    obj_quantity = CleanDecimal(TableCell('quantity'), default=NotAvailable)
    obj_unitprice = CleanDecimal(TableCell('unitprice'), replace_dots=True, default=NotAvailable)
    obj_unitvalue = CleanDecimal(TableCell('unitvalue'), replace_dots=True, default=NotAvailable)
    obj_valuation = CleanDecimal(TableCell('valuation'), replace_dots=True, default=NotAvailable)
    obj_diff = CleanDecimal(TableCell('diff'), replace_dots=True, default=NotAvailable)

    def obj_label(self):
        return CleanText().filter((TableCell('value')(self)[0]).xpath('.//a'))

    def obj_code(self):
        return CleanText().filter((TableCell('value')(self)[0]).xpath('./span')) or NotAvailable


class MarketPage(LoggedPage, HTMLPage):
    @pagination
    @method
    class iter_history(TableElement):
        item_xpath = '//table/tbody/tr'
        head_xpath = '//table/thead/tr/th'

        col_label = 'Nature'
        col_amount = 'Montant'
        col_date = 'Date d\'effet'

        next_page = Link('//li[@class="pagination__next"]/a')

        class item(ItemElement):
            klass = Transaction

            obj_date = Date(CleanText(TableCell('date')), dayfirst=True)
            obj_raw = Transaction.Raw(CleanText(TableCell('label')))
            obj_amount = CleanDecimal(TableCell('amount'), replace_dots=True, default=NotAvailable)
            obj__is_coming = False

            def parse(self, el):
                if el.xpath('./td[2]/a'):
                    m = re.search('(\d+)', el.xpath('./td[2]/a')[0].get('data-modal-alert-behavior', ''))
                    if m:
                        self.env['account']._history_pages.append((Field('raw')(self),\
                                                                self.page.browser.open('%s%s%s' % (self.page.url.split('mouvements')[0], 'mouvement/', m.group(1))).page))
                        raise SkipItem()

    @method
    class iter_investment(Myiter_investment):
        class item (Myitem):
            def obj_unitvalue(self):
                return CleanDecimal(replace_dots=True, default=NotAvailable).filter((TableCell('unitvalue')(self)[0]).xpath('./span[not(@class)]'))

    def get_transactions_from_detail(self, account):
        for label, page in account._history_pages:
            amounts = page.doc.xpath('//span[contains(text(), "Montant")]/following-sibling::span')
            if len(amounts) == 3:
                amounts.pop(0)
            for table in page.doc.xpath('//table'):
                t = Transaction()

                t.date = Date(CleanText(page.doc.xpath('//span[contains(text(), "Date d\'effet")]/following-sibling::span')), dayfirst=True)(page)
                t.label  = label
                t.amount = CleanDecimal(replace_dots=True).filter(amounts[0])
                amounts.pop(0)
                t._is_coming = False
                t.investments = []
                for tr in table.xpath('./tbody/tr'):
                    i = Investment()
                    i.label = CleanText().filter(tr.xpath('./td[1]'))
                    i.vdate = Date(CleanText(tr.xpath('./td[2]')), dayfirst=True)(tr)
                    i.unitvalue = CleanDecimal(replace_dots=True).filter(tr.xpath('./td[3]'))
                    i.quantity = CleanDecimal(replace_dots=True).filter(tr.xpath('./td[4]'))
                    i.valuation = CleanDecimal(replace_dots=True).filter(tr.xpath('./td[5]'))
                    t.investments.append(i)

                yield t


class SavingMarketPage(MarketPage):
    @pagination
    @method
    class iter_history(TableElement):
        item_xpath = '//table/tbody/tr'
        head_xpath = '//table/thead/tr/th'

        col_label = u'Opération'
        col_amount = u'Montant'
        col_date = u'Date opération'
        col_vdate = u'Date Val'

        next_page = Link('//li[@class="pagination__next"]/a')

        class item(ItemElement):
            klass = Transaction

            obj_label = CleanText(TableCell('label'))
            obj_amount = CleanDecimal(TableCell('amount'), replace_dots=True)
            obj__is_coming = False

            def obj_date(self):
                return parse_french_date(CleanText(TableCell('date'))(self))

            def obj_vdate(self):
                return parse_french_date(CleanText(TableCell('vdate'))(self))

    @method
    class iter_investment(TableElement):
        item_xpath = '//table/tbody/tr[count(descendant::td) > 4]'
        head_xpath = '//table/thead/tr[count(descendant::th) > 4]/th'

        col_label = u'Fonds'
        col_code = u'Code Isin'
        col_unitvalue = u'Valeur de la part'
        col_quantity = u'Nombre de parts'
        col_vdate = u'Date VL'

        class item(ItemElement):
            klass = Investment

            obj_label = CleanText(TableCell('label'))
            obj_code = CleanText(TableCell('code'))
            obj_unitvalue = CleanDecimal(TableCell('unitvalue'), replace_dots=True)
            obj_quantity = CleanDecimal(TableCell('quantity'), replace_dots=True)
            obj_valuation = Eval(lambda x, y: x * y, Field('quantity'), Field('unitvalue'))
            obj_vdate = Date(CleanText(TableCell('vdate')), dayfirst=True)


class AsvPage(MarketPage):
    @method
    class iter_investment(Myiter_investment):
        col_vdate = u'Date de Valeur'

        class item(Myitem):
            obj_vdate = Date(CleanText(TableCell('vdate')), dayfirst=True)


class AccbisPage(LoggedPage, HTMLPage):
    def populate(self, accounts):
        cards = []
        for account in accounts:
            for li in  self.doc.xpath('//li[@class="nav-category"]'):
                title = CleanText().filter(li.xpath('./h3'))
                for a in li.xpath('./ul/li//a'):
                    label = CleanText().filter(a.xpath('.//span[@class="nav-category__name"]'))
                    balance_el = a.xpath('.//span[@class="nav-category__value"]')
                    balance = CleanDecimal(replace_dots=True, default=NotAvailable).filter(balance_el)
                    if 'CARTE' in label and balance:
                        acc = Account()
                        acc.balance = balance
                        acc.label = label
                        acc.currency = FrenchTransaction.Currency().filter(balance_el)
                        acc._link = Link().filter(a.xpath('.'))
                        acc._history_page = acc._link
                        acc.id = acc._webid = Regexp(pattern='([^=]+)$').filter(Link().filter(a.xpath('.')))
                        acc.type = Account.TYPE_CARD
                        if not acc in cards:
                            cards.append(acc)
                    elif account.label == label and account.balance == balance:
                        if not account.type:
                            account.type = AccountsPage.ACCOUNT_TYPES.get(title, Account.TYPE_UNKNOWN)
                        if account.type == Account.TYPE_LOAN:
                            account._history_page = None
                        elif account.type in (Account.TYPE_LIFE_INSURANCE, Account.TYPE_MARKET):
                            account._history_page = re.sub('/$', '', Link().filter(a.xpath('.')))
                        elif '/compte/cav' in a.attrib['href'] or not 'titulaire' in self.url:
                            account._history_page = self.browser.other_transactions
                        else:
                            account._history_page = self.browser.budget_transactions
                        account._webid = Attr(None, 'data-account-label').filter(a.xpath('.//span[@class="nav-category__name"]'))
        accounts.extend(cards)


class LoanPage(LoggedPage, HTMLPage):
    pass


class ErrorPage(HTMLPage):
    pass
