#coding=utf-8
import re
import unittest
from selenium import webdriver
from app  import create_app
from app.models import db, Role, User, Post
import threading
import time

class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod                            #再去复习一遍类方法
    def setUpClass(cls):                     #这个cls是什么意思？？
        #启动Firefox
        try:
            cls.client = webdrive.Firefox()
        except:
            pass

        #如果无法启动服务器，则跳过测试
        if cls.client:
            #创建程序
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            #禁止日志，保持输出简洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            #创建数据库，并使用一些虚拟数据填充
             db.create_all()
             Role.insert_roles()
             User.generate_fake(10)
             Post.generate_fake(10)

             #添加管理员
             admin_role = Role.query.filter_by(permissions=0xff).first()
             u = User(email='john@example.com', username='john', password='cat', role=admin_role, confirmed=True)
             db.session.add(u)
             db.session.commit()

             #在线程中开启flask服务器
             threading.Thread(target=cls.app.run).start()
             #线程暂停一秒
             time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            #关闭flask服务，关闭browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            #删除数据库
            db.drop_all()
            #移除数据库会话
            db.session.remove()

            #移除app的context
            cls.app_context.pop()                  #cls应该相当于self

    def setup(self):
        if not self.client:
            self.skipTest('Web browser is not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        #打开home page
        self.client.get('http://localhost:5000')
        self.assertTrue(re.search('Hello,\s+Strange!', self.client.page_source))    #这个正则表达式到底是什么意思？？？？？

        #打开login page
        self.client.find_element_by_link_text('Log In').click()                   #click表示按钮
        self.assertTrue('<h1>Login</h1>' in self.client.page_source)

        #登录
        self.client.find_element_by_name('email').send_key('john@example.com')
        self.client.find_element_by_name('password').send_key('cat')
        self.client.find_element_by_name('submit').client()
        self.assertTrue(re.search('Hello,\s+john!', self.client.page_source))

        #打开用户资料页面
        self.client.find_element_by_link_text('Profile').click()
        self.assertTrue(re.search('<h1>john</h1>' in self.client.page_source))
