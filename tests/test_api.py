#coding=utf-8
import unittest
import json
from app import db, create_app
from app.models import Role, User, Post, Comment
from base64 import b64decode
from flask import url_for
import re

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()    #查看app_context()的源码
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()        #查看test_client的源码

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.app_context.pop()

    def get_api_headers(self, username, password):
        return{
            'Authorization':
                  'Basic' + b64decode(
                      (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    #错误的url
    def test_404(self):
        response = self.client.get(
            headers = self.get_api_headers('email', 'password')
        )
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data.decode('utf-8'))        #response.data是什么意思？？
        self.assertTrue(json_response['error'] == 'not found')

    def test_no_auth(self):
        response = self.client.get(
              url_for('api.get_posts'),
               content_type='application/json')
        self.assertTrue(response.status_code == 401)

    def test_bad_auth(self):

        #添加用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        #用错误密码登录
        response = self.client.get(
            url_for('api.get_posts'),
            headers = self.get_api_headers('john@example','dog')
        )
        self.assertTrue(response.status_code == 401)

    def test_token_auth(self):

        #添加用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='dog', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        #用错误的token发送请求
        response = self.client.get(         #用token发送请求使用get方法
            url_for('api.get_posts'),
            headers = self.get_api_headers('bad-token', ''))     #get_api_headers()第二个参数为什么为空？？？

        self.assertTrue(response.status_code == 401 )

        #创建一个token
        response = self.client.get(
            url_for('get_token'),
            headers = self.get_api_headers('john@example.com', 'dog'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        #用token发送一个请求
        response = self.client.get(
            url_for('get_posts'),
            headers = self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)

    def test_anonymous(self):
        #匿名用户测试
        response = self.client.get(
            url_for('get_posts'),
            headers = self.get_api_headers('', ''))
        self.assertTrue(response.status_code == 200)

    def test_unconfirmed_count(self):
        #添加一个未确认的账户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=False, role=r)
        db.session.add(u)
        db.session.commit()
        #显示未确认账户的博客
        response = self.client.get(
            url_for('get_posts'),
            headers = self.get_api_headers('john@exanple.com', 'cat'))
        self.assertTrue(response.status_code == 403)

    def test_posts(self):
        #添加一个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        #写一篇文章
        response = self.client.post(                                       #此处使用post方法，编辑博客使用put方法
                  url_for('api.new_post'),
                  headers = self.get_api_headers('john@example.com', password='cat'), #self.get_auth_header是什么意思？？？？
                  data = json.dumps({'body': 'body of the *blog* post' }))         #self.dumps()是什么意思？？？？？？
        self.assertTrue(response.status_code == 201)
        url = response.headers.get('Location')                     #注意此处的Location应该是api文件夹中的Location
        self.assertIsNotNone(url)

        #获取刚发布的文章
        response = self.client.get(
                          url,
                          headers = self.get_api_headers('john@example.com', password='cat'))
        self.assertTrue( response.status_code == 201 )
        json_response = json.loads(response.data.decode('utf-8'))     #注意解码方式 json.loads(),此处json_response为一个字典
        self.assertTrue(json_response['url'] == url )
        self.assertTrue(json_response['body'] == 'body of the *blog* post ')
        self.assertTrue(json_response['body_html'] == '<p>body of the <em>blog</em> post </p>')
        json_post = json_response

        #从用户(粉丝)处获取博客
        response = self.client.get(
            url_for('api.get_user_followed_posts', id=u.id),             #不要忘记添加id
            headers = self.get_api_headers('john@exapmple.com', 'cat'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(response.headers.get('posts'))                    #检查posts是否存在
        self.assertTrue(json_response('count', 0) == 1)                        #????????????
        self.assertTrue(json_response['posts'][0] == json_post)                #这是数组吗？？？？？？？？？？？

        #从关注者处获取博客
        response = self.client.get(
            url_for('api.get_user_followed_posts', id=u.id),
            headers = self.get_api_headers('john@example.com', 'dog'))
        self.assertTrue(response.status_code == 200)
        json_response = response.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response('count', 0) == 1)
        self.assertTrue(json_response['posts'][0] == json_post)

        #编辑博客
        response = self.client.put(                                  #更新博客使用了put方法
            url,                           #此处从哪里获取url???????
            headers = self.get_api_headers('john@example.com', 'cat'),
            data = json.dumps({'body': 'updated body'}))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url) #为什么要检查url
        self.assertTrue(json_response['body'] == 'updated body')
        self.assertTrue(json_response['body_html'] == '<p>updated body</p>')

    def test_users(self):

        #添加两名用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email = 'john@exampel.com', password='dog', confirmed=True, role=r)
        u2 = User(email = 'susan@example.com', password = 'cat', confirmed=True, role=r)
        db.session.add_all([u1,u2])
        db.session.commit()

        #获取两名用户
        response = self.client.get(
                 url_for('api.get_user', id=u1.id),
                 headers = self.get_api_headers('john@example.com', 'dog'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'john')

        response = self.client.get(
                 url_for('api.get_user', id=u2.id),
                 headers = self.get_api_headers('susan@example.com', 'dog'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'susan')

    def test_comments(self):

        #添加两名用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User.query.filter_by(email='john@example.com').first()
        u2 = User.query.filter_by(email='susan@example.com').first()
        db.session.add_all([u1,u2])
        db.session.commit()

        #添加一篇博客
        post = Post(body='body of the post', author=u1)
        db.session.add(post)
        db.session.commit()

        #添加评论
        response = self.client.post(
                url_for('api.get_posts_comments', id=post.id),
                headers = self.get_api_headers('susan@example.com', 'dog'),
                data = json.dumps({'body':'Good[post](http://example.com)!'}))
        self.assertTrue(response.status_code == 201)
        url = response.headers.get('Location')                                        #这里是从何处获取的Location
        self.assertIsNotNone(url)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['body'] == 'Good[post](http://example.com)!')
        self.assertTrue(
                re.sub('<.*?>', '', json_response['body_html']) == 'Good post!')       #这个正则表达式是什么意思？？？？？？

        #获取评论
        response = self.client.get(
                url,                                      #此处的url应该是前面获取的url,Location的那个
                headers = self.get_api_headers('john@example.com', password='dog'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url)
        self.assertTrue(json_response['body'] == 'Good[post](http://example.com)!')

        #添加其他评论
        comment = Comment(body='Thank you!', author=u1, post=post)
        db.session.add(comment)
        db.session.commit()

        #从博客中获取两条评论
        response = self.client.get(
                url_for('get_posts_comments', id=post.id),
                headers = self.get_api_headers('susan@example.com', password='dog'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertTrue(json_response.get('count',0) == 2)     #获取两条评论所以数字为2????????  数字2是什么意思,   数字0是什么意思？？

        #获取所有评论
        response = self.client.get(
                url_for('get_comments'),
                headers = self.get_api_headers('susan@example.com', password='dog'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertTrue(json_response.get('count', 0) == 2)
