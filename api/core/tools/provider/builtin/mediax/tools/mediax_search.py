from typing import Any, Union
import json
import logging
import requests
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class MediaxSearch():
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

    def mediax_search(self, keyword, page_no=1, page_size=20, hit_propert=None, media_types=None):
        from urllib.parse import urlencode
        import json
        
        sign_url = self.get_sign_url()

        url = f"{self.domain}/openapi/mediax/search/v1"
        """
        pageForm: 是当前页数。
        hitPropert: 是搜索过程中用的命中条件，该参数是一个英文单词；
        搜索命中，过滤字段，不传是所有
        语言，人脸，字幕，标题，视频标签，图片标签，音频标签，文本标签，说明，类似命中
        asr,face,ocr,title,videoTag,imageTag,audioTag,textTag,content，similarPart
        keyword是搜索用的关键词，或者搜索用的名称。
        媒资类型:
        video
        image
        audio 
        draft,doc
        epaper
        file
        folder
        """
        
        data = {
            "keyword": keyword,
            "pageForm": page_no,
            "pageSize": page_size
        }
        if hit_propert:
            data['hitPropert'] = hit_propert
        if media_types:
            data['mediaTypes'] = media_types
        else:
            data['mediaTypes'] = "video,audio,image"

        url = url + "?" + urlencode(data)  + "&" + sign_url
        
        response = requests.get(url)
        result = response.json()
        logging.info("\n请求结果：" + json.dumps(result, ensure_ascii=True))
        if result['code'] != '00000':
            return False, result

        # 需要格式化接口的输出
        media_list = result["data"]["data"]
        if len(media_list) == 0:
            return True, []
        
        return True, [{
            "媒资编号": item["mediaId"],
            "媒资标题": item["title"],
            "媒资地址": item["url"]
            } for item in media_list
        ]

class MediaxSearchTool(BuiltinTool):
    def _invoke(self, 
                user_id: str,
               tool_parameters: dict[str, Any], 
        ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
            invoke tools
        """
        mediax_ak = self.runtime.credentials['mediax_ak']
        mediax_sk = self.runtime.credentials['mediax_sk']
        mediax_api_domain = self.runtime.credentials['mediax_api_domain']
        media_searcher = MediaxSearch(mediax_api_domain, mediax_ak, mediax_sk)

        keyword = tool_parameters['keyword']
        hit_propert = tool_parameters.get('hit_propert', None)
        media_types = tool_parameters.get('media_types', None)
        is_success ,datas = media_searcher.mediax_search(
            keyword, hit_propert=hit_propert, media_types=media_types)
        if not is_success:
            raise Exception(f'绑定失败: {json.dumps(datas, ensure_ascii=False)}')

        return self.create_text_message(text=json.dumps(datas, ensure_ascii=False))