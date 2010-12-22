def http_user_agent(req, name):
    user_agent = req.META.get('HTTP_USER_AGENT', '')
    return user_agent.find(name) + 1

isIE = lambda req: http_user_agent(req, "MSIE")
isIE7 = lambda req: http_user_agent(req, "MSIE 7.0")
isIE8 = lambda req: http_user_agent(req, "MSIE 8.0")
isIE6 = lambda req: http_user_agent(req, "MSIE 6")
isOpera = lambda req: http_user_agent(req, "Opera")
isMozilla = lambda req: http_user_agent(req, "Mozilla")
isFF = lambda req: http_user_agent(req, "Firefox")
isSafari = lambda req: False if http_user_agent(req, "Chrome") \
    else http_user_agent(req, "Safari")
isChrome = lambda req: http_user_agent(req, "Chrome")
isWebkit = lambda req: http_user_agent(req, "WebKit")
isMAC = lambda req: http_user_agent(req, "Mac OS")
isWindows = lambda req: http_user_agent(req, "Windows")
