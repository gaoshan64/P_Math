# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : word_card_main.py
# Time       ：2021/11/9 21:34
# Author     ：Gao Shan
# Description：
"""
import tornado.ioloop

import tornado.options
import tornado.gen
import random
import tornado.web
import tornado.httpclient
import db_controler
from stardict import StarDict
import json
import os
from shutil import copyfile
import pathlib
import create_word_infor_image
import create_A4_pdf
from PIL import Image
from io import BytesIO
import codecs,markdown
import add_word
import get_en_word
import create_web_tn
import time

from creat_url_qrcode import get_url_qrcode
setting={
    "cookie_secret": "188EDCA6-5207-412F-7342-D4B8F7A49A2B",  # 认证用
    #"login_url": "/login",  # 认证页面
    # 'autoreload': True,
    #'xsrf_cookies': True  # 防跨域
    }
bigger_dict=StarDict('ecdict.db')
this_dict=StarDict('cot_bak.db')
memorydb=db_controler.DBControler('./static/users_image/test_db.db')



class BaseHandler(tornado.web.RequestHandler):
    '''
    BaseHandler
    认证功能，所有页面继承自此类
    '''

    def copy_user_image(self,uid,word):
        word_infor = this_dict.query(word)
        image_id = word_infor['image_id']
        img_s_p = './static/w_img/{}_img.png'.format(word)  # 存储的图片地址
        s_pathfile = pathlib.Path(img_s_p)  # 存储的图片PATH对象
        #static/w_qrcode_webview
        img_s_web_p = './static/w_qrcode_webview/{}_img.png'.format(word)  # 缩略图加二维码
        s_web_pathfile = pathlib.Path(img_s_web_p)  # 缩略图加二维码PATH对象
        img_u_p = './static/users_image/{}/{}_{}_img.png'.format(uid, word, str(image_id))  # 用户图片地址
        u_pathfile = pathlib.Path(img_u_p)  # 用户图片地址对象
        img_u_i_p = './static/users_image/{}/{}_infor.png'.format(uid, word, str(image_id))  # 用户信息图片地址
        i_pathfile = pathlib.Path(img_u_i_p)  # 用户图片地址对象
        img_u_web_p = './static/users_image/{}/tn/{}_{}_wv_img.png'.format(uid, word, str(image_id))#用户加完二维码缩略图
        web_pathfile = pathlib.Path(img_u_web_p)
        if not u_pathfile.exists():
            if not s_pathfile.exists():
                # 如果图库里没有 拷贝个占位图片过去
                copyfile('../word_card2/static/__no_image_found.png', img_u_p)
                copyfile('../word_card2/static/__no_image_found.png', img_u_web_p)
            else:
                # 如果用户图片 不存在 拷贝存储的图片 到用户图片文件夹
                copyfile(img_s_p, img_u_p)
                copyfile(img_s_web_p,img_u_web_p)
            '''   
            im_web = Image.open(img_u_p)
            im_web = self.add_image_qr(im_web, word)
            # im.thumbnail((150,50))
            im_web.thumbnail((im_web.size[0] // 2, im_web.size[1] // 2))
            im_web.save('./static/users_image/{}/tn/{}_{}_wv_img.png'.format(uid, word, str(image_id)))
            '''
        if not i_pathfile.exists():
            # 如果用户单词信息图片不存在 生成
            create_word_infor_image.create_word_infor_image(word).save(img_u_i_p)


    def create_web_view_image(self,img):
        img =Image.open(BytesIO(img))
        pass

    def add_image_qr(self,img,word):

        im_qr = get_url_qrcode(word)  # 生成qrcode
        img.paste(im_qr, (img.size[0] - im_qr.size[0], img.size[1] - im_qr.size[1]))
        # 把qrcode 粘贴到IMAGE 的右下角
        #im.save('./static/users_image/{}/{}_{}_qr_img.png'.format(uid, word, image_id))
        # 把添加了qrcode 的 IMAGE 保存到 用户文件夹 命名规则 word_imageid_qr_imag.png
        return img



    def resize_image(self,img):
        '''

        :param img: c传入图片
        :return: 传出图片
        图片处理函数
        '''

        # 将requests 结果 直接转给pillow Img
        img = Image.open(BytesIO(img))

        turned = False
        if img.size[0] / img.size[1] >= 1:
            img = img.rotate(90, expand=True)
            turned = True
            # print('rotate 90')
        else:

            # print('no rotate')
            pass

        if img.size[0] / img.size[1] >= 0.7:
            # print('too fat')
            # print('before ' + str(img.size))
            # img.thumbnail((1000,620))

            baseheight = 620

            hpercent = (baseheight / float(img.size[1]))
            wsize = int((float(img.size[0]) * float(hpercent)))
            img = img.resize((wsize, baseheight), Image.ANTIALIAS)

            # print('after ' + str(img.size))
            cut = (img.size[0] - 438) // 2
            cropped = img.crop((cut, 0, img.size[0] - cut, img.size[1]))
            # cropped.save('./static/w_img/a_img_resize.png')
        else:
            # print('too tall')
            # img.thumbnail((438,1000))
            # print('before ' + str(img.size))

            basewidth = 438

            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), Image.ANTIALIAS)

            # print('after ' + str(img.size))
            cut = (img.size[1] - 620) // 2
            cropped = img.crop((0, cut, img.size[0], img.size[1] - cut))
            # cropped.save('./static/w_img/a_img_resize.png')

        if turned:
            cropped = cropped.rotate(270, expand=True)

        return cropped

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
            os.mkdir('./static/users_image/{}'.format(str(uid)))
            os.mkdir('./static/users_image/{}/tn'.format(str(uid)))
            os.mkdir('./static/users_image/{}/page'.format(str(uid)))
            headers=dict(self.request.headers.get_all())
            user_infor=headers
            user_infor['first_time']=time.time()
            #print(uid,'######',user_infor)
            memorydb.update(uid, {'user_infor': user_infor})

            self.set_cookie('uid', str(uid))

        uid_path='./static/users_image/{}'.format(str(uid))
        uid_tn_path='./static/users_image/{}/tn'.format(str(uid))
        uid_page_path='./static/users_image/{}/page'.format(str(uid))
        # pathlib.Path(img_s_p)
        if not  pathlib.Path(uid_path):
            #如果没有文件夹 创建
            os.mkdir('./static/users_image/{}'.format(str(uid)))

        if not pathlib.Path(uid_tn_path):
            os.mkdir('./static/users_image/{}/tn'.format(str(uid)))

        if not pathlib.Path(uid_page_path):
            os.mkdir('./static/users_image/{}/tn'.format(str(uid)))




        if isinstance(uid, int):
            return uid
        elif isinstance(uid, str):

            return int(uid)
        else:
            print('get_uid_fail')
            return None


    def get_word_infor_list(self,uid):
        ### word infor list 是个字典组成的列表
        #print(uid)
        memory_dict = memorydb.query(uid)
        if not memory_dict:
            #print('word_infor_list')

            uid=self.get_uid(reset=True)
            memory_dict=memorydb.query(uid)
        #print('memorydic',memory_dict)
        # print(''+ len(memory_dict))
        # word_infor_list.append(word_infor)
        if  not memory_dict['word_infor_list']:
            word_infor_list = []
            #print('here')
        elif isinstance(memory_dict['word_infor_list'],str):
            word_infor_list=memory_dict['word_infor_list']
            word_infor_list=json.loads(word_infor_list)


            #print([x['word'] for x in word_infor_list])
        else:
            print('get word_infor_list fail')
            return None

        return word_infor_list


    def get_batch_word_list(self,uid):
        ### word infor list 是个字典组成的列表
        memory_dict = memorydb.query(uid)
        #print('memorydic',memory_dict)
        # print(''+ len(memory_dict))
        if not memory_dict:
            #print('word_batch_list')

            uid=self.get_uid(reset=True)

            memory_dict=memorydb.query(uid)

        if  not memory_dict['batch_word_list']:
            batch_word_list = []
            #print('here')
        elif isinstance(memory_dict['batch_word_list'],str):
            batch_word_list=memory_dict['batch_word_list']
            batch_word_list.lower()
            #print('get',batch_word_list)
            batch_word_list=json.loads(batch_word_list)


            #print([x['word'] for x in word_infor_list])
        else:
            print('get batch_word_list fail')
            return None

        return batch_word_list

    def get_page_list(self,uid):
        ### word infor list 是个字典组成的列表
        memory_dict = memorydb.query(uid)
        #print('get_page_list',memory_dict)
        #print('memorydic',memory_dict)
        # print(''+ len(memory_dict))
        if not memory_dict:
            #print('get_page_list')


            uid=self.get_uid(reset=True)
            memory_dict=memorydb.query(uid)

        if  not memory_dict['page_list']:
            page_list = []
            #print('here')
        elif isinstance(memory_dict['page_list'],str):
            page_list=memory_dict['page_list']
            page_list=json.loads(page_list)

            #print([x['word'] for x in word_infor_list])
        else:
            print('get page_list fail')
            return None

        return page_list


    def w_i_list_to_db(self,uid,word_infor_list):
        #将列表写如数据库
        try:
            memorydb.update(uid, {'word_infor_list':word_infor_list})
            #print('写入？')
            #memorydb.query(uid)
        except Exception as e:
            print(e)
            print(e.args)
            print(str(e))
            print(repr(e))
            print('write db back fail')


    def b_w_list_to_db(self,uid,batch_word_list):
        #将列表写如数据库
        try:
            memorydb.update(uid, {'batch_word_list':batch_word_list})
            #print('写入？')
            memorydb.query(uid)
        except Exception as e:
            print(e)
            print(e.args)
            print(str(e))
            print(repr(e))
            print('write db back fail')

    def page_list_to_db(self,uid,page_list):
        #将列表写如数据库
        try:
            memorydb.update(uid, {'page_list':page_list})
            #print('写入？')
            #memorydb.query(uid)
        except Exception as e:
            print(e)
            print(e.args)
            print(str(e))
            print(repr(e))
            print('write db back fail')


    def get_to_temp_list(self,word_infor_list):
        #最后传递给页面的数据
        #列表 列表中的每项是 字典 字典包括从 this 中查询出的所有字段
        blank_dict = {'word': '__empty'}
        fill_list = []
        for x in range(0, 8):
            fill_list.append(blank_dict)
        to_temp_list = (word_infor_list + fill_list)[0:8]
        #print([x['word'] for x in to_temp_list])
        return to_temp_list



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
        word_infor_list=self.get_word_infor_list(uid)
        batch_word_list=self.get_batch_word_list(uid)
        page_list=self.get_page_list(uid)
        cl=self.get_argument('cl',None)
        if not cl:
            cl=''
        page=self.get_argument('page',None)
        if not page:
            page=''
        #print([x['word'] for x in word_infor_list])
        to_temp_list=self.get_to_temp_list(word_infor_list)
        message=('alert-primary','Hello,Welcome.User{}'.format(str(uid)))
        random_v=0
        pdf_out_fn = './static/users_image/{}/finalpdf.pdf'.format(uid)
        page_fp= './static/users_image/{}/page'.format(uid)

        if pathlib.Path(pdf_out_fn).exists():
            random_v=random.randint(100,10000)


        if page_list == []:
            havepage=False
        else:
            havepage=True

        self.render('./static/index.html',uid=str(uid),
                    data=to_temp_list,message=message,
                    batch_word_list=batch_word_list, cl=cl,
                    random_v=random_v,havepage=havepage)

    def post(self):
        uid = self.get_uid()
        message = ('alert-primary', 'Hello,Welcome!User{}.'.format(str(uid)))
        word=self.get_argument('u_word',None)
        if word :
            word=word.strip().lower()
        page_fp = './static/users_image/{}/page'.format(uid)
        if os.listdir(page_fp) == []:
            havepage=False
        else:
            havepage=True
        word_delete_index=self.get_argument('word_delete_index',None)
        #print(word_delete_index)
        #print(type(word_delete_index))

        word_infor_list=self.get_word_infor_list(uid)
        batch_word_list = self.get_batch_word_list(uid)

        if (len(word_infor_list) < 8) and (word != None):
            #获取用户输入的单词 已输入单词数少于8 并且用户输入的单词不为空
            #print('here',len(word_infor_list))
            #去词典里查询这个单词
            word_infor = this_dict.query(word)

            if isinstance(word_infor,dict):
                #如果查到了这个单词
                #print('#',word_infor_list)
                word_infor_list.append(word_infor)
                #print('#',word_infor_list)

                #将单词加到 word_infor_list 的最后
                #print([x['word'] for x in word_infor_list])
                #将图片拷贝到用户文件夹
                self.copy_user_image(uid,word)
                message=('alert-success', 'New word added !')
            else:
                if bigger_dict.query(word):
                    add_word.add_word_all(word)
                    #print('new word added in to cot')
                    word_infor = this_dict.query(word)

                    if isinstance(word_infor, dict):

                        word_infor_list.append(word_infor)

                        self.copy_user_image(uid, word)
                        message = ('alert-success', 'New word added !')
                else:


                    message = ('alert-danger', 'No such word in dictionary !')
        else:
            message = ('alert-danger', 'The WordList full !')



        if isinstance(word_delete_index,str):
            #print('delete ',word_delete_index)
            del word_infor_list[int(word_delete_index)]
            #print(print([x['word'] for x in word_infor_list]))
            message = ('alert-success', 'Successfully delete word !')



        self.w_i_list_to_db(uid, word_infor_list)

        to_temp_list=self.get_to_temp_list(word_infor_list)
        #print(to_temp_list)
        random_v=0
        pdf_out_fn = './static/users_image/{}/finalpdf.pdf'.format(uid)
        if pathlib.Path(pdf_out_fn).exists():
            random_v = random.randint(100, 10000)

        self.render('./static/index.html',uid=str(uid),data=to_temp_list,
                    message=message,random_v=random_v,batch_word_list=batch_word_list,
                    cl='',havepage=havepage)

class ViewPageHandler(BaseHandler):
    def get(self):
        uid=self.get_uid()
        page_list=self.get_page_list(uid)
        user_path='./static/users_image/{}'.format(str(uid))
        page_path='{}/page'.format(user_path)


        self.render('./static/pageview.html',page_list=page_list,uid=str(uid))

class RandomFill(BaseHandler):

    def get(self):
        uid=self.get_uid()
        word_infor_list = self.get_word_infor_list(uid)
        need_refine_words=this_dict.refine_image()
        random_need_refine_words=random.sample(need_refine_words,8)
        for word in random_need_refine_words:
            if len(word_infor_list)>=8:
                break
            word_infor=this_dict.query(word)
            self.copy_user_image(uid,word)
            word_infor_list.append(word_infor)
        self.w_i_list_to_db(uid,word_infor_list)
        self.redirect('/')











        
class ViewHandler(BaseHandler):



    async def download_image(self,new_image_url):
        #response = await tornado.httpclient.AsyncHTTPClient().fetch(new_image_url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
        }
        this_request=tornado.httpclient.HTTPRequest(url=new_image_url,headers=headers)

        i = 0
        while i <= 5:
            try:
                response = await tornado.httpclient.AsyncHTTPClient().fetch(this_request)

            except Exception as e:
                i += 1
                print("Error:%s" % e)
            else:
                break
        img=response.body
        return img

    async def get(self):
        uid=self.get_uid()
        word_infor_list=self.get_word_infor_list(uid)
        word_index=self.get_argument('word_index')
        word=word_infor_list[int(word_index)]['word'].lower()
        new_image_url=self.get_argument('new_image_url',None)
        image_id=self.get_argument('image_id',None)
        if image_id:
            image_id=int(image_id)
        if new_image_url:
            word_infor_list[int(word_index)]['image_id']=image_id
            this_dict.update(word,{'image_id':image_id})
            self.w_i_list_to_db(uid,word_infor_list)

            img=await self.download_image(new_image_url)
            img=self.resize_image(img)
            img_path='./static/users_image/{}/{}_{}_img.png'.format(str(uid),word,str(image_id))
            #os.remove(img_path)
            img.save(img_path)
            im_web=self.add_image_qr(img,word)
            im_web.thumbnail((im_web.size[0]//2,im_web.size[1]//2))
            im_web.save('./static/users_image/{}/tn/{}_{}_wv_img.png'.format(uid,word,str(image_id)))

        #print(type(word_index))
        message_list=[str(uid),'###############',
                   json.dumps(word_infor_list,ensure_ascii=False,indent=2),'######################',
                   word_index]
        message = ('alert-success', 'View {} detial'.format(word))
        to_temp_list = self.get_to_temp_list(word_infor_list)

        #print(uid,word_infor_list,word_index)
        await self.render('./static/view.html',uid=str(uid),
                    data=to_temp_list,message=message,word_index=word_index,word=word)



class ImageChoiceHandler(BaseHandler):



    def make_url(self,word,page=1,lang='en'):
        safesearch = 'true'
        # orientation='vertical'
        lang = lang


        per_page = '18'
        key = '24061411-b0033e79b6a54ea8e0b73d201'
        url = 'https://pixabay.com/api/?key={}&q=“{}”&safesearch={}' \
              '&per_page={}&page={}&lang={}'.format(key, word, safesearch, per_page,page,lang)
        #print(url)
        return url

    async def do_request(self,url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
        }
        this_request = tornado.httpclient.HTTPRequest(url=url, headers=headers)
        i=0
        while i<=5:
            try:
                response = await tornado.httpclient.AsyncHTTPClient().fetch(this_request)

            except Exception as e:
                i+=1
                print("Error:%s"%e)
            else:
                break

        #print("fetched %s" % url)

        api_str = response.body.decode(errors="ignore")
        api_list=json.loads(api_str)['hits']
        lean_api_list=[(x['id'],x['largeImageURL'],x['previewURL'],x['user_id'],x['user']) for x in api_list]
        return lean_api_list



    async def get(self):
        uid=self.get_uid()
        word=self.get_argument('word')
        page =self.get_argument('page',None)
        lang = self.get_argument('lang','en')
        if not page:
            page =1

        word_index=self.get_argument('word_index')
        url=self.make_url(word,page,lang)
        image_list=await self.do_request(url)
        lean_image_list=[(x[2],x[1],x[0]) for x in image_list ]
        #print(uid)
        #print(word)
        #print(image_list)
        if len(lean_image_list) :
            message = ('alert-primary', 'Please chose your image')
        else:
            message = ('alert-warning', 'NO Matching image,Try change key word.')

        #self.write('hello')
        await self.render('./static/imagechoice.html', uid=str(uid),
                          word_index=word_index,
                          lean_image_list=lean_image_list, word=word,
                          message=message,page=page,lang = lang)






class TempTest(BaseHandler):

    def get(self):
        self.render('./static/temp_test.html')


class UpdateImage(BaseHandler):

    def get(self):
        uid = self.get_uid()
        word_infor_list = self.get_word_infor_list(uid)
        word_index = self.get_argument('word_index')
        #print('########',word_index,type(word_index),'############')
        '''for x in word_infor_list:
            print('*#'*20)
            print(x['word'],x['image_id'])
            print('*#' * 20)'''
        word_infor=word_infor_list[int(word_index)]
        #print( word_infor['word'],word_infor['image_id'])
        #将用户图片拷贝到图库
        img_s_p = './static/w_img/{}_img.png'.format(word_infor['word'].lower())
        img_u_p='./static/users_image/{}/{}_{}_img.png'.format(uid, word_infor['word'].lower(), word_infor['image_id'])
        s_pathfile = pathlib.Path(img_s_p)
        u_pathfile = pathlib.Path(img_u_p)
        if u_pathfile.exists():
            #print('here')
            #os.remove(img_s_p)
            copyfile(img_u_p,img_s_p)

            file_add_qr_path = './static/w_qrcode/{}_img.png'.format(word_infor['word'].lower())
            file_qr_web_path = './static/w_qrcode_webview/{}_img.png'.format(word_infor['word'].lower())
            try:
                create_web_tn.add_qr(img_s_p, word_infor['word'], result=file_add_qr_path)
            except Exception as e:
                print('addqr', e)

            try:
                create_web_tn.create_thumbnail(file_add_qr_path, result=file_qr_web_path)
            except Exception as e:
                print(e)



            #print('图库已经更新')
        self.redirect('/')

class ClearAllWord(BaseHandler):
    def get(self):
        uid = self.get_uid()
        position=self.get_argument('position',None)
        word_infor_list = []
        self.w_i_list_to_db(uid,word_infor_list)
        if position:
            position='downloadpdf'
        else:
            position=''
        self.redirect('/#{}'.format(position))

class CreatePage(BaseHandler):
    def get(self):
        print('create page','#uid',)
        uid=self.get_uid()
        word_infor_list=self.get_word_infor_list(uid)
        page_list=self.get_page_list(uid)
        if (not page_list) or page_list == []:
            page_id=1
        else:
            page_id=page_list[-1]+1

        image_infor_list = [(x['word'], x['image_id']) for x in word_infor_list]
        create_A4_pdf.create_image_side(uid, image_infor_list,page_id)
        create_A4_pdf.create_infor_side(uid, image_infor_list,page_id)
        create_A4_pdf.image_infor_merge(uid,page_id)
        page_list.append(page_id)
        self.page_list_to_db(uid,page_list)
        self.redirect('/clearallword?position=bottom')

class CreatePdf(BaseHandler):
    def get(self):
        uid = self.get_uid()
        page_list=self.get_page_list(uid)
        print_type=self.get_argument('printtype')
        create_A4_pdf.create_pdf(uid,page_list,print_type)
        page_list=[]
        self.page_list_to_db(uid,page_list)
        self.redirect('/clearallword?position=bottom')


class GetBatchWord(BaseHandler):
    def post(self):
        uid=self.get_uid()
        txt=self.get_argument("para")
        txt=txt.lower()
        word_list=get_en_word.get_en_word(txt)
        #print('wordlist',word_list)
        batch_word_list=self.get_batch_word_list(uid)
        #print('batch_word_list before',batch_word_list)
        if word_list:
            #batch_word_list.extend(word_list)
            for word in word_list:
                if word in batch_word_list:
                    continue
                batch_word_list.append(word)

        #print('batch_word_list after',batch_word_list)
        self.b_w_list_to_db(uid,batch_word_list)
        self.redirect('/?cl=show')

class InsertBatchWord(BaseHandler):
    async def post(self):
        uid=self.get_uid()
        word_infor_list = self.get_word_infor_list(uid)
        batch_word_list=self.get_argument('batch_word').lower().split(',')
        while '' in batch_word_list:
            batch_word_list.remove('')
        while None in batch_word_list:
            batch_word_list.remove(None)
        #print('before batch===>',batch_word_list)
        #print('before w_i_l len===>',len(word_infor_list))
        cp_batch_word_list=batch_word_list[:]
        for word in cp_batch_word_list:
            if len(word_infor_list)>=8:
                break
            if not word:
                continue
            word_infor=this_dict.query(word)
            #print(word,'===',word_infor)
            if not word_infor:
                add_word.add_word_all(word)
                await tornado.gen.sleep(0.5)
                word_infor=this_dict.query(word)
                #print('added',word,'=====',word_infor)
            self.copy_user_image(uid,word)
            word_infor_list.append(word_infor)
            batch_word_list.remove(word)



        #print('after bath===>', batch_word_list)
        #print('after w_i_l len===>',len(word_infor_list))
        while '' in batch_word_list:
            batch_word_list.remove('')
        self.w_i_list_to_db(uid,word_infor_list)
        self.b_w_list_to_db(uid,batch_word_list)
        self.redirect('/?cl=show')

class DelPage(BaseHandler):
    def get(self):
        uid=self.get_uid()
        del_page_index=self.get_argument('page_index',None)
        page_list=self.get_page_list(uid)
        del page_list[int(del_page_index)]
        #print('del_page_name',del_page_index,type(del_page_index))
        #print('page_list', page_list, type(page_list))
        self.page_list_to_db(uid,page_list)
        self.redirect('/viewpage')



class Memo(BaseHandler):
    def get(self):
        uid = self.get_uid()



        input_file = codecs.open("../word_card2/static/memo/to_do.md", mode="r", encoding="utf-8")
        text = input_file.read()
        todolist = markdown.markdown(text)
        #print(memo1)

        input_file = codecs.open("../word_card2/static/memo/usage.md", mode="r", encoding="utf-8")
        text = input_file.read()
        usage = markdown.markdown(text)
        #print(usage)


        self.render('./static/memo.html',todolist=todolist,usage=usage)


def make_app():
    # tornado 路由设置
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/temptest",TempTest),
        (r"/view", ViewHandler),
        (r"/imagechoice", ImageChoiceHandler),
        (r"/updateimage", UpdateImage),
        (r"/clearallword", ClearAllWord),
        (r"/createpage", CreatePage),
        (r"/createpdf", CreatePdf),
        (r"/get_batch_word",GetBatchWord),
        (r"/insert_batch_word",InsertBatchWord),
        (r"/memo", Memo),
        (r"/viewpage",ViewPageHandler),
        (r"/delpage",DelPage),
        (r"/randomfill", RandomFill),
        #(r"/imagechose/",ImagechoseHandler),
        #(r"/added/", AddedHandler),

        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': './static'}),

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
    app.listen(3333)
    tornado.ioloop.IOLoop.current().start()