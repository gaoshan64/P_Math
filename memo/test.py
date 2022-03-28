# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : test.py
# Time       ：2022/2/11 1:25
# Author     ：Gao Shan
# Description：
"""


def decode_list(list):
    list_finish = []
    for x in list:
        y = x.decode("utf-8")
        list_finish.append(y)
    return list_finish


a={"step": ["3"], "is_result": ["0"], "is_bracket": [""], "carry": ["1"], "abdication": ["1"], "remainder": ["2"], "multistep_a1": ["1"], "multistep_a2": ["100"], "multistep_b1": ["1"], "multistep_b2": ["100"], "multistep_c1": ["1"], "multistep_c2": ["100"], "multistep_d1": ["1"], "multistep_d2": ["100"], "multistep_e1": ["0"], "multistep_e2": ["1000"], "symbols_a": ["1", "2", "3", "4"], "symbols_b": ["1", "2", "3", "4"], "symbols_c": ["1", "2", "3", "4"], "jz_title": ["数学测试"], "inf_title": ["姓名：__________ 日期：____月____日 用时：________ 正确率：____"], "number": ["50"]}