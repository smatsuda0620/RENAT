# -*- coding: utf-8 -*-
#  Copyright 2018 NTT Communications
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# $Date: 2018-08-27 18:38:01 +0900 (Mon, 27 Aug 2018) $
# $Rev: 1238 $
# $Ver: $
# $Author: $

import os,time,re
import lxml.html
import Common
from WebApp import WebApp
from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.BuiltIn import RobotNotRunningError
# from Selenium2Library import Selenium2Library
from SeleniumLibrary import SeleniumLibrary
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType


class Samurai(WebApp):
    """ A library provides functions to control Samurai application

    The library utilize `Selenium2Library` and adds more functions to control
    Samurai application easily. Without other furthur mentions, all of the concepts
    of ``user``, ``user group`` are Samurai concepts. By default, RENAT will try to
    connec to all Samurai nodes defined in active ``local.yaml`` at the beginning of
    the test and disconnect from them at the end of the test automatically. Usually
    user does not need to use ``Connect All`` and ``Close`` explicitly.

    Currently, this module supposed that Samurai is used in Japanese locale.
    When Samurai module has error, it tried to make the last snapshot in
    ``result/selenium-screenshot-x.png``. Checking this capture will help to
    understand the reason of the error.

    Currently the module support Samurai 09/14/16

    Some keywords of [./Samurai.html|Samurai] is using ``xpath`` to identify
    elements. See `Selenium2Library` for more details about xpath.  

    See [./WebApp.html|WebApp] for common keywords of web applications and how
    to configure the ``local.yaml`` file.


    `Selenium2Library` keywords still could be used together within this library.
    See [http://robotframework.org/Selenium2Library/Selenium2Library.html|Selenium2Library] for more details.
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = Common.version()


    def __init__(self):
        super(Samurai,self).__init__()
        self._type = 'samurai'


    def connect_all(self):
        """ Connects to all applications defined in ``local.yaml``

        The name of the connection will be the same of the `webapp` name
        """

        num = 0
        if 'webapp' in Common.LOCAL and Common.LOCAL['webapp']:
            for entry in Common.LOCAL['webapp']:
                device = Common.LOCAL['webapp'][entry]['device']
                type = Common.GLOBAL['device'][device]['type']
                if type.startswith('samurai'):
                    num += 1
                    self.connect(entry,entry)
                    BuiltIn().log("Connected to %d applications" % num)
        else:
            BuiltIn().log("WARNING: No application to connect")



    def connect(self,app,name):
        """ Opens a web browser and connects to application and assigns a
        ``name``.
        
        If not defined in ``local.yaml`` those following key will have defaut
        values: 
        | browser     | firefox             | optional |
        | login_url   | /                   | optiona  | 
        | proxy:      |                     | optional |
        |     http:   10.128.8.210:8080     | optional |
        |     ssl:    10.128.8.210:8080     | optional | 
        |     socks:  10.128.8.210:8080     | optional |
        | profile_dir | ./config/samurai.profile | optional |  

        """
        if name in self._browsers:
            BuiltIn().log("Browser `%s` already existed" % name)
            return

        login_url       = '/'
        browser         = 'firefox'
        proxy = None
        capabilities    = None 
        ff_profile_dir  = None

        # collect information about the application
        app_info = Common.LOCAL['webapp'][app]
        if 'login_url' in app_info and app_info['login_url']:      
            login_url = app_info['login_url']
        if 'browser' in app_info and app_info['browser']:         
            browser  = app_info['browser']
        if 'profile_dir' in app_info and app_info['profile_dir']:     
            ff_profile_dir  = os.getcwd() + 'config/' + app_info['profile_dir']
        if 'proxy' in app_info and app_info['proxy']:
            proxy = Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            if 'http' in app_info['proxy']:
                proxy.http_proxy    = app_info['proxy']['http']
            # if 'socks' in app_info['proxy']:
            #    proxy.socks_proxy   = app_info['proxy']['socks']
            if 'ssl' in app_info['proxy']:
                proxy.ssl_proxy     = app_info['proxy']['ssl']
            if 'ftp' in app_info['proxy']:
                proxy.ftp_proxy     = app_info['proxy']['ftp']
            capabilities = webdriver.DesiredCapabilities.FIREFOX
            proxy.add_to_capabilities(capabilities)
       
        device = app_info['device']
        device_info = Common.GLOBAL['device'][device]
        ip = device_info['ip']
        # currently, only plain-text authentication is supported
        auth = {}
        auth['username']    = Common.GLOBAL['auth']['plain-text']['samurai']['user']
        auth['password']    = Common.GLOBAL['auth']['plain-text']['samurai']['pass']
        url = 'https://' + ip + '/' + login_url
    
        # open a browser
        self._driver.open_browser(url,browser,'_samurai_'+name,False,capabilities,ff_profile_dir)
        self._driver.wait_until_element_is_visible('name=username')
        
        # login
        self._driver.input_text('name=username', auth['username'])
        self._driver.input_text('name=password', auth['password'])
        self._driver.click_button('name=Submit')
        time.sleep(5)
    
        self._current_name = name
        browser_info = {}
        browser_info['capture_counter'] = 0
        browser_info['capture_format']  = 'samurai_%010d'
        browser_info['browser']         = browser
        self._browsers[name] = browser_info


    def login(self):
        """ Logs-in into the application

        User and password is set by the template and authentication methods in
        the master files
        """
        self.switch(self._current_name) 
        # login
        self._driver.input_text('name=username', auth['username'])
        self._driver.input_text('name=password', auth['password'])
        self._driver.click_button('name=Submit')
        
        BuiltIn().log("Logged-in the application")

    
    def logout(self):
        """ Logs-out the current application, the browser remains
        """
    
        self.switch(self._current_name) 
        self._driver.click_link('logout')
        self._driver.page_should_contain_image('image/logout_10.gif')

        BuiltIn().log("Exited samurai application")
    
    
    def switch(self,name):
        """ Switches the current browser to ``name``
        """
    
        self._driver.switch_browser('_samurai_' + name)
        self._current_name = name
        BuiltIn().log("Switched the current browser to `%s`" % name)

    
#    def set_count(self,value=0):
#        """ Sets current screen capture counter to ``value``
#        """
#        pass
    
    def close(self):
        """ Closes the current active browser
        """
    
        self.switch(self._current_name) 

        old_name = self._current_name
        self._driver.close_browser()
        del(self._browsers[old_name])
        if len(self._browsers) > 0:
            self._current_name = list(self._browsers.keys())[-1]
        else:
            self._current_name = None
    
        BuiltIn().log("Closed the browser '%s', current acttive browser is `%s`" % (old_name,self._current_name))
        return old_name
    
    
    def close_all(self):
        """ Closes all current opened applications
        """
        for entry in self._browsers:
            self.switch(entry)
            self._driver.close_browser()
        BuiltIn().log("Closed all Samurai applications")
    
    
    def left_menu(self,menu,locator=None, ignore_first_element=True):
        """ Chooses the left panel menu by its displayed name

        When ``locater`` is not null, the keyword will return a list of text
        attribute of all elements specified by the ``locator``. ``locator``
        could be a xpath or a predefined string.

        ``locator`` predefined strings are: ``MITIGATE_REALTIME``,
        ``MITIGATE_LIST``, ``DETECT_LIST``

        For example, a xpath ``//div[@id='infoareain2']/*//td[1]/a`` means the list of
        `link` of all elements in a 1st column of a table insides a ``div`` with
        id ``infoareain2``.
        
        Examples:
        | Samurai.`Left Menu` | Traffic |
        | Samurai.`Left Menu` | Detection |
        | Samurai.`Left Menu` | ポリシー管理 |
        | @{LIST}= | Samurai.`Left Menu` | Active Mitigation | //div[@id='infoareain2']/*//td[1]/a |
        """
        
        self.switch(self._current_name) 
        self._driver.select_window('MAIN')

        target = self._driver.get_webelement("xpath=//div[@class='submenu' and contains(.,'%s')]" % menu)
        id      = target.get_attribute('id')
        style   = target.get_attribute('style')
        if 'none' in style: 
            self._driver.execute_javascript("toggle_disp('%s','mitigation')" % id)
        self._driver.click_link(menu)
        self._driver.wait_until_element_is_visible("id=my_contents")
        # self._driver.wait_until_page_contains_element("infoareain")
        # get item list (the 1st meaningful column)

        item_list = []
        if locator:
            if locator == 'MITIGATE_LIST':
                xpath = "//div[@id='infoareain2']/*//td[1]/a"
            elif locator == 'MITIGATE_REALTIME':
                xpath = "//div[@id='infoareain']/*//td[1]/a"
            elif locator == 'DETECT_LIST':
                xpath = "//div[@id='infoareain']/*//td[1]/a"
            else:
                xpath = locator
            try:
                # item_list = map(lambda x:x.text,self._driver.get_webelements(xpath))
                item_list = [ x.text for x in self._driver.get_webelements(xpath) ]
            except Exception:
                pass 
        
        if ignore_first_element and len(item_list) > 0:
            BuiltIn().log("    Removed the 1st element in the list")
            item_list = item_list[1:]
        else:
            BuiltIn().log("    Found zero elements")

        BuiltIn().log("Chose menu `%s`" % menu)
        return item_list
  
 
    def start_mitigation(self,policy,prefix,comment="mitigation started by RENAT",device=None,force=False):
        """ Starts a mitigation with specific ``prefix``

        ``device`` is used for matching real device name configured by Samurai
        If ``force`` is ``TRUE`` then the keyword will fail if selected device
        does not contain ``device``

        Returns mitigation ``id`` and selected ``arbor device``

        Example:
        | ${id} |  ${device}=  |  Samurai.`Start Mitigation` | 211.1.12.1/32 | mitigation by RENAT | SP-A | ${TRUE} |
        """
        self.switch(self._current_name)

        self._driver.execute_javascript("toggle_disp('submenu3','mitigation')")
        self._driver.click_link("Active Mitigation")
        self._driver.wait_until_page_contains_element(u"//input[@value='Guard実行']")
        self._driver.click_button(u"//input[@value='Guard実行']")
        time.sleep(5)

        # IP input
        self._driver.select_window(u"title=Mitigation登録 IPアドレスの決定") 
        self._driver.select_from_list_by_label("gui_policy",policy)
        self._driver.input_text("name=address",prefix)
        self._driver.click_button(u"//input[@value='追加']")

        # device check
        # self._driver.page_should_not_contain_textfield(u"デバイスがありません")
        self._driver.element_should_not_be_visible(u"//span[contains(.,'有効な mitigation デバイスがありません')]")
        # self._driver.wait_until_page_contains_element(u"//*[text()[contains(.,'Mitigation ID')]]")

        # device selection
        title = self._driver.get_title()
        if title == u"Mitigation 登録 Mitigation Device決定" :
            if device:
                value = self._driver.get_value("//tr[contains(.,'%s')]/td[1]/input" % device)
                self._driver.select_radio_button("device_id",value)
            BuiltIn().log("Chose device `%s`" % device)
            self._driver.click_button(u"Mitigation Device 決定") 

        # comment input
        applied_device = self._driver.get_text(u"//td[.='Mitigation デバイス']/../td[2]")
        if force and device not in applied_device:
            raise("Selected device is `%s` which does not contain `%s`" % (applied_device,device))
       
        self._driver.input_text("name=comment",comment)
        # time.sleep(5)

        # execute
        self._driver.click_button(u"//input[@value='Mitigation 実行']")
        # time.sleep(5)
        id = self._driver.get_text("xpath=//*[text()[contains(.,'Mitigation ID')]]")
        search = re.search(".*:(.+) .*$", id)
        result = search.group(1)
        
        self._driver.click_button(u"//input[@value='閉じる']")
        # time.sleep(5)
        self._driver.select_window("title= Active Mitigation") 
        self._driver.reload_page()
        time.sleep(5)
        
        BuiltIn().log("Started a new mitigation id=`%s` by device `%s`" % (result,applied_device))
        return (result,applied_device)
 
    
    def stop_mitigation(self,id,stop_when_error=True):
        """ Stops a mitigation by its ID

            Example:
            | Samurai.`Stop Mitigation` | 700 |
        """

        self.switch(self._current_name)
        self.left_menu(u"Active Mitigation")
        self._driver.wait_until_page_contains(u"Active Mitigation")

        try:
            self._driver.select_window("title= Active Mitigation") 
            self._driver.reload_page()
            self._driver.wait_until_element_is_visible("infoarea")
            self._driver.click_button(u"//input[@onclick='delete_confirm(%s);']" % id)
            self._driver.confirm_action()
            self._driver.wait_until_element_is_visible(u"//span[contains(.,'削除を開始しました')]")
            BuiltIn().log("Stopped the mitigation id=%s" % id)
        except Exception as err:
            if stop_when_error:
                raise err
            else:
                BuiltIn().log_to_console("WARN: failed to stop mitgation %s but continue" % id)

    
    def add_user(self,group,**user_info): 
        """ Adds user to the current group
        ``user_info`` is a dictionary contains user information that has
        following keys: ``name``, ``password``, ``privilege`` and ``policy``

        ``privilege`` is existed privilege that has been created (e.g:
_system_admin_. 
        
        ``policy`` could be ``*`` for all current policies or a list of policy
        names that are binded to this user.

        ``group`` is the user group. ``Dot(.)`` means current group 

        Examples:
        | Samurai.`Add User` |  OCNDDoS | name=user000   |  password=Test12345678 |
        | ...                |  privilege=system_admin |  policy=*  |
        | Samurai.`Add User` |  OCNDDoS | username=user001   |  password=Test12345678 |
        | ...                |  privilege=system_admin |  policy=OCN11,OCN12  |

        """
        ### choose menu
        if group == '.':
            self.left_menu(u"ユーザ管理(自グループ)")
        else:
            self.left_menu(u"ユーザ管理(他グループ)") 
            self._driver.select_from_list_by_label("policy_group_id", group)
   
        self._driver.wait_until_page_contains_element(u"//input[@value='ユーザの追加']") 
        self._driver.click_button(u"//input[@value='ユーザの追加']")  
        self._driver.input_text("user_name",user_info['name'])
        self._driver.input_text("password1",user_info['password'])
        self._driver.input_text("password2",user_info['password'])
        self._driver.select_from_list("privilege_group_id",user_info["privilege"])
        policy = '' 
        if 'policy' in user_info:
            policy = user_info['policy']
            if policy == '*':
                self._driver.execute_javascript("change_all_check_box(document.FORM1.policy_id, true)")
            else:
                for entry in [x.strip() for x in policy.split(',')] :
                    self._driver.select_checkbox(u"//label[contains(.,'%s')]/../input" % entry) 
        #
        self._driver.click_button(u"//button[contains(.,'追加')]")
        self._driver.wait_until_page_contains_element(u"//span[contains(.,'ユーザを追加しました')]")
        BuiltIn().log("Added user `%s`" % user_info['name']) 
        

    def delete_user(self,group,*user_list):
        """ Deletes user from the user group
   
        ``group`` is the user group. And ``.`` means current group 
        Returns the number of deleted users

        Examples:
        | Samurai.`Delete User` | SuperGroup | user001 | user002 |
        | Samurai.`Delete User` | .          | user002 |
        """
        ### choose menu
        if group == '.':
            self.left_menu(u"ユーザ管理(自グループ)")
        else:
            self.left_menu(u"ユーザ管理(他グループ)") 
            self._driver.select_from_list_by_label("policy_group_id", group)
        
        self._driver.wait_until_page_contains(u"ユーザ管理")
        items,selected_items = self.select_items_in_table("//tr/td[3]","../td[1]",*user_list)
        if len(selected_items) > 0:
            # self._driver.click_button(u"//input[contains(@value,'削除')]")
            self._driver.click_button(u"//input[@value='削除']")
            # self.capture_screenshot()
            # self._driver.click_button(u"//input[@name='delete']")
            self._driver.confirm_action()
            # self.capture_screenshot()
            self._driver.wait_until_page_contains_element(u"//span[contains(.,'ユーザを削除しました')]")

        BuiltIn().log("Deleted %d user" % len(selected_items))
        return len(selected_items)    


    def make_item_map(self,xpath):
        """ Makes a item/webelement defined `xpath`
        
        The map is a dictionary from `item` to the `WebElement`
        Items name found by ``xpath`` are used as keys
        """
        BuiltIn().log("Making item map by xpath `%s`" % xpath)
        items = self._driver.get_webelements(xpath)
        item_map = {}
        for item in items:
            html = item.get_attribute('outerHTML')
            element = lxml.html.fromstring(html)
            text = element.text
            # using text_content in case of nothing found from text
            if not text: text = element.text_content()   
            key = text.replace(u'\u200b','').strip()
            item_map[key] = item

        BuiltIn().log("Made a map of %d items of from a table" % (len(items)))
        return item_map



