# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : db_controler.py
# Time       ：2021/11/9 22:15
# Author     ：Gao Shan
# Description：
"""

import sqlite3
import os
import json

class DBControler(object):
    '''
    数据库控制
    '''

    def __init__(self,filename,verbose=False):
        self.__dbname=filename
        # 如果数据库不在内存中
        # conn = sqlite3.connect(':memory:')
        if filename != ':memory:':
            os.path.abspath(filename)
        self.__conn = None
        self.__verbose=verbose
        self.__open()

    def __open(self):
        sql='''
        CREATE TABLE IF NOT EXISTS "user_config"(
        "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
        "user_config" TEXT,
        "user_infor" TEXT
        
        );
        CREATE UNIQUE INDEX IF NOT EXISTS "user_config_1" ON user_config (id);
        
        
        '''
        self.__conn = sqlite3.connect(self.__dbname,isolation_level = "IMMEDIATE")
        self.__conn.isolation_level = "IMMEDIATE"

        sql = '\n'.join([n.strip('\t') for n in sql.split('\n')])
        sql = sql.strip('\n')

        self.__conn.executescript(sql)
        self.__conn.commit()
        fields = ('id','user_config',"user_infor")
        self.__fields = tuple([(fields[i], i) for i in range(len(fields))])
        self.__names = {}
        for k, v in self.__fields:
            self.__names[k] = v
        self.__enable = self.__fields[1:]
        return True

        # 关闭数据库

    def close(self):
        if self.__conn:
            self.__conn.close()
        self.__conn = None

    def __del__ (self):
        self.close()




        # 数据库记录转化为字典

    def __record2obj(self, record):
        if record is None:
            return None
        word = {}
        for k, v in self.__fields:
            word[k] = record[v]
        return word
        # 查询单词

    def query(self, key):
        c = self.__conn.cursor()
        record = None
        if isinstance(key, int):
            c.execute('select * from user_config where id = ?;', (key,))
        else:
            return None
        record = c.fetchone()
        return self.__record2obj(record)


    # 输出日志
    def out (self, text):
        if self.__verbose:
            print(text)
        return True



    # 取得总数
    def count (self):
        c = self.__conn.cursor()
        c.execute('select count(*) from user_config;')
        record = c.fetchone()
        return record[0]

    def register (self, id=None,):
        sql = 'INSERT INTO user_config (id) VALUES(?);'
        try:
            self.__conn.execute(sql, (id,))
        except sqlite3.IntegrityError as e:
            self.out(str(e))
            return False
        except sqlite3.Error as e:
            self.out(str(e))
            return False
        self.__conn.commit()
        #self.update(id, items, commit)
        return True


    #删除记录
    def remove (self, key, commit = True):
        if isinstance(key, int):
            sql = 'DELETE FROM user_config WHERE id=?;'
        try:
            self.__conn.execute(sql, (key,))
            if commit:
                self.__conn.commit()
        except sqlite3.IntegrityError:
            return False
        return True

    ## 更新单词数据
    # item 传入字典
    def update (self, key, items, commit = True):
        names = []
        values = []
        for name, id in self.__enable:
            if name in items:
                names.append(name)
                value = items[name]
                if value is not None:
                    value = json.dumps(value, ensure_ascii=False)

                values.append(value)
        if len(names) == 0:
            if commit:
                try:
                    self.__conn.commit()
                except sqlite3.IntegrityError:
                    return False
            return False
        sql = 'UPDATE user_config SET ' + ', '.join(['%s=?'%n for n in names])
        if isinstance(key,int):
            sql += ' WHERE id=?;'
        try:
            self.__conn.execute(sql, tuple(values + [key]))
            if commit:
                self.__conn.commit()
        except sqlite3.IntegrityError:
            return False
        return True

     # 浏览词典
    def __iter__ (self):
        c = self.__conn.cursor()
        sql = 'select "id" from "user_config"'
        sql += ' order by "id" ;'
        c.execute(sql)
        return c.__iter__()


      #长度
    def __len__ (self):
        return self.count()



    def __contains__ (self, key):
        return self.query(key) is not None


    def __getitem__ (self, key):
        return self.query(key)

    #提交变更
    def commit(self):
        try:
            self.__conn.commit()
        except sqlite3.IntegrityError:
            self.__conn.rollback()
            return False
        return True

    #
    def dumps (self):
        return [ n[0] for  n in self.__iter__() ]