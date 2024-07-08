from typing import Any, Union
import json
import logging
import requests
from core.tools.provider.builtin.mediax.tools.shuwen import SignTool
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

class MediaxSearch():
    def __init__(self, api_domain, ak, sk) -> None:
        self.sign_tool = SignTool(api_domain, ak, sk)

    def mediax_search(self, keyword, page_no=1, page_size=20, hit_propert=None, media_types=None):
        from urllib.parse import urlencode
        import json
        
        sign_url = self.sign_tool.get_sign_url()

        url = f"{self.domain}/openapi/mediax/search/v1"
        
        data = {
            "keyword": keyword,
            "pageForm": page_no,
            "pageSize": page_size
        }

        # 不设置命中条件默认全部
        if hit_propert and hit_propert != "ALL":
            data['hitPropert'] = hit_propert

        # 为空默认设置图片、音频、视频。
        if media_types is None or media_types == "ALL":
            data['mediaTypes'] = "video,audio,image"
        else:
            data['mediaTypes'] = media_types

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
        
        return True, media_list

class MediaxSearchTool(BuiltinTool):
    def create_image_link_message(self, image: str, meta: dict = None, save_as: str = '') -> ToolInvokeMessage:
        """
            create an image message

            :param image: the url of the image
            :return: the image message
        """
        return ToolInvokeMessage(
            type=ToolInvokeMessage.MessageType.IMAGE_LINK, 
            message=image, 
            meta=meta,
            save_as=save_as
        )
   
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
        top_n = tool_parameters.get('top_n', None)
        return_type = tool_parameters.get('return_type')
        is_success ,datas = media_searcher.mediax_search(
            keyword, hit_propert=hit_propert, media_types=media_types, page_size=top_n)
        if not is_success:
            raise Exception(f'绑定失败: {json.dumps(datas, ensure_ascii=False)}')

        if return_type == "json":
            json_datas = [{
                "媒资编号": item["mediaId"],
                "媒资标题": item["title"],
                "媒资地址": item["url"]
                } for item in datas
            ]
            return self.create_text_message(text=json.dumps(json_datas, ensure_ascii=False))
        else:
            # result = []
            # for item in datas:
                # if item['mediaType'] == "image":
                #     m_type = item['subMediaType']
                #     logging.info("find image: " + item["url"])
                #     result.append(
                #         self.create_image_message(
                #             item["url"],
                #             # meta={'mime_type': f'image/{m_type}'}
                #         )
                #     )
            
            markdown = "## 检索到的内容如下：\n"
            other_list = []
            for item in datas:
                if item['mediaType'] == "image":
                    markdown += f"#### {item['title']}\n"
                    markdown += f"* 媒资编号: {item['mediaId']}\n"
                    markdown += f"![图片]({item['url']})\n\n"
                elif item['mediaType'] == "video" or item['mediaType'] == "audio":
                    other_list.append(item)
            for item in other_list:
                markdown += f"[{item['title']}]({item['url']})\n\n"
            
            result = self.create_text_message(text=markdown)
        return result
       