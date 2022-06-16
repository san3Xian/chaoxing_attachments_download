"""
等个有缘人转化成油猴脚本
一个随手写的用于批量下载 chaoxing/fanya 课程页面中附件的脚本

"""
import requests
import urllib.parse
import sys
import re
import json
import os

# 将下述两行修改为你的账号密码
account = "你的chaoxing账号"
password = "你的chaoxing密码"  # 如果开启了des加密，则这里不能填写明文密码

req_headers = {
    # "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
    "Referer": "https://passport2.chaoxing.com/login?loginType=4&newversion=true&fid=2182&newversion=true&refer=http://i.mooc.chaoxing.com",
    "X-Requested-With": "XMLHttpRequest",
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"'
}


def chaoxing_do_login():
    """
    登陆chaoxing，并将cookie写入文件
    """
    login_url = "https://passport2.chaoxing.com/fanyalogin"

    login_data = {
        'fid': '2182',  # 机构登陆代码
        'uname': account,
        'password': password,
        'refer': 'http%3A%2F%2Fi.mooc.chaoxing.com',
        't': 'false',  # 控制是否使用des加密(CryptoJS.pad.Pkcs7) 登陆，在https://passport2.chaoxing.com/js/fanya/login.js
                       # 若true则key这个文件encryptByDES函数中
        'validate': ''
    }
    result = requests.post(url=login_url, data=login_data, headers=req_headers)

    if not result.json()["status"]:
        print("Login Failed, exit")
        exit(-1)
    else:
        print("🎉Login succeeded")
    # save cookie
    result_cookiejar = result.cookies
    result_cookie_dict = requests.utils.dict_from_cookiejar(result_cookiejar)
    with open("chaoxing_cookie", "w") as cookie_file:
        cookie_file.write(json.dumps(result_cookie_dict))
    return result_cookie_dict


def chaoxing_check_login() -> dict:
    """
    检查chaoxing登陆状态
    """
    if os.path.exists("chaoxing_cookie"):
        with open("chaoxing_cookie", mode="r") as cookie_file:
            cookie_str = cookie_file.read()
        cookie_dict = json.loads(cookie_str)
        login_status_url = "http://i.mooc.chaoxing.com/space/index"
        result = requests.get(url=login_status_url, cookies=cookie_dict, headers=req_headers, allow_redirects=False)
        if result.status_code == 200:
            print(re.search(r'<p class="personalName" title=".*?"', result.text).group().replace('<p class="personalName" title=', ""), "已登陆")
            return cookie_dict
    return chaoxing_do_login()


if __name__ == '__main__':
    cookie = chaoxing_check_login()
    print("😆I am running!")
    url_parse = urllib.parse.urlparse(sys.argv[1])
    url_params = urllib.parse.parse_qs(url_parse.query)

    # 利用urllib模块解析出网址中的courseId参数和knowledgeId / chapterId参数
    # 并且将参数值赋予给名为course_id 和 knowledge_id 的变量
    # 因为在url地址中，同一个参数可以有多个值，所以这里我们通过指定下标只取第一个值
    clazz_id = ""
    course_id = url_params["courseId"][0]
    if "knowledgeId" in url_params.keys():
        knowledge_id = url_params["knowledgeId"][0]
    else:
        knowledge_id = url_params["chapterId"][0]
    if "clazzid" in url_params.keys():
      clazz_id = url_params["clazzid"][0]
      

    # 将上述解析到course_id 和 knowledge_id 拼接到新的网址中形成新的字符串
    # 请求chaoxing的接口获取课程附件信息
    # 拼接后效果如: https://mooc1.chaoxing.com/knowledge/cards?courseid=200351800&knowledgeid=130793594
    cards_url = "https://mooc1.chaoxing.com/knowledge/cards?" + "courseid=" + course_id + "&knowledgeid=" + knowledge_id + "&clazzid=" + clazz_id
    cards_result = requests.get(cards_url, headers=req_headers, cookies=cookie, allow_redirects=False)
    print("cards_url",cards_url)
    if cards_result.status_code != 200:
        print(cards_result.status_code, "Cookie(即传入脚本的第二个参数)有误，请重新执行")

    attachment_str = re.search(r"mArg = .*\};", cards_result.text).group()
    attachment_json = json.loads(attachment_str.replace("mArg = ", "", 1).replace("};", "}", 1))

    # 定义需要下载的附件类型
    download_type = [".ppt", ".pptx", ".pdf"]

    req_headers["Referer"] = "https://mooc1.chaoxing.com/ananas/modules/pdf/index.html"
    #print("===", json.dumps(attachment_json)) # Debug messages
    for attachment in attachment_json["attachments"]:
        if "type" not in attachment:
            continue
        print("找到文件id", attachment["property"]["objectid"])
        download_url = "https://mooc1.chaoxing.com/ananas/status/" + attachment["property"]["objectid"] + "?flag=normal"
        print("文件类型", attachment["property"]["type"])
        print("文件名", attachment["property"]["name"])
        if attachment["property"]["type"] in download_type:
            print("开始下载文件", attachment["property"]["name"])
            attachment_metadata = requests.get(url=download_url, headers=req_headers).json()
            attachment_data = requests.get(url=attachment_metadata["download"], headers=req_headers)
            with open(attachment["property"]["name"], "wb") as file:
                file.write(attachment_data.content)
        print("=======================")
    print("程序结束")
