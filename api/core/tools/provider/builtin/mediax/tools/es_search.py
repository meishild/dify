from typing import Any, Union
import json
import logging
import requests
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

class ESSearch():
    def __init__(self, domain: str) -> None:
        self.domain = domain

    def query(self, query, index_name, source_includes):
        import json

        query_json = json.loads(query)
        _source = query_json.get('_source', {})
        if source_includes:
            includes_list = source_includes.split(",")
            if "includes" in _source:
                _source['includes'].extend(includes_list)
            else:
                _source['includes'] = includes_list
        else:
            _source['excludes'] = _source.get('excludes', []) + ['imageFeature']
        query_json['_source'] = _source

        url = f"{self.domain}/data_access/elasticsearch/query/{index_name}/_search"
        headers = {"Content-Type": "application/json"}

        logging.info("\n查询条件:"+ json.dumps(query_json))
        response = requests.post(url, data=json.dumps(query_json), headers=headers)
        result = response.json() 
        logging.info("\n请求结果：" + json.dumps(result, ensure_ascii=True))
        return {
            "datas": result,
            "query": query_json,
        }

class ESSearchTool(BuiltinTool):
    def _invoke(self, 
                user_id: str,
               tool_parameters: dict[str, Any], 
        ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
            invoke tools
        """
        domain = tool_parameters['domain']
        es_searcher = ESSearch(domain)

        query = tool_parameters['query']
        index_name = tool_parameters.get('index_name', None)
        source_includes = tool_parameters.get('source_includes', None)
        
        datas = es_searcher.query(query, index_name=index_name, source_includes=source_includes)
        
        return self.create_json_message(datas)
        