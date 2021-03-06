import base64
import json

import requests
from graia.application.entry import Image, Plain

class TextureBase(object):
    url: str
    hash: str

class TextureProvider(object):
    class No(object):
        description = '无'
    
    class LittleSkin(object):
        description = 'LittleSkin'

    class Mojang(object):
        description = 'Mojang'


class TextureModel(object):
    class No(object):
        description = '无'
    
    class slim(object):
        description = 'slim'

    class default(object):
        description = 'default'


class YggdrasilProfile():
    uuid: str
    name: str

    class skin(TextureBase):
        '''皮肤'''
        pass

    class cape(TextureBase):
        '''披风'''
        pass

    def __init__(self, yggdrasil_profile: dict):
        self.uuid = yggdrasil_profile['profileId']
        self.name = yggdrasil_profile['profileName']

        if 'SKIN' in yggdrasil_profile['textures']:
            self.skin.model = TextureModel.slim() if 'metadata' in yggdrasil_profile[
                'textures']['SKIN'] else TextureModel.default()
            self.skin.url = yggdrasil_profile['textures']['SKIN']['url']
            self.skin.hash = self.getHashFromUrl(self.skin.url)
            self.skin.provider = self.getTextureProvider(self.skin.url)
        else:
            self.skin.model = TextureModel.No()
            self.skin.url = None
            self.skin.hash = None
            self.skin.provider = TextureProvider.No()

        if 'CAPE' in yggdrasil_profile['textures']:
            self.cape.url = yggdrasil_profile['textures']['CAPE']['url']
            self.cape.provider = self.getTextureProvider(self.cape.url)
            self.cape.hash = self.getHashFromUrl(self.cape.url)
        else:
            self.cape.url = None
            self.cape.provider = TextureProvider.No()
            self.cape.hash = None

    @staticmethod
    def getHashFromUrl(url: str) -> str:
        _hash = url.split('/')[-1]
        return _hash

    @staticmethod
    def getTextureProvider(url: str) -> str:
        _provider = TextureProvider.LittleSkin() if 'mcskin.littleservice.cn' in url else TextureProvider.Mojang()
        return _provider


class PlayerProfile():
    def __init__(self, player_name: str):
        self.playerName = player_name

    @staticmethod
    def getPreviewByHash(texture_hash: str) -> Image:
        '''通过 hash 获取 Image 对象'''
        r = requests.get(
            f'https://mcskin.littleservice.cn/preview/hash/{texture_hash}?png')
        if r.status_code == 200:
            return Image.fromUnsafeBytes(r.content)
        else:
            return None

    def previewImage(self, skin_hash: str, cape_hash: str) -> list:
        '''获取皮肤和披风的预览图

        使用方法：
        ``` python
        *self.previewImage(skin_hash, cape_hash)
        ```'''
        _l = list()
        if skin_hash:
            _l.append(self.getPreviewByHash(skin_hash))
        if cape_hash:
            _l.append(self.getPreviewByHash(cape_hash))
        return _l

    def getCsl(self) -> list:
        r = requests.get(
            f'https://mcskin.littleservice.cn/csl/{self.playerName}.json')
        j = r.json()
        if 'username' in j:
            name = j['username']
            skin_type = 'default' if 'default' in j['skins'] else 'slim'
            skin_hash = j['skins'][skin_type] if j['skins'][skin_type] else None
            cape_hash = j['cape'] if j['cape'] else None
            return [Plain(f'''角色名：{name}
模型：{skin_type}
皮肤：{skin_hash}
披风：{cape_hash}
'''), *self.previewImage(skin_hash, cape_hash)]
        else:
            return [Plain(f'Error: Player {self.playerName} not found')]

    def getYgg(self) -> list:
        r1 = requests.post(
            'https://mcskin.littleservice.cn/api/yggdrasil/api/profiles/minecraft', json=[self.playerName])
        s1 = r1.json()
        if s1 == []:
            return [Plain(f'Error: Player {self.playerName} not found')]
        #
        player_uuid = s1[0]['id']
        r2 = requests.get(
            f'https://mcskin.littleservice.cn/api/yggdrasil/sessionserver/session/minecraft/profile/{player_uuid}')
        s2 = r2.json()
        unbase64ed = s2['properties'][0]['value']
        _gameprofile = base64.b64decode(unbase64ed)

        #
        gameprofile = YggdrasilProfile(json.loads(_gameprofile))
        return [Plain(f'''角色名：{gameprofile.name}
UUID：{gameprofile.uuid}
模型：{gameprofile.skin.model.description}
皮肤：{gameprofile.skin.hash} ({gameprofile.skin.provider.description})
披风：{gameprofile.cape.hash} ({gameprofile.cape.provider.description})
'''), *self.previewImage(gameprofile.skin.hash if isinstance(gameprofile.skin.provider, TextureProvider.LittleSkin) else None,
                         gameprofile.cape.hash if isinstance(gameprofile.cape.provider, TextureProvider.LittleSkin) else None)]