#     def click_buttons_in_table(self,xpath,xpath2,*item_list):
#         """ Clicks buttons in Samurai table by xpath
#         
#         ``xpath`` points to the column that used as key and ``xpath2`` is the
#         relative xpath contains the button column.
# 
#         ``item_list`` is a list of item that need to check. Item in the list
#         could be a regular expresion with the format ``reg=<regular
#         expression``.
# 
#         The keyword is called with assuming that the table is already visible.
# 
#         Returns the tupple of all items and selected items
# 
#         *Note:* Non-width-space (\u200b) will be take care by the keyword.
#     
#         *Note:* if the first item_list is `*` then the keywork will try to click
#         a link named `すべてを選択`.
#         """
# 
#         BuiltIn().log("Trying to click %d buttons in the table" % len(item_list))
# 
#         item_map  = self.make_item_map(xpath)
#         if item_list[0] == '*':
#             self._driver.click_link(u"すべてを選択")
#             count = len(item_map)
#             result_map = item_map
#         else:  
#             key_list = [] 
#             for item in item_list:
#                 if item.startswith('reg='):
#                     pattern = item.split('=')[1]
#                     re_match = re.compile(pattern)
#                     key_list += [k for k in item_map if re_match.match(k)] 
#                 else:
#                     key_list.append(item)
# 
#             result_map = {} 
#             for k in key_list:
#                 if k in item_map: 
#                     BuiltIn().log("    Found item `%s`" % k)
#                     result_map[k] = item_map[k]
#         count = len(result_map)
#         # if count == 0:
#         #    raise Exception("ERROR: Could not found any item in the table")
#         for item in result_map:
#              = result_map[item].find_element_by_xpath(xpath2) 
#             self._driver.click_element(checkbox)
# 
#         BuiltIn().log("Selected %d/%d items in the table" % (len(result_map),len(item_map)))



    def select_items_in_table(self,xpath,xpath2,*item_list):
        """ Checks items in Samurai table by xpath
        
        ``xpath`` points to the column that used as key and ``xpath2`` is the
        relative xpath contains the target column.

        ``item_list`` is a list of item that need to check. Item in the list
        could be a regular expresion with the format ``reg=<regular
        expression>``.

        The keyword is called with assuming that the table is already visible.

        Returns the tupple of all items and selected items


        *Note:* Non-width-space (\u200b) will be take care by the keyword.
    
        *Note:* if the first item_list is `*` then the keywork will try to click
        a link named `すべてを選択`.
        """

        BuiltIn().log("Trying to select %d items from table" % len(item_list))

        # prepare 
        count = 0
        result_map = {} 
        action_map = {}
        item_map  = self.make_item_map(xpath)
       
        tmp = item_list[0].split(',') 
        if tmp[0] == '*':
            self._driver.click_link(u"すべてを選択")
            count = len(item_map)
            result_map = item_map
            for key in result_map:
                action_map[key] = tmp[1]
        else:  
            key_list = [] 
            action_list = []
            for item in item_list:
                tmp = item.split(':')
                if len(tmp) < 2: 
                    action = 'click'
                else:
                    action = tmp[1]
                if tmp[0].startswith('reg='):
                    pattern = tmp[0].split('=')[1]
                    re_match = re.compile(pattern)
                    for k in item_map:
                        if re_match.match(k):
                            key_list.append(k)
                            action_list.append(action)
                else:
                    key_list.append(tmp[0])
                    action_list.append(action)

            for k,action in zip(key_list,action_list):
                if k in item_map: 
                    BuiltIn().log("    Found item %s:%s" % (k,action))
                    result_map[k] = item_map[k]
                    action_map[k] = action
                    
        count = len(result_map)

        # 
        for item in result_map:
            target = result_map[item].find_element_by_xpath(xpath2) 
            action = action_map[item]
            if action == 'click':       
                self._driver.click_element(target)
                BuiltIn().log("    Clicked the item")
            if action == 'check':       
                if not target.is_selected():
                    self._driver.click_element(target)
                    BuiltIn().log("    Checked the item")
                else:
                    BuiltIn().log("    Item is already checked")
            if action == 'uncheck':       
                if target.is_selected():
                    self._driver.click_element(target)
                    BuiltIn().log("    Unchecked the item")
                else:
                    BuiltIn().log("    Item is already unchecked")

        BuiltIn().log("Set %d/%d items in the table" % (len(result_map),len(item_map)))
        return (item_map,result_map)



    def show_policy_basic(self,policy_name):
        """ Makes the virtual browser show basic setting of the policy `name`.

        A following Samurai.`Capture Screenshot` is necessary to capture  the
        result.
        """

        self.left_menu(u"ポリシー管理")
        self._driver.input_text("filter",policy_name)
        time.sleep(self._ajax_wait)
        item_map = self.make_item_map("//tr/td[3]/div")
        item = item_map[policy_name]
        button = item.find_element_by_xpath("../../td/div/input[@title='編集']")
        self._driver.wait_until_page_contains_element(button)
        self._driver.click_element(button)
        BuiltIn().log("Showed basic setting of the policy `%s`" % policy_name)

    
    def show_policy_mitigation(self,policy_name):
        """ Make the virtual browser show the mitigation setting of a policy

        A following Samurai.`Capture Screenshot` is necessary to capture  the
        result.
        """

        self.left_menu(u"ポリシー管理")
        self._driver.wait_until_page_contains_element("//input[@id='filter']")
        self._driver.input_text("filter",policy_name)
        time.sleep(self._ajax_wait)
        item_map = self.make_item_map("//tr/td[3]/div")
        item = item_map[policy_name]
        button = item.find_element_by_xpath("../../td/div/input[@title='編集']")
        self._driver.wait_until_page_contains_element(button)
        self._driver.click_element(button)
        self._driver.wait_until_page_contains(u"Mitigation設定")
        self._driver.click_element(u"//span[normalize-space(.)='Mitigation設定']")
        self._driver.wait_until_page_contains(u"Zone設定")

        BuiltIn().log("Showed mitigation setting of the policy `%s`" % policy_name)


    def show_policy_mo(self,policy_name):
        """ Make the virtual browser show the MO setting of a policy

        Automatically expand the MO section of other devices if necessary.

        A following Samurai.`Capture Screenshot` is necessary to capture  the
        result.

        """

        self.left_menu(u"ポリシー管理")
        self._driver.wait_until_page_contains_element("//input[@id='filter']")
        self._driver.input_text("filter",policy_name)
        time.sleep(self._ajax_wait)
        item_map = self.make_item_map("//tr/td[3]/div")
        item = item_map[policy_name]
        button = item.find_element_by_xpath("../../td/div/input[@title='編集']")
        self._driver.wait_until_page_contains_element(button)
        self._driver.click_element(button)
        self._driver.wait_until_page_contains(u"TMS MO設定")
        self._driver.click_element(u"//span[normalize-space(.)='TMS MO設定']")
        self._driver.wait_until_page_contains(u"TMS Managed Object設定")
        # not all device information is expanded yet
        mo_info = self._driver.get_webelements(u"//div[starts-with(@id,'mo_')]")
        for item in mo_info:
            id      = item.get_attribute('id')
            style   = item.get_attribute('style')
            if 'none' in style:
                self._driver.execute_javascript("toggle_disp('%s','%s_img')" % (id,id))

        BuiltIn().log("Showed mitigation setting of the policy `%s`" % policy_name)


    def show_policy_monitor(self,policy_name):
        """ Make a virtual browser show the mitigation setting of a policy

        A following Samurai.`Capture Screenshot` is necessary to capture  the
        result.
        """

        self.left_menu(u"ポリシー管理")
        self._driver.wait_until_page_contains_element("//input[@id='filter']")
        self._driver.input_text("filter",policy_name)
        time.sleep(self._ajax_wait)
        item_map = self.make_item_map("//tr/td[3]/div")
        item = item_map[policy_name]
        button = item.find_element_by_xpath("../../td/div/input[@title='編集']")
        self._driver.wait_until_page_contains_element(button)
        self._driver.click_element(button)
        self._driver.wait_until_page_contains(u"NW 監視設定")
        self._driver.click_element(u"//span[normalize-space(.)='NW 監視設定']")
        self._driver.wait_until_page_contains(u"NW 監視設定")

        BuiltIn().log("Showed NW monitoring setting of the policy `%s`" % policy_name)

       
    def edit_policy(self,**policy):
        """ Edits a Samurai policy

        ``policy`` contains information about the policy. See `Add Policy` for
        more details about ``policy`` format
        """ 

        policy_name = policy['name']

        # basic
        changing = False
        if any(x in policy for x in ['basic_cidr_list','basic_option_filter','basic_direction']):
            BuiltIn().log("### Basic setting ###")
            changing = True
            self.show_policy_basic(policy_name)
        if 'basic_cidr_list' in policy:
            cidr_list = [x.strip() for x in policy['basic_cidr_list'].split(',')]
            self._driver.input_text("detection_cidr", '\n'.join(cidr_list))
        if 'basic_option_filter' in policy:
            self._driver.input_text("option_filter", policy['basic_option_filter'])
            time.sleep(self._ajax_wait)
        if 'basic_direction' in policy:
                if policy['basic_direction'].lower() in ['incoming', 'in'] :
                    basic_direction = 'Incoming'
                else:
                    basic_direction = 'Outgoing'
                self._driver.select_from_list_by_label("direction",basic_direction)
        if changing:
            self._driver.click_button("submitbutton")
            self._driver.wait_until_page_contains(u"ポリシー情報を変更しました")

        # mitigation
        changing = False
        self.show_policy_mitigation(policy_name)
        if 'mitigation_zone_prefix' in policy:
            changing = True
            self._driver.input_text("prefix0",policy['zone_prefix'])
        if 'mitigation_thr_bps' in policy:
            changing = True
            self._driver.input_text("thr_bps",policy['mitigation_thr_bps'])
        if 'mitigation_thr_pps' in policy:
            changing = True
            self._driver.input_text("thr_pps",policy['mitigation_thr_pps'])
        if 'mitigation_mo_enabled' in policy:
            changing = True
            if policy['mitigation_mo_enabled']:
                mitigation_mo_enabled = 'true'
            else:
                mitigation_mo_enabled = 'false'
            self._driver.select_radio_button("arbor_mo_enable",mitigation_mo_enabled)
        if 'mitigation_device_list' in policy:
            changing = True
            device_list = [x.strip() for x in policy['mitigation_device_list'].split(',')]
            table_map,selected_table_map = self.select_items_in_table('//tr/td[2]','../td[1]', *device_list)
        if changing:
            self._driver.click_button("submitbutton")
            self._driver.wait_until_page_contains(u"Mitigation情報を変更しました")

        # only Samurai > 16 has this panel
        changing = False
        if any(x in policy for x in \
            ['nw_monitor_gre1','nw_monitor_gre2','nw_monitor_ce1','nw_monitor_ce2','nw_monitor_p1','nw_monitor_pe2']):
            changing = True
            self.show_policy_monitor(policy_name)

        if ('nw_monitor_gre1' in policy) or ('nw_monitor_gre2' in policy):
            gre_elements = self._driver.get_webelements('//input[contains(@id,"gre_addr")]')
            self._driver.input_text(gre_elements[0],policy['nw_monitor_gre1'])
            self._driver.input_text(gre_elements[1],policy['nw_monitor_gre2'])
        if ('nw_monitor_pe1' in policy) or ('nw_monitor_ce1' in policy):
            pe_elements = self._driver.get_webelements('//select[contains(@name,"pe_id")]')
            self._driver.select_from_list_by_label(pe_elements[0],policy['nw_monitor_pe1'])
            self._driver.select_from_list_by_label(pe_elements[1],policy['nw_monitor_pe2'])
        if ('nw_monitor_ce1' in policy) or ('nw_monitor_ce2' in policy):
            ce_elements = self._driver.get_webelements('//input[contains(@id,"ce_addr")]')
            self._driver.input_text(ce_elements[0],policy['nw_monitor_ce1'])
            self._driver.input_text(ce_elements[1],policy['nw_monitor_ce2'])
        if changing:
            self._driver.click_button("submitbutton")
            self._driver.wait_until_page_contains(u"NW監視情報を変更しました")

        BuiltIn().log("Changed setting for the policy `%s`" % policy_name)


    def add_policy(self,**policy):
        """ Adds a new Samurai policy
        
        ``policy`` is a map containing the below information to create the new policy. 
        | *key*     | *meaning*             | *mandatory* | *sample* |  
        | name      | name of the policy    | yes | _test001_  | 
        | basic_alias     | alias name of the policy |   | _test001_  | 
        | basic_port_id   | another alias |  | |
        | basic_facing   | ``customer`` or ``backbone`` | | _customer_ |
        | basic_intf_list | list of router and interface pair, separated by comma | yes | _10.128.18.31:xe-0/0/0.1_ | 
        | basic_cidr_list | list of CIDR separate by comma | | |
        | basic_option_filter | optinal filter | | |
        | basic_direction | direction of the traffic (``incoming`` or ``outgoing``) | | _Incoming_ |
        | traffic_enabled | Enable traffic monitoring or not | yes | _${TRUE}_ or _${FALSE}_ | 
        | detection_enabled | Enable detection or not | yes | _${TRUE}_ or _${FALSE}_ |
        | mitigation_enabled | Enable Mitigation or not | yes | _${TRUE}_ or _${FALSE}_ |
        | mitigation_zone_name | Name of the zone for mitigation | | _zone001_ |
        | mitigation_zone_prefix | Prefixes that could mitigate | | _1.1.1.1/32_ |
        | mitigation_thr_bps | Upper limit (bps) | | _800,000,000_ | 
        | mitigation_thr_pps | Upper limit (pps) | | _54,000,000_ |
        | mitigation_auto_enabled | Enable automitgation or not | | _${TRUE}_ or _${FALSE}_ |
        | mitigation_auto_level | Automitgation level  | | 0:overLow 1:overMedium 2:High |
        | mitigation_auto_time | Automitigation detect attack time (min) | | default is 15 |
        | mitigation_mo_enabled | Using Arbor TMS MO or not | yes | _${TRUE}_ or _${FALSE}_ |
        | mitigation_auto_stop_enabled | Enable automitgation stop or not | | _${TRUE}_ or _${FALSE}_ |
        | mitigation_auto_stop_level | Automitgation level  | | 0:overLow  2:High |
        | mitigation_auto_stop_time | Automitigation stop detect attack time (min) | | default is 15 |
        | mitigation_device_list | Devices used for TMS, separated by comma | | _ArborSP-A_ |
        | mitigation_mo_name     | MO name, separated by comma | | _OCN12(ALU)_LOOSE_ |
        | mitigation_comm_list   | commna separated peer/community list |   | _1.10(180.0.1.10)/2914:666,1.11(180.0.1.11)/2914:777_ |
        | nw_monitor_gre1 | 1st GRE address for NW monitor |  | _210.0.1.1_ |
        | nw_monitor_gre2 | 2nd GRE address for NW monitor |  | _210.0.1.1_ |
        | nw_monitor_ce1  | 1st CE address for NW monitor  |  | _210.0.1.2_ |
        | nw_monitor_ce2  | 2nd CE address for NW monitor  |  | _210.0.1.2_ |
        | nw_monitor_pe1  | 1st PE for NW monitor (list)   |  | _edge01hige-MX2020-15(118.23.176.244)_ |
        | nw_monitor_pe2  | 2nd PE for NW monitor (list)   |  | _edge01hige-MX2020-15(118.23.176.244)_ |
        | event_name  | name of the message event to make |  | _info1_ |
        | event_addr  | address to send the events      |  |  _user@mail.com_ |
        | view_group  | user group that could view this policy, separated by comma | yes | _SuperGroup,test_group_007_ |

        Example:
        | Samurai.`Switch`      | samurai-1 | |
        | Samurai.`Add Policy`  | name=${POLICY_NAME}        | basic_alias=${POLICY_NAME} |
        | ...                   | basic_facing=customer      | basic_intf_list=10.128.18.31:xe-0/0/0.1 |
        | ...                   | basic_cidr_list=1.1.1.0/24 | basic_direction=incoming |
        | ...                   | traffic_enabled=${TRUE} |
        | ...                   | detection_enabled=${TRUE} | 
        | ...                   | mitigation_zone_name=test_zone001 | mitigation_zone_prefix=1.1.1.1/32 |
        | ...                   | mitigation_device_list=ArborSP-A,ArborSP-B |
        | ...                   | mitigation_mo_enabled=${TRUE} |
        | ...                   | mitigation_mo_name=N000000012_LOOSE |
        | ...                   | mitigation_comm_list=1.10(180.0.1.10)/2914:666,1.11(180.0.1.11)/2914:777 |
        | ...                   | event_name=test |        event_addr=user@mail.com |
        | ...                   | view_group=SuperGroup |
        """

        # menu
        self.left_menu(u"ポリシー管理")

        traffic_enabled         = 'false'
        detection_enabled       = 'false'
        mitigation_enabled      = 'false'
        mitigation_mo_enabled   = 'false'

        # basic 
        BuiltIn().log("### Basic setting ###")
        self._driver.click_button(u"//input[@value='ポリシーの追加']")
        self._driver.input_text("policy_name", policy['name'])
        if 'basic_alias' in policy: 
            self._driver.input_text("alias_name1", policy['basic_alias'])
        else:
            self._driver.input_text("alias_name1", policy['name'])
        if 'basic_port_id' in policy:
            self._driver.input_text("alias_name2", policy['basic_port_id'])
        if 'basic_facing' in policy:
            if policy['basic_facing'] == 'customer':
                customer_flag = 'true'
            else:
                customer_flag = 'false'
            self._driver.select_from_list_by_value("customer_flag",customer_flag)
        intf_list = [x.strip() for x in policy['basic_intf_list'].split(',')]
        self._driver.input_text("detection_interface", '\n'.join(intf_list))
        if 'basic_cidr_list' in policy:
            cidr_list = [x.strip() for x in policy['basic_cidr_list'].split(',')]
            self._driver.input_text("detection_cidr", '\n'.join(cidr_list))
        if 'basic_option_filter' in policy: 
            self._driver.input_text("option_filter", policy['basic_option_filter'])
            time.sleep(self._ajax_wait)

        basic_direction = 'Outgoing'
        if 'basic_direction' in policy and policy['basic_direction'].lower() in ['incoming', 'in'] :
                basic_direction = 'Incoming'
        self._driver.select_from_list_by_label("direction", basic_direction) 
        self._driver.click_button("submitbutton")
        self._driver.wait_until_page_contains(u"ポリシーを追加しました。")
        self._driver.click_button(u"//button[.='進む']") 

        # traffic setting
        BuiltIn().log("### Traffic setting ###")
        if policy['traffic_enabled']:   traffic_enabled = 'true'
        if traffic_enabled == 'true':
            self._driver.select_radio_button("traffic_enabled",traffic_enabled) 
        self._driver.click_button(u"//button[.='次へ']")

        # detection setting
        BuiltIn().log("### Detection setting ###")
        detection_enabled = 'false'
        if 'detection_enabled' in policy and policy['detection_enabled']:
                detection_enabled = 'true'
        self._driver.select_radio_button("misuse_enabled_flag",detection_enabled) 
        self._driver.click_button(u"//button[.='次へ']")

        # mitigation
        if policy['mitigation_enabled']: mitigation_enabled = 'true'
        if mitigation_enabled == 'true':
            BuiltIn().log("### Mitigation setting ###")
            self._driver.click_button("zoneaddbutton")
            self._driver.input_text("zonename0",policy['mitigation_zone_name'])
            self._driver.input_text("prefix0",policy['mitigation_zone_prefix'])
            if policy['mitigation_mo_enabled']:         mitigation_mo_enabled = 'true'
            self._driver.select_radio_button("arbor_mo_enable",mitigation_mo_enabled)

            device_list = [x.strip() for x in policy['mitigation_device_list'].split(',')]
            table_map,selected_table_map = self.select_items_in_table("//tr/td[2]","../td[1]", *device_list)
            if 'mitigation_thr_bps' in policy:
                self._driver.input_text("thr_bps",policy['mitigation_thr_bps'])
            if 'mitigation_thr_pps' in policy :
                self._driver.input_text("thr_pps",policy['mitigation_thr_pps'])

            mitigation_auto_enabled = 'false'
            if 'mitigation_auto_enabled' in policy and policy['mitigation_auto_enabled']:
                    mitigation_auto_enabled = 'true'
            self._driver.select_radio_button("auto_enable",mitigation_auto_enabled)

            mitigation_auto_level = "1" # default
            if 'mitigation_auto_level' in policy:
                if policy['mitigation_auto_level'].lower() in ['0','low']:
                    mitigation_auto_level = '0'
                if policy['mitigation_auto_level'].lower() in ['2','high']:
                    mitigation_auto_level = '2'
            self._driver.select_radio_button("attack_lv",mitigation_auto_level)

            mitigation_auto_time = "15"
            if "mitigation_auto_time" in policy:
                mitigation_auto_time = policy['mitigation_auto_time']
            self._driver.input_text("attack_ln",mitigation_auto_time)

            mitigation_auto_stop_enabled = 'false'
            if 'mitigation_auto_stop_enabled' in policy and policy['mitigation_auto_stop_enabled']:
                    mitigation_auto_stop_enabled = 'true'
            self._driver.select_radio_button("auto_stop",mitigation_auto_stop_enabled)

            mitigation_auto_stop_level = "2" # default
            if 'mitigation_auto_stop_level' in policy:
                if policy['mitigation_auto_stop_level'].lower() in ['0','low']:
                    mitigation_auto_stop_level = '0'
            self._driver.select_radio_button("stop_lv",mitigation_auto_stop_level)

            mitigation_auto_stop_time = "15"
            if "mitigation_auto_stop_time" in policy:
                mitigation_auto_stop_time = policy['mitigation_auto_stop_time']
            self._driver.input_text("stop_ln",mitigation_auto_stop_time)
        
       
            if 'mitigation_comm_list' in policy: 
                BuiltIn().log("### Diversion Community setting ###")
                for entry in [x.strip() for x in policy['mitigation_comm_list'].split(',')]:
                    (peer,comm) = [x.strip() for x in entry.split('/')]
                    if peer in table_map:
                        item = table_map[peer] 
                        check =         item.find_element_by_xpath("../td[1]")
                        comm_input =    item.find_element_by_xpath("../td[3]/input")
                        self._driver.select_checkbox(check)
                        self._driver.input_text(comm_input,comm) 
        self._driver.click_button(u"//button[.='次へ']")
      
        # MO
        # When peers have been configured, there are no places to set community
        if mitigation_mo_enabled == 'true':
            BuiltIn().log("### MO setting ###")
            self._driver.wait_until_page_contains_element(u"//b[.='TMS Managed Object設定']")
            mo_name = policy['mitigation_mo_name']
            # not all device information is expanded yet
            mo_info = self._driver.get_webelements(u"//div[starts-with(@id, 'mo_')]")
            for item in mo_info:
                id      = item.get_attribute('id')
                style   = item.get_attribute('style')
                if 'none' in style:
                    self._driver.execute_javascript("toggle_disp('%s','%s_img')" % (id,id))

            items = self._driver.get_webelements(u"//tr/td[2][.='%s']/../td[1]" % mo_name)
            for k in items: self._driver.click_element(k)
            self._driver.click_button(u"//button[.='次へ']")

        # Add more setting for Samurai16
        BuiltIn().log("### Monitoring setting ###")
        nw_monitor = int(self._driver.get_matching_xpath_count(u"//div[contains(.,'NW 監視設定')]"))
        if nw_monitor > 0:
            if ('nw_monitor_gre1' in policy) or ('nw_monitor_gre2' in policy):
                gre_elements = self._driver.get_webelements('//input[contains(@id,"gre_addr")]')
                self._driver.input_text(gre_elements[0],policy['nw_monitor_gre1'])
                self._driver.input_text(gre_elements[1],policy['nw_monitor_gre2'])
            if ('nw_monitor_pe1' in policy) or ('nw_monitor_ce1' in policy):
                pe_elements = self._driver.get_webelements('//select[contains(@name,"pe_id")]')
                self._driver.select_from_list_by_label(pe_elements[0],policy['nw_monitor_pe1'])
                self._driver.select_from_list_by_label(pe_elements[1],policy['nw_monitor_pe2'])
            if ('nw_monitor_ce1' in policy) or ('nw_monitor_ce2' in policy):
                ce_elements = self._driver.get_webelements('//input[contains(@id,"ce_addr")]')
                self._driver.input_text(ce_elements[0],policy['nw_monitor_ce1'])
                self._driver.input_text(ce_elements[1],policy['nw_monitor_ce2'])
        
            self._driver.click_button(u"//button[.='次へ']")

        # Event
        BuiltIn().log("### Event setting ###")
        if 'event_name' in policy:
            self._driver.wait_until_page_contains_element(u"//input[@value='メール通知の追加']")
            self._driver.click_button(u"//input[@value='メール通知の追加']")
            self._driver.input_text("user_name",policy['event_name'])
            self._driver.input_text("mail_address",policy['event_addr'])
            self._driver.click_button(u"//button[.='追加']")
            self._driver.wait_until_page_contains(u"メール通知設定を追加しました")

        # View setting
        BuiltIn().log("### View setting ###")
        view_group_list = [x.strip() for x in policy['view_group'].split(',')]
        self.change_policy_view_group(policy['name'],*view_group_list)

        BuiltIn().log("Added a Samurai policy named `%s`" % policy['name'])
         


    def change_policy_view_group(self,name,*group_name):
        """ Changes the groups that could see this policy

        ``name`` is the policy name. ``group_name`` is a list of policies

        Example:
        | Samurai.`Change Policy View Group` | super_admin | test_group001 | 
        """
       
        BuiltIn().log("Changing Policy View Group of the policy `%s`" % name) 

        self.left_menu(u"ポリシー管理")
        self._driver.input_text("filter",name)
        time.sleep(self._ajax_wait)
        item_map = self.make_item_map("//tr/td[3]/div")
        item = item_map[name]
        button = item.find_element_by_xpath("../../td/div/input[@title='編集']")
        self._driver.click_element(button)

        # view ( not check the case when there are multi groups over 1 page)
        self._driver.click_element(u"//span[normalize-space(.)='閲覧設定']")
        #
        self._driver.wait_until_page_contains_element("//tr/td[2]")

        item_map,result_map = self.select_items_in_table("//tr/td[2]","../td[1]",*group_name)
        for item in result_map:
            link = result_map[item].find_element_by_xpath(u"..//a[text()='すべてを選択']")
            self._driver.click_element(link)

        self._driver.click_button(u"//button[.='変更']")
        self._driver.click_element(u"//span[contains(.,'閲覧設定を変更しました')]")

        # list current policies
        self.left_menu(u"ポリシー管理")
        BuiltIn().log("Changed the groups that could see this policy")


    def delete_policy(self,*policy_names):
        """ Deletes poilcies by their names

        Returned the number of deleted users

        *Notes:* If the policy does not exists, the system will not report any error.

        Examples:
        | Samurai.`Delete Policy` | test001 | test002 |
        """
        # menu
        BuiltIn().log("Deleting policies")
        self.left_menu(u"ポリシー管理")
    
        all_items,selected_items = self.select_items_in_table('//tr/td[3]/div','../../td[1]',*policy_names)
        if len(selected_items) > 0:
            self._driver.click_button(u"//input[@value='削除']") 
            self._driver.confirm_action()
            self._driver.wait_until_page_contains_element(u"//span[contains(.,'ポリシーを削除しました')]")

        BuiltIn().log("Deleted %d/%d policies" % (len(selected_items),len(policy_names)))
        return len(selected_items)


    def add_policy_group(self,group_name,policy_list="*",limit_bps="4000000000",limit_pps="2700000"):
        """ Add a new policy group

        ``group_name`` is the name of the new group. ``policy_list`` is a comma
        separated of existed policy that should be bound to this policy. An
        asterisk for this parameter (``*``) means `all of the existed policy`.
        ``limit_bps`` and ``limit_pps`` are the mitigation capacity threshold of
        this group.
        """
        # menu
        self.left_menu(u"ポリシーグループ管理")
    
        self._driver.click_button(u"//input[@value='ポリシーグループの追加']")
        self._driver.input_text("policy_group_name",group_name)

        count = 0 
        if policy_list:
            if policy_list == "*" :
                item_list = self._driver.get_webelements("xpath=//*[starts-with(@for,'label')]")
                count = len(item_list)
                self._driver.click_link(u"すべてを選択") 
            else :
                item_list = [x.strip() for x in policy_list.split(',')] 
                for item in item_list:
                    self._driver.click_element(u"//input[@id=//label[.='%s']/@for]" % item)
                count = len(item_list)

            self._driver.click_button(u"//input[@value='追加']")
            self._driver.page_should_contain_element(u"//span[contains(.,'ポリシーグループを追加しました')]")

        self.left_menu(u"ポリシーグループ管理")
        BuiltIn().log("Added policy group '%s' and bound it to %d policies" % (group_name,count))


    def delete_policy_group(self,*group_list):
        """ Deletes policy groups
    
        Returns the number of deleted policy groups
        Example:
        | Samurai.`Delete Policy Group` | test_group001 | test_group002 |
        """
        # menu
        self.left_menu(u"ポリシーグループ管理")
        all_items,selected_items = self.select_items_in_table("//tr/td[3]","../td[1]",*group_list)
        if len(selected_items) > 0:
            self._driver.click_button(u"//input[contains(@value,'削除')]")
            self._driver.confirm_action()
            self._driver.wait_until_page_contains_element(u"//span[contains(.,'ポリシーグループを削除しました')]")

        BuiltIn().log("Deleted %d policy groups" % len(selected_items))
        return len(selected_items)
        

    def click_all_elements(self,xpath):
        """ Click all element in current page defined by ``xpath``

        Returns the number of elements that have been clicked
        """
        items = self._driver.get_webelements(xpath)
        for item in items: self._driver.click_element(item)

        BuiltIn().logs("Clicked %d items defined by xpath=`%s`" % (len(items),xpath))
        return len(items)


    def show_detail_mitigation(self,id):
        """ Shows detail information of a mitigation
        """
        self.left_menu(u"Active Mitigation")
        self._driver.wait_until_page_contains(u"Active Mitigation")
        self._driver.click_link('%s' % id)
        self._driver.select_window(u"title=リアルタイム詳細")
        self._driver.wait_until_page_contains(u"適用フィルタ情報")
        
        BuiltIn().log("Showed detail of mitigation id `%s`" % id)


    def close_window():
        """ Closes the current window
        """
        self._driver.close_window()
        time.sleep(2)
        BuiltIn().log("Closed the current window")


    def select_window(self,title):
        """ Selects a window by its title
        """
        # self.switch(self._current_name)
        self._driver.select_window(u"title=%s" % title) 
        self._driver.wait_until_page_contains(title)
        
        BuiltIn().log("Selected window `%s`" % title)


    def get_mitigation_list(self,status=u'実行中'):
        """ Gets current mitigation list

        Return current active mitgation name, ID and the number of them

        Example:
        | ${MITI}  ${IDS}  ${NUM}=   |     Samurai.`Get Mitigation List` |
        """
        result = []
        result_ids = []
        self.left_menu(u"Active Mitigation")
        time.sleep(2)
        try:
            item_list = self._driver.get_webelements("//div[@id='infoareain']//tr/td[2]") 
            for item in item_list:
                item_status = item.find_element_by_xpath(u'../td[5]').text
                # BuiltIn().log_to_console(item_status)
                if item.text != u'ポリシー' and item_status == status:
                    result.append(item.text)
                    result_ids.append(item.find_element_by_xpath(u'../td[1]').text)

            BuiltIn().log("Got %d active mitigations has status %s" % (len(result),status))
        except Exception as err: 
            BuiltIn().log("No active mitigations found")
        return result,result_ids,len(result)

    
    def edit_mitigation_controller(self,controller,**config):
        """ Change the setting of the mitigation control
    
        - ``control``: name of the mitigation controller
        - ``config``: configuration need to be changed. Currently only
          ``tms_group`` is configurable with the following format:
            ``groupname1:action1,groupname2:action2``. ``groupname`` is
            currently set TMS group name and action could be `click`,`check` or `uncheck`.


        Example:
        | Samurai.`Edit Mitigation Controller` |  controller=vSP-A | tms_group=Logical0_SOCN_IPv4:uncheck |
             
        """
        self.left_menu(u"Mitigation Device管理") 
        self._driver.wait_until_page_contains_element("//div[@id='dataTable']")
        edit_button = self._driver.get_webelement(u"//tr/td/div[.='%s']/../../td[2]/div/input[@name='change']" % controller)
        self._driver.click_button(edit_button)
        time.sleep(2)
        self._driver.wait_until_page_contains_element("//button[@id='submitbutton']")
        if 'tms_group' in config:
            tmp = config['tms_group'].split(':')
            check_box = self._driver.get_webelement(u"//tr/td[.='%s']/../td[1]//input" % tmp[0])
            if (tmp[1] == 'check' and not check_box.is_selected()) or (tmp[1] == 'uncheck' and check_box.is_selected()):
                self._driver.click_element(check_box)
                
            
        self._driver.click_button("submitbutton")
        self._driver.wait_until_page_contains(u"Mitigationデバイス情報を変更しました")
            
