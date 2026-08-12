import re

html = open("index.html").read()
m = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
js = m.group(1) if m else ""
open("dash_check.js", "w").write(js)
print("js extracted:", len(js), "chars")
