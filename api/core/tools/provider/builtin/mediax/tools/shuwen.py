import logging
import requests

class SignTool():
    def __init__(self, domain: str, access_key: str, secret_key: str) -> None:
        """Initialize SerpAPI tool provider."""
        self.access_key = access_key 
        self.secret_key = secret_key
        self.domain = domain

    def get_signature(self, timestamp):
        import hashlib

        need_signature_str = f"{self.secret_key}{timestamp}{self.access_key}"
        logging.info(need_signature_str)
        try:
            md5 = hashlib.md5()
            md5.update(need_signature_str.encode('utf-8'))
            summery = md5.hexdigest()
            return summery
        except Exception as e:
            logging.error("获取签名串失败", exc_info=e)
            return ""

    def get_sign_url(self):
        import time
        current_time = str(int(time.time() * 1000))
        
        sign = self.get_signature(current_time)
        biz_param = {
            'signature' : sign,
            'access_key': self.access_key,
            'timestamp': current_time,
        }
        return '&'.join([f"{key}={value}" for key, value in biz_param.items()])
