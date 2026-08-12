import re

src = open("src/mk7/commands/ui.py").read()
html = open("opc-dash.html").read()
pattern = re.compile(r'HTML_TEMPLATE = """.*?"""', re.DOTALL)
new_src, n = pattern.subn('HTML_TEMPLATE = """' + html + '"""', src, count=1)
open("src/mk7/commands/ui.py", "w").write(new_src)
print("replaced:", n)
