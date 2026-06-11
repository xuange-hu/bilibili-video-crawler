"""
B站 WBI 签名模块
用于生成B站API请求所需的签名参数 w_rid 和 wts
"""

import hashlib
import time
import re
import json
from typing import Dict, Any
import httpx


class WbiSign:
    """B站 WBI 签名类"""
    
    # WBI混淆顺序表
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 11, 20, 56, 21, 34, 52, 11, 37,
    ]
    
    def __init__(self):
        self.img_key = ""
        self.sub_key = ""
        self.last_update = 0
        self.update_interval = 3600  # 1小时更新一次
    
    def _get_mixin_key(self) -> str:
        """获取混合密钥 - 正确的算法"""
        # 原始的 img_key + sub_key
        orig_key = self.img_key + self.sub_key
        # 根据混淆表重新排列
        mixin_key = ""
        for i in self.MIXIN_KEY_ENC_TAB:
            if i < len(orig_key):
                mixin_key += orig_key[i]
        return mixin_key[:32]
    
    def _get_sign(self, data: Dict[str, Any]) -> str:
        """计算签名"""
        # 将参数按字母顺序排序
        items = sorted(data.items())
        query_string = "&".join([f"{k}={v}" for k, v in items])
        
        # 获取混合密钥
        mixin_key = self._get_mixin_key()
        
        # 计算签名：SHA256(参数字符串 + 混合密钥)
        sign_str = query_string + mixin_key
        return hashlib.sha256(sign_str.encode()).hexdigest()
    
    def update_keys(self, img_key: str, sub_key: str):
        """更新密钥"""
        self.img_key = img_key
        self.sub_key = sub_key
        self.last_update = time.time()
    
    def need_update(self) -> bool:
        """检查是否需要更新密钥"""
        return time.time() - self.last_update > self.update_interval
    
    def sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        对参数进行签名
        
        Args:
            params: 请求参数字典
            
        Returns:
            添加了签名的参数字典
        """
        if not self.img_key or not self.sub_key:
            return params
        
        # 添加时间戳
        params['wts'] = int(time.time())
        
        # 计算签名
        w_rid = self._get_sign(params)
        params['w_rid'] = w_rid
        
        return params
    
    @staticmethod
    def fetch_keys() -> tuple:
        """
        从B站获取 WBI 密钥
        
        Returns:
            (img_key, sub_key) 元组
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
            }
            
            # 获取导航页面，从中提取密钥
            response = httpx.get(
                'https://api.bilibili.com/x/web-interface/nav',
                headers=headers,
                timeout=10,
                follow_redirects=True
            )
            
            response.raise_for_status()
            data = response.json()
            if data.get('code') != 0:
                return "", ""
            
            wbi_img = data.get('data', {}).get('wbi_img', {})
            if not wbi_img:
                return "", ""
            
            # 从图片URL提取img_key
            img_url = wbi_img.get('img_url', '')
            img_key = re.findall(r'/([a-zA-Z0-9_-]+)\.png', img_url)
            img_key = img_key[0] if img_key else ""
            
            # 从子图片URL提取sub_key
            sub_url = wbi_img.get('sub_url', '')
            sub_key = re.findall(r'/([a-zA-Z0-9_-]+)\.png', sub_url)
            sub_key = sub_key[0] if sub_key else ""
            
            return img_key, sub_key
        except Exception as e:
            print(f"获取WBI密钥失败: {e}")
            return "", ""


# 全局WBI签名实例
wbi_sign = WbiSign()
