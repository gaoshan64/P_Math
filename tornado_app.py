# !/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# @Time : 2022/2/623:23
# @Author : gaoshan
# @Email : gaoshan-1@michelin.com
# @File : .py
# @Software: PyCharm



import tornado.ioloop

import tornado.options
import tornado.gen
import json
import random
import tornado.web
import tornado.httpclient
import db_controler
import os
import pathlib
import time
import Psmrcddup
import PrintPreview
from pprint import pprint


setting={
    "cookie_secret": "188EDCA6-5207-412F-7342-D4B8F7A49A2B",  # 认证用
    #"login_url": "/login",  # 认证页面
    # 'autoreload': True,
    #'xsrf_cookies': True  # 防跨域
    }


memorydb=db_controler.DBControler('./test_db.db')

class BaseHandler(tornado.web.RequestHandler):


    def get_current_user(self):
        '''
        每次获取GET 请求后返回这个COOKIE
        :return:
        '''
        return self.get_secure_cookie("uid")



    def get_uid(self,reset=None):
        uid = self.get_cookie('uid')
        # print(type(uid),uid)
        if reset:
            uid=None

        if not uid:
            #如果没有COOKIE
            memorydb.register()
            uid = memorydb.dumps()[-1]
            os.mkdir('./static/userfile/{}'.format(str(uid)))
            #os.mkdir('./static/users_image/{}/tn'.format(str(uid)))
            #os.mkdir('./static/users_image/{}/page'.format(str(uid)))
            headers=dict(self.request.headers.get_all())
            user_infor=headers
            user_infor['first_time']=time.time()
            #print(uid,'######',user_infor)
            memorydb.update(uid, {'user_infor': user_infor})

            self.set_cookie('uid', str(uid))

        uid_path='./static/userfile/{}'.format(str(uid))
        #uid_tn_path='./static/users_image/{}/tn'.format(str(uid))
        #uid_page_path='./static/users_image/{}/page'.format(str(uid))
        # pathlib.Path(img_s_p)
        if not  pathlib.Path(uid_path):
            #如果没有文件夹 创建
            os.mkdir('./static/users_image/{}'.format(str(uid)))

        #if not pathlib.Path(uid_tn_path):
            #os.mkdir('./static/users_image/{}/tn'.format(str(uid)))

        #if not pathlib.Path(uid_page_path):
            #os.mkdir('./static/users_image/{}/tn'.format(str(uid)))




        if isinstance(uid, int):
            return uid
        elif isinstance(uid, str):

            return int(uid)
        else:
            print('get_uid_fail')
            return None

    def get_user_config(self,uid):
        ### word infor list 是个字典组成的列表
        memory_dict = memorydb.query(uid)
        #print('memorydic',memory_dict)
        # print(''+ len(memory_dict))
        if not memory_dict:
            #print('word_batch_list')

            uid=self.get_uid(reset=True)

            memory_dict=memorydb.query(uid)

        if  not memory_dict['user_config']:
            user_config = ''
            #print('here')
        elif isinstance(memory_dict['user_config'],str):
            user_config=memory_dict['user_config']
            user_config=json.loads(user_config)
            #print([x['word'] for x in word_infor_list])
        else:
            print('get user_config fail')
            return None
        return user_config

    def user_config_to_db(self,uid,user_config):
        #将列表写如数据库
        try:
            memorydb.update(uid, {'user_config':user_config})
            #print('写入？')
            memorydb.query(uid)
        except Exception as e:
            print(e)
            print(e.args)
            print(str(e))
            print(repr(e))
            print('write db back fail')

class LoginHandler(BaseHandler):
    '''
    登录 获取用户名
    生成uid
    '''
    def get(self):


        self.redirect('/')


class MainHandler(BaseHandler):
    #@tornado.web.authenticated

    def get(self):
        uid=self.get_uid()
        user_config = self.get_user_config(uid)

        if not user_config:
            user_config = "{\"step\": [\"3\"], \"is_result\": [\"0\"], \"is_bracket\": [\"\"], " \
                          "\"carry\": [\"1\"], \"abdication\": [\"1\"], \"remainder\": [\"2\"], " \
                          "\"multistep_a1\": [\"1\"], \"multistep_a2\": [\"100\"], \"multistep_b1\": " \
                          "[\"1\"], \"multistep_b2\": [\"100\"], \"multistep_c1\": [\"1\"], " \
                          "\"multistep_c2\": [\"100\"], \"multistep_d1\": [\"1\"], \"multistep_d2\":" \
                          " [\"100\"], \"multistep_e1\": [\"0\"], \"multistep_e2\": [\"1000\"], " \
                          "\"symbols_a\": [\"1\", \"2\", \"3\", \"4\"]," \
                          " \"symbols_b\": [\"1\", \"2\", \"3\", \"4\"]," \
                          " \"symbols_c\": [\"1\", \"2\", \"3\", \"4\"]," \
                          " \"jz_title\": [\"数学测试\"], " \
                          "\"inf_title\": [\"姓名：__________ 日期：____月____日 用时：________ 正确率：____\"]," \
                          " \"number\": [\"50\"]}"
        user_config=json.loads(user_config)





        print(uid)
        pprint(user_config)
        print('#',type(user_config))

        self.render('./templates/index.html',uid=uid,questions='',
                    answers='',cols=1,title1='',title2='',user_config=user_config)

    def post(self):
        uid=self.get_uid()
        user_config=self.get_user_config(uid)
        post_data = self.request.arguments


        def decode_list(list):
            list_finish=[]
            for x in list:
                y=x.decode("utf-8")
                list_finish.append(y)
            return list_finish

        post_data={x:decode_list(post_data.get(x))  for x in post_data.keys()}
        user_config = post_data
        post_data=json.dumps(post_data, ensure_ascii=False)
        self.user_config_to_db(uid,post_data)

        if not user_config:
            user_config = "{\"step\": [\"3\"], \"is_result\": [\"0\"], \"is_bracket\": [\"\"], " \
                          "\"carry\": [\"1\"], \"abdication\": [\"1\"], \"remainder\": [\"2\"], " \
                          "\"multistep_a1\": [\"1\"], \"multistep_a2\": [\"100\"], \"multistep_b1\": " \
                          "[\"1\"], \"multistep_b2\": [\"100\"], \"multistep_c1\": [\"1\"], " \
                          "\"multistep_c2\": [\"100\"], \"multistep_d1\": [\"1\"], \"multistep_d2\":" \
                          " [\"100\"], \"multistep_e1\": [\"0\"], \"multistep_e2\": [\"1000\"], " \
                          "\"symbols_a\": [\"1\", \"2\", \"3\", \"4\"]," \
                          " \"symbols_b\": [\"1\", \"2\", \"3\", \"4\"]," \
                          " \"symbols_c\": [\"1\", \"2\", \"3\", \"4\"]," \
                          " \"jz_title\": [\"数学测试\"], " \
                          "\"inf_title\": [\"姓名：__________ 日期：____月____日 用时：________ 正确率：____\"]," \
                          " \"number\": [\"50\"]}"



        print(uid)
        pprint(user_config)

        #post_data = json.dumps(post_data)

        #if not post_data:
        #post_data = self.request.body.decode('utf-8')
        #post_data = json.loads(post_data)
        #print(post_data)
        #print(type(post_data))
        '''{'step': [b'1'], 'is_result': [b'0'], 'is_bracket': [b'on'], 'carry': [b'1'], 'abdication': [b'1'],
         'remainder': [b'1'], 'multistep_a1': [b'1'], 'multistep_a2': [b'100'], 'multistep_b1': [b'1'],
         'multistep_b2': [b'100'], 'multistep_c1': [b'1'], 'multistep_c2': [b'100'], 'multistep_d1': [b'1'],
         'multistep_d2': [b'100'], 'multistep_e1': [b'0'], 'multistep_e2': [b'1000'],
         'symbols_a': [b'1', b'2', b'3', b'4'], 'symbols_b': [b'1', b'2', b'3', b'4'],
         'symbols_c': [b'1', b'2', b'3', b'4'],
         'jz_title': [b'\xe5\xb0\x8f\xe5\xad\xa6\xe6\x95\xb0\xe5\xad\xa6\xe6\xb5\x8b\xe8\xaf\x95'], 'inf_title': [
            b'\xe5\xa7\x93\xe5\x90\x8d\xef\xbc\x9a__________ \xe6\x97\xa5\xe6\x9c\x9f\xef\xbc\x9a____\xe6\x9c\x88____\xe6\x97\xa5 \xe6\x97\xb6\xe9\x97\xb4\xef\xbc\x9a________ \xe5\xaf\xb9\xe9\xa2\x98\xef\xbc\x9a____\xe9\x81\x93'],
         'number': [b'50']}'''
        add=int(self.get_arguments("carry")[0])
        if add not in [1,2,3,]:
            add= 3
        add={"carry":add}
        sub=int(self.get_arguments('abdication')[0])
        if sub not in [1,2,3]:
            sub =3

        sub={"abdication":sub}

        div=int(self.get_arguments("remainder")[0])
        if div not in [1,2,3]:
            div=2

        div={"remainder":div, }

        symbols_a=[int(x) for x  in self.get_arguments('symbols_a') ]

        if not symbols_a:
            symbols_a = [1,2,3,4]

        for x in symbols_a:
            if x not  in [1,2,3,4]:
                symbols_a = [1,2,3,4]
            break


        symbols_b=[int(x) for x  in self.get_arguments('symbols_b') ]

        if not symbols_b:
            symbols_b = [1,2,3,4]

        for x in symbols_b:
            if x not in [1, 2, 3, 4]:
                symbols_b = [1, 2, 3, 4]
            break

        symbols_c = [int(x) for x in self.get_arguments('symbols_c')]

        if not symbols_c:
            symbols_c = [1,2,3,4]


        for x in symbols_c:
            if x not in [1, 2, 3, 4]:
                symbols_c = [1, 2, 3, 4]
            break

        signum=symbols_a
        symbols=[symbols_a,symbols_b,symbols_c,]

        multistep_a1 =int(self.get_arguments('multistep_a1')[0])
        if multistep_a1 <0:
            multistep_a1 =0
            user_config['multistep_a1'][0]='0'

        multistep_a2 = int(self.get_arguments('multistep_a2')[0])
        if multistep_a2 >100:
            multistep_a2=100
            user_config['multistep_a2'][0] = '100'

        if multistep_a1>multistep_a2:
            multistep_a1 = multistep_a2
            user_config['multistep_a1'][0] = user_config['multistep_a2'][0]





        multistep_e1 = int(self.get_arguments('multistep_e1')[0])
        if multistep_e1 <0:
            multistep_e1 =0
            user_config['multistep_a1'][0]='0'

        multistep_e2 = int(self.get_arguments('multistep_e2')[0])
        if multistep_e2 >1000:
            multistep_e2=1000
            user_config['multistep_e2'][0] = '5000'

        if multistep_e1>multistep_e2:
            multistep_e1 = multistep_e2
            user_config['multistep_e1'][0] = user_config['multistep_e2'][0]


        multistep=[[multistep_a1,multistep_a2],[multistep_a1,multistep_a2],
                   [multistep_a1,multistep_a2],[multistep_a1,multistep_a2],
                   [multistep_e1,multistep_e2]]

        step=int(self.get_arguments('step')[0])

        if step not in [1,2,3]:
            step =3

        is_result=int(self.get_arguments('is_result')[0])

        if is_result not in [1,0]:
            is_result =1

        number=int(self.get_arguments('number')[0])

        if number>50:
            number =50
        elif number< 0:
            number = 0


        is_bracket=self.get_arguments('is_bracket')
        if is_bracket:
            is_bracket = 1
        else:
            is_bracket = 0

        #print(add,sub,div,signum,step,number,is_result,is_bracket,multistep,symbols)




        g=Psmrcddup.Generator(add,sub,div,signum,step,number,is_result,is_bracket,multistep,symbols)

        data_list=g.generate_data()
        questions=[x[0] for x in data_list]
        answers=[x[1] for x in data_list]
        #print(questions)
        #print(answers)

        if step == 1:
            cols =4
        else:
            cols =2
        print(step,'aaaa',cols)

        title1=self.get_argument('jz_title')
        title2=self.get_argument('inf_title')

        p=PrintPreview.PrintPreview(l=[questions],tit=[title1],subtitle=title2,col=cols,docxpath='./static/userfile/')
        p.create_psmdocx(l=questions,title=title1,docxname=str(uid))

        print('#', type(user_config))

        self.render('./templates/index.html',uid=uid,questions=questions,answers=answers,
                    cols=cols,title1=title1,title2=title2,user_config=user_config)

class ClearConfigHandler(BaseHandler):
    def get(self):
        uid=self.get_uid()
        user_config = "{\"step\": [\"3\"], \"is_result\": [\"0\"], \"is_bracket\": [\"\"], " \
                      "\"carry\": [\"1\"], \"abdication\": [\"1\"], \"remainder\": [\"2\"], " \
                      "\"multistep_a1\": [\"1\"], \"multistep_a2\": [\"100\"], \"multistep_b1\": " \
                      "[\"1\"], \"multistep_b2\": [\"100\"], \"multistep_c1\": [\"1\"], " \
                      "\"multistep_c2\": [\"100\"], \"multistep_d1\": [\"1\"], \"multistep_d2\":" \
                      " [\"100\"], \"multistep_e1\": [\"0\"], \"multistep_e2\": [\"1000\"], " \
                      "\"symbols_a\": [\"1\", \"2\", \"3\", \"4\"]," \
                      " \"symbols_b\": [\"1\", \"2\", \"3\", \"4\"]," \
                      " \"symbols_c\": [\"1\", \"2\", \"3\", \"4\"]," \
                      " \"jz_title\": [\"数学测试\"], " \
                      "\"inf_title\": [\"姓名：__________ 日期：____月____日 用时：________ 正确率：____\"]," \
                      " \"number\": [\"50\"]}"
        self.user_config_to_db(uid,user_config)
        self.redirect('/pmath')

class temp_test(BaseHandler):
    def get(self):
        self.render('./templates/temp.html')

class SendMailHandler(BaseHandler):
    def post(self):
        uid=self.get_uid()
        email=self.get_argument('email')
        #print(type(uid),uid,'/n',type(email),email)
        if uid and email:
            print('ok')
        self.write('here')

def make_app():
    # tornado 路由设置
    return tornado.web.Application([
        (r"/pmath", MainHandler),
        (r"/pmath/clear_config",ClearConfigHandler),
        (r"/pmath/sendmail", SendMailHandler),

        #(r"/imagechose/",ImagechoseHandler),
        #(r"/added/", AddedHandler),----

        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': './static'}),
        #(r'/templates/(.*)', tornado.web.StaticFileHandler, {'path': './templates'}),

        # change static path
        #(r"/login", LoginHandler),
        #(r'/logout', LogoutHandler),

    ],

        # +SockJSRouter(RealTimeHandler,'/realtime').urls,
        **setting
    )

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = make_app()
    app.listen(3334)
    tornado.ioloop.IOLoop.current().start()