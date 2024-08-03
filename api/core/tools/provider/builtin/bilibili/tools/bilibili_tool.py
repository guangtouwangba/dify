from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class BilibiliTool(BuiltinTool):

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[
        ToolInvokeMessage, list[ToolInvokeMessage]]:
        pass

    def get_video_info(self, bv_id):
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
        headers = {
            'User-Agent': self.config.get('user_agent'),
            'Referer': 'https://www.bilibili.com/',
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        if data['code'] != 0:
            return None
        video_info = data['data']
        return video_info

    def get_video_download_url(self, bv_id):
        video_info = self.get_video_info(bv_id)
        if video_info is None:
            return None
        video_title = video_info['title']
        video_pages = video_info['pages']
        video_page = video_pages[0]
        video_cid = video_page['cid']
        video_url = f'https://api.bilibili.com/x/player/playurl?cid={video_cid}&bvid={bv_id}&qn=112'
        headers = {
            'User-Agent': self.config.get('user_agent'),
            'Referer': f'https://www.bilibili.com/video/{bv_id}',
        }
        response = requests.get(video_url, headers=headers)
        data = response.json()
        video_download_url = data['data']['durl'][0]['url']
        return video_title, video_download_url

    def download_video(self, bv_id, output_dir):
        video_info = self.get_video_info(bv_id)
        if video_info is None:
            return False
        video_title = video_info['title']
        video_pages = video_info['pages']
        video_page = video_pages[0]
        video_cid = video_page['cid']
        video_url = f'https://api.bilibili.com/x/player/playurl?cid={video_cid}&bvid={bv_id}&qn=112'
        headers = {
            'User-Agent': self.config.get('user_agent'),
            'Referer': f'https://www.bilibili.com/video/{bv_id}',
        }
        response = requests.get(video_url, headers=headers)
        data = response.json()
        video_download_url = data['data']['durl'][0]['url']
        video_file_path = os.path.join(output_dir, f'{video_title}.flv')
        response = requests.get(video_download_url, headers=headers, stream=True)
        with open(video_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        return True
