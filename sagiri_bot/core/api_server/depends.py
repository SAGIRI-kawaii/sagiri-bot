import hmac
import time
import base64


def generate_token(user_name: str, nonce: str, expire: int = 86400):
    """
    @Args:
        user_name: 用户名
        nonce: 随机字符串
        expire: int(最大有效时间，单位为s)
    @Return:
        state: str
    """
    ts_str = str(time.time() + expire)
    ts_byte = ts_str.encode("utf-8")
    sha1_tshex_str = hmac.new((user_name + nonce).encode("utf-8"), ts_byte, 'sha1').hexdigest()
    token = ts_str + ':' + sha1_tshex_str
    b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
    return b64_token.decode("utf-8")


def certify_token(user_name: str, nonce: str, token: str = None):
    """
    @Args:
        user_name: 用户名
        nonce: 随机字符串
        token: token
    @Returns:
        boolean
    """
    token_str = base64.urlsafe_b64decode(token).decode('utf-8')
    token_list = token_str.split(':')
    if len(token_list) != 2:
        return False
    ts_str = token_list[0]
    if float(ts_str) < time.time():
        return False
    known_sha1_tsstr = token_list[1]
    sha1 = hmac.new((user_name + nonce).encode("utf-8"), ts_str.encode('utf-8'), 'sha1')
    calc_sha1_tsstr = sha1.hexdigest()
    return calc_sha1_tsstr == known_sha1_tsstr
