#coding=utf-8
import re
import unittest
from app import create_app, db
from app.models import User, Role
from flask import url_for


class FlaskClientTestCase(unittest.TestCase):
   def setup(self):
       self.app = create_app('testing')
       self.app_context = self.app.app_context()
       self.app_context.push()
       db.create_all()
       Role.insert_roles()
       self.client = self.app.test_client(use_cookie = True)    #测试用例中的实例变量

   def tearDown(self):
       db.session.remove()
       db.drop_all()
       self.app_context.pop()

   def test_home_page(self):
       response = self.client.get(url_for('main.index'))     #向首页发起请求
       self.assertTrue( b'Strange' in response.get_data(as_text=True))   #as_text用来获取Unicode字符串, b'Strange'是什么意思

   def test_register_and_login(self):
       #注册新账户
       response = self.client.post(url_for('auth.register'), data={
           'email':'john@example.com',
           'username': 'john',
           'password': 'dog',
           'password2': 'cat'
       })
       self.assertTrue(response.status_code == 302)

       #使用新注册的账户登录
       response = self.client.post(url_for('auth.login'),data={
           'email':'john@example.com',
           'password': 'cat'
       }, follow_redirects=True)
       data = response.get_data(as_text=True)
       self.assertTrue(re.search('Hello,\s+john!', data))      #为什么要加data
       self.assertTrue('You have not confirmed your account yet' in response.data)   #in data 是什么意思

       #发送确认令牌
       user = User.query.filter_by(email='john@example.com').first()
       token = user.generate_confirmation_token()
       response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
       data = response.get_data(as_text=True)
       self.assertTrue('You have confirmd your account' in response.data)

       #退出
       response = self.client.get(url_for('auth.logout'),
                                  follow_redirects=True)
       data = response.get_data(as_text=True)
       self.assertTrue('You have been logged out' in response.data)
