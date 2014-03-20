# -*- coding: utf-8 -*-

# Copyright(C) 2013-2014 Florent Fourcot
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

from weboob.tools.browser import BrowserBanned
from weboob.tools.browser2.page import HTMLPage, LoggedPage, method, ListElement, ItemElement
from weboob.tools.browser2.filters import Env, CleanText, CleanDecimal, Field, Attr, Filter, Time, Date, Link
from weboob.capabilities.bill import Subscription, Detail
from datetime import datetime


__all__ = ['LoginPage', 'HomePage', 'HistoryPage', 'BillsPage', 'ErrorPage']


class ErrorPage(HTMLPage):
        pass


class LoginPage(HTMLPage):

    def login(self, login, password):
        captcha = self.doc.xpath('//label[@class="label_captcha_input"]')
        if len(captcha) > 0:
            raise BrowserBanned('Too many connections from you IP address: captcha enabled')

        xpath_hidden = '//form[@id="newsletter_form"]/input[@type="hidden"]'
        hidden_id = Attr(xpath_hidden, "value")(self.doc)
        hidden_name = Attr(xpath_hidden, "name")(self.doc)

        form = self.get_form(xpath="//form[@class='form-detail']")
        form['login[username]'] = login
        form['login[password]'] = password
        form[hidden_name] = hidden_id
        form.submit()


class InsertX(Filter):
    """
    Insert a list of Filters inside a string
    """
    def __init__(self, selectors, string):
        self.string = string
        self.selectors = selectors

    def map_filter(self, selector, item):
        if isinstance(selector, basestring):
            value = item.xpath(selector)
        elif callable(selector):
            value = selector(item)
        else:
            value = selector
        return value

    def __call__(self, item):
        myliste = [self.map_filter(selector, item) for selector in self.selectors]
        return self.filter(tuple(myliste))

    def filter(self, mytupple):
        return self.string % mytupple


class HomePage(LoggedPage, HTMLPage):

    @method
    class get_list(ListElement):
        item_xpath = '.'

        class item(ItemElement):
            klass = Subscription

            obj_id = CleanText('//span[@class="welcome-text"]/b')
            obj__balance = CleanDecimal(CleanText('//span[@class="balance"]'), replace_dots=False)
            obj_label = InsertX([Field('id'), Field('_balance')], u"Poivy - %s - %s €")


class HistoryPage(LoggedPage, HTMLPage):

    @method
    class get_calls(ListElement):
        item_xpath = '//table/tbody/tr'

        def next_page(self):
            link_path = "//div[@class='date-navigator center']/span/a"
            text = CleanText(link_path)(self.page.doc)
            if "Previous" in text:
                link = Link(link_path)(self.page.doc)
                return link
            return

        class item(ItemElement):
            klass = Detail

            obj_id = None
            obj_datetime = Env('datetime')
            obj_price = CleanDecimal('td[7]', replace_dots=False, default=0)
            obj_currency = u'EUR'
            obj_label = InsertX([CleanText('td[3]'), CleanText('td[4]'),
                                 CleanText('td[5]'), CleanText('td[6]')],
                                u"%s from %s to %s - %s")

            def parse(self, el):
                mydate = Date(CleanText('td[1]'))(el)
                mytime = Time(CleanText('td[2]'))(el)

                self.env['datetime'] = datetime.combine(mydate, mytime)


#TODO
class BillsPage(HTMLPage):
    pass
