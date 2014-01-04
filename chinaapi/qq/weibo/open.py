# coding=utf-8
from chinaapi.open import ClientBase, Method, OAuth2Base, Token as TokenBase, App
from chinaapi.exceptions import InvalidApi, ApiResponseError
from chinaapi.utils import parse_querystring


IS_POST_METHOD = {
    'user': lambda m: m in ['verify'],
    'friends': lambda m: m in ['addspecial', 'delspecial', 'addblacklist', 'delblacklist'],
    't': lambda m: m in ['re_add', 'reply', 'comment', 'like', 'unlike'],
    'fav': lambda m: m in ['addht', 'addt', 'delht', 'delt'],
    'vote': lambda m: m in ['createvote', 'vote'],
    'list': lambda m: m != 'timeline', # 只有timeline接口是读接口，其他全是写接口
    'lbs': lambda m: True  # 全是写接口
}

DEFAULT_IS_POST_METHOD = lambda m: False

RET = {
    0: u'成功返回',
    1: u'参数错误',
    2: u'频率受限',
    3: u'鉴权失败',
    4: u'服务器内部错误',
    5: u'用户错误',
    6: u'未注册微博',
    7: u'未实名认证'
}


def parse(response):
    r = response.json_dict()
    if 'ret' in r and r.ret != 0:
        raise ApiResponseError(response, r.ret, RET.get(r.ret, u''), r.get('errcode', ''), r.get('msg', ''))
    if 'data' in r:
        return r.data
    return r


class Client(ClientBase):
    #写接口
    _post_methods = ['add', 'del', 'create', 'delete', 'update', 'upload']

    def __init__(self, app=App()):
        super(Client, self).__init__(app, Token())
        self.openid = None
        self.clientip = None

    def set_openid(self, openid):
        self.openid = openid

    def set_clientip(self, clientip):
        self.clientip = clientip

    def _parse_response(self, response):
        return parse(response)

    def _prepare_url(self, segments, queries):
        """
        因del为Python保留字，无法作为方法名，需将del替换为delete，并在此处进行反向转换。
        """
        if segments[-1] == 'delete' and segments[-2] != 'list':  # list本身有delete方法，需排除
            segments[-1] = 'del'
        return 'https://open.t.qq.com/api/{0}'.format('/'.join(segments))

    def _prepare_method(self, segments):
        if len(segments) != 2:
            raise InvalidApi(self._prepare_url(segments, None))
        model, method = tuple([segment.lower() for segment in segments])
        if method.split('_')[0] in self._post_methods:
            return Method.POST
        elif IS_POST_METHOD.get(model, DEFAULT_IS_POST_METHOD)(method):
            return Method.POST
        return Method.GET

    def _prepare_queries(self, queries):
        queries.update(oauth_version='2.a', format='json', oauth_consumer_key=self.app.key)
        if not self.token.is_expires:
            queries['access_token'] = self.token.access_token
        if self.openid:
            queries['openid'] = self.openid
        if 'clientip' not in queries and self.clientip:
            queries['clientip'] = self.clientip


class Token(TokenBase):
    """
    openid：用户统一标识，可以唯一标识一个用户
    openkey：与openid对应的用户key，是验证openid身份的验证密钥
    """

    def __init__(self, access_token=None, expires_in=None, refresh_token=None, **kwargs):
        super(Token, self).__init__(access_token, expires_in, refresh_token, **kwargs)
        self.openid = kwargs.pop('openid', None)
        self.openkey = kwargs.pop('openkey', None)
        self.name = kwargs.pop('name', None)


class OAuth2(OAuth2Base):
    def __init__(self, app):
        super(OAuth2, self).__init__(app, 'https://open.t.qq.com/cgi-bin/oauth2/')

    def _parse_response(self, response):
        return parse(response)

    def _parse_token(self, response):
        data = parse_querystring(response.text)
        if 'errorCode' in data:
            raise ApiResponseError(response, data['errorCode'], data.get('errorMsg', '').strip("'"))
        return Token(**data)

    def revoke(self, **kwargs):
        """ 取消授权
        请求参数：oauth或openid&openkey标准参数
        返回是否成功取消
        """
        kwargs['format'] = 'json'
        response = self._session.get('http://open.t.qq.com/api/auth/revoke_auth', params=kwargs)
        self._parse_response(response)
        return True  # 没有异常说明ret=0（ret: 0-成功，非0-失败）