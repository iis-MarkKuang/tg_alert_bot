import hmac
import hashlib
import base64

# 替换为你的 IAM 用户的秘密访问密钥
SECRET_ACCESS_KEY = 'BCyU3r4fbHZL4nfzxuUqV5VV3BVnEVSV5gnRFUvQEWUg'
# 替换为你的 AWS 区域，例如 'us-east-1'
AWS_REGION = 'us-east-1'
# 常量
MESSAGE = 'SendRawEmail'
VERSION = chr(2)

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_smtp_password(secret_access_key, region):
    date = '20250421'
    region = region
    service = 'ses'
    message = MESSAGE
    version = VERSION

    kDate = sign(('AWS4' + secret_access_key).encode('utf-8'), date)
    kRegion = sign(kDate, region)
    kService = sign(kRegion, service)
    kSigning = sign(kService, 'aws4_request')
    signature = sign(kSigning, message)
    smtp_password = base64.b64encode((version + str(signature)).encode('utf-8')).decode('utf-8')
    return smtp_password

if __name__ == '__main__':
    smtp_password = get_smtp_password(SECRET_ACCESS_KEY, AWS_REGION)
    print(smtp_password)