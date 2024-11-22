import requests
import time
import json
import hashlib
from Crypto.Cipher import AES
from binascii import b2a_hex
import smtplib
from email.mime.text import MIMEText

# AES加密函数
def AES_encrypt(data):
    BLOCK_SIZE = 16  # Bytes
    secret_key = "23DbtQHR2UMbH6mJ"
    pad = lambda s: (s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE))
    cipher = AES.new(secret_key.encode(), AES.MODE_ECB)
    encrypted_text = cipher.encrypt(bytes(pad(str(data)), encoding='utf-8'))
    encrypted_text_hex = str(b2a_hex(encrypted_text), encoding='utf-8')
    return encrypted_text_hex


loginUrl = 'https://api.moguding.net:9000/session/user/v3/login'
saveUrl = "https://api.moguding.net:9000/attendence/clock/v2/save"

# 获取 Token
def getToken(account, password):
    data = {
        "password": AES_encrypt(password),  # 密码
        "t": AES_encrypt(int(time.time() * 1000)),
        "phone": AES_encrypt(account),  # 账号
        "loginType": "android",
        "uuid": ""
    }
    resp = postUrl(loginUrl, data=data, headers={'content-type': 'application/json; charset=UTF-8',
                                                 'User-Agent': 'Mozilla/5.0 (Linux; U; Android 10; zh-cn; MIX 3 Build/QKQ1.190828.002) '
                                                               'AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1',
                                                 })

    # 打印响应内容以调试
    print("API Response:", resp)

    # 检查 'data' 是否存在
    if 'data' in resp:
        return resp['data']['token']
    else:
        print("Error: 'data' key not found in response.")
        return None


# POST 请求函数
def postUrl(url, headers, data):
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    return resp.json()

# 执行签到
def clock_in(account, password, address, province, city, clock_type):
    mail_host = "smtp.qq.com"
    mail_user = ""  # 发送人邮箱
    mail_pass = "nxpkpuuquwcjdied"  # 授权码
    sender = ''  # 发件人邮箱
    receivers = ['']  # 批量发送的接收邮箱

    timeArray = time.localtime(int(time.time()))
    otherStyleTime = time.strftime("%H:%M:%S", timeArray)

    data = {
        "country": "中国",
        "address": address,  # 签到地址
        "province": province,  # 签到省份
        "city": city,  # 签到城市
        "description": "打卡上班",  # 签到文本
        # "description": "打卡下班" if clock_type == "END" else "打卡上班",  # 签到文本
        "planId": "169dea675fba3b92187a5880ac99f4b2",  # 获取的 planId
        "type": clock_type,  # START 上班 END 下班
        "device": "Android",
        "latitude": "25.24169878",  # 签到维度
        "longitude": "110.18619487",  # 签到经度
        "t": AES_encrypt(int(time.time() * 1000)),
    }

    text = data["device"] + data["type"] + data["planId"] + "104117995" + data["address"] + "3478cbbc33f84bd00d75d7dfa69e0daa"
    hl = hashlib.md5()
    hl.update(text.encode(encoding='utf8'))
    md5 = hl.hexdigest()

    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 10; zh-cn; MIX 3 Build/QKQ1.190828.002) AppleWebKit/533.1 (KHTML, like Gecko) '
                      'Version/5.0 Mobile Safari/533.1',
        'roleKey': 'student',
        'Authorization': getToken(account, password),
        'sign': md5,  # 填sign参数
    }

    resp = postUrl(saveUrl, headers, data)

    try:
        print(resp)
        message = MIMEText(f'工学云签到成功\n---{clock_type}', 'plain', 'utf-8')
        message['Subject'] = f'{clock_type} 签到'
        message['From'] = '工学云签到提示!'
        message['To'] = ','.join(receivers)

        smtpObj = smtplib.SMTP_SSL(mail_host)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        smtpObj.quit()
        print(f'{clock_type}签到成功', otherStyleTime)
        time.sleep(10)
    except smtplib.SMTPException as e:
        print('error', e)
        time.sleep(10)


# 从 config.json 加载账号和地址信息
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 执行定时签到
# def schedule_sign_in():
#     current_hour = time.localtime().tm_hour
#     config = load_config()

    # if current_hour == 8:  # 8点上班
    #     for acc in config['accounts']:
    #         clock_in(acc['account'], acc['password'], acc['address'], acc['province'], acc['city'], "START")
    # elif current_hour == 18:  # 18点下班
    #     for acc in config['accounts']:
    #         clock_in(acc['account'], acc['password'], acc['address'], acc['province'], acc['city'], "END")

# 调用定时签到函数
# schedule_sign_in()


config = load_config()
for acc in config['accounts']:
    clock_in(acc['account'], acc['password'], acc['address'], acc['province'], acc['city'], "START")
