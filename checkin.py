#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: checkin.py(飞牛NAS社区签到)
Author: Gaopan
cron: 30 8 * * *
new Env('飞牛NAS社区签到');
Update: 2025/3/20
"""

import os
import requests
from bs4 import BeautifulSoup
import sys

# 加载通知服务
def load_send():
    cur_path = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(cur_path)
    if os.path.exists(cur_path + "/sendNotify.py"):
        try:
            from sendNotify import send
            return send
        except Exception as e:
            print(f"加载通知服务失败：{e}")
            return None
    else:
        print("加载通知服务失败")
        return None

def parse_cookie(cookie_str: str) -> dict:
    """
    将Cookie字符串解析为字典格式
    示例输入："pvRK_2132_saltkey=abc; pvRK_2132_auth=123"
    返回：{'pvRK_2132_saltkey': 'abc', 'pvRK_2132_auth': '123'}
    """
    cookie_dict = {}
    # 分割每个Cookie条目
    for item in cookie_str.split(';'):
        # 去除首尾空格后分割键值对
        key_value = item.strip().split('=', 1)
        if len(key_value) == 2:
            cookie_dict[key_value[0]] = key_value[1]
    return cookie_dict

# 从环境变量读取配置信息
COOKIE_STR = os.getenv('FN_COOKIE', '')        # 完整的Cookie字符串,名称自己按需修改
FN_SIGN = os.getenv('fn_pvRK_2132_sign', '')   # 签到请求的签名参数,名称自己按需修改

# 解析Cookie获取关键参数
cookie_dict = parse_cookie(COOKIE_STR)
required_cookies = {
    'pvRK_2132_saltkey': cookie_dict.get('pvRK_2132_saltkey'),
    'pvRK_2132_auth': cookie_dict.get('pvRK_2132_auth')
}

def sign_in():
    """
    执行签到操作，处理三种状态：
    1. 签到成功 2. 已签到 3. 签到失败
    """
    try:
        # 构建签到请求URL（需要签名参数）
        sign_url = f'https://club.fnnas.com/plugin.php?id=zqlj_sign&sign={FN_SIGN}'
        response = requests.get(sign_url, cookies=required_cookies)

        if '恭喜您，打卡成功！' in response.text:
            print('✅ 签到成功')
            get_sign_in_info()
        elif '您今天已经打过卡了' in response.text:
            print('⏰ 今日已签到')
            get_sign_in_info()
        else:
            error_msg = '❌ 失败：Cookie可能失效或网站改版'
            return error_msg

    except Exception as e:
        error_msg = f'🚨 请求异常：{str(e)}'
        return error_msg

def get_check_in_info():
    """
    获取签到详情数据并推送
    使用CSS选择器定位关键数据
    """
    try:
        response = requests.get('https://club.fnnas.com/plugin.php?id=zqlj_sign', 
                              cookies=required_cookies)
        soup = BeautifulSoup(response.text, 'html.parser')
  
        # 定义需要抓取的数据项和对应CSS选择器
        target_data = {
            '最近打卡': 'li:-soup-contains("最近打卡")',
            '本月打卡': 'li:-soup-contains("本月打卡")',
            '连续打卡': 'li:-soup-contains("连续打卡")',
            '累计打卡': 'li:-soup-contains("累计打卡")',
            '累计奖励': 'li:-soup-contains("累计奖励")',
            '最近奖励': 'li:-soup-contains("最近奖励")',
            '当前等级': 'li:-soup-contains("当前打卡等级")',
        }

        # 提取并格式化数据
        result = []
        for name, selector in target_data.items():
            element = soup.select_one(selector)
            if element:
                # 提取文本并分割出数值部分
                text = element.get_text().split('：')[-1].strip()
                result.append(f'{name}: {text}')

        # 推送格式化后的消息
        if result:
            msg_content = '\n'.join(result)
            print('📊 签到详情：\n')
            return msg_content
        else:
            raise Exception('未找到签到数据，页面结构可能已变更')

    except Exception as e:
        error_msg = f'抓取详情失败：{str(e)}'
        print(error_msg)


def validate_config():
    """
    启动前校验必要配置
    """
    errors = []
    if not COOKIE_STR:
        errors.append('缺少FN_COOKIE环境变量')
    if not FN_SIGN:
        errors.append('缺少fn_pvRK_2132_sign环境变量')
    if not required_cookies.get('pvRK_2132_saltkey'):
        errors.append('Cookie中缺少pvRK_2132_saltkey')
    if not required_cookies.get('pvRK_2132_auth'):
        errors.append('Cookie中缺少pvRK_2132_auth')
  
    if errors:
        print('❌ 配置错误：')
        print('\n'.join(errors))
        exit(1)

if __name__ == '__main__':
    # 启动时先验证配置
    validate_config()
    print('🔍 配置校验通过，开始执行签到')
    sign_in()
    title = "飞牛NAS签到通知"
    contents = get_check_in_info()
    send_notify = load_send()
    if send_notify:
        if contents =='':
            contents=f'签到失败，请检查账户信息以及网络环境'
            print(contents)
        send_notify(title, contents)