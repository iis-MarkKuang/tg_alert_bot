import hmac
import hashlib
import base64

# 初始化参数
key = "AKIA4Y34TXGODF63GIMX"
region = "us-east-1"
date = "20250421"
service = "ses"
terminal = "aws4_request"
message = "SendRawEmail"
version = 0x04


# 定义 HmacSha256 函数
def hmac_sha256(key, msg):
    # 确保 key 是 bytes 类型
    if isinstance(key, str):
        key = key.encode('utf-8')
    # 确保 msg 是 bytes 类型
    if isinstance(msg, str):
        msg = msg.encode('utf-8')
    return hmac.new(key, msg, hashlib.sha256).digest()


if __name__ == '__main__':
    # 计算 kDate
    kDate = hmac_sha256("AWS4" + key, date)
    # 计算 kRegion
    kRegion = hmac_sha256(kDate, region)
    # 计算 kService
    kService = hmac_sha256(kRegion, service)
    # 计算 kTerminal
    kTerminal = hmac_sha256(kService, terminal)
    # 计算 kMessage
    kMessage = hmac_sha256(kTerminal, message)

    # 拼接版本和 kMessage
    signature_and_version = bytes([version]) + kMessage
    # 进行 Base64 编码
    smtp_password = base64.b64encode(signature_and_version).decode('utf-8')

    print(smtp_password)