import base64, subprocess, sys
u = sys.argv[1].replace('meow-locate://', '')
p = base64.b64decode(u).decode('utf-8')
subprocess.Popen(['explorer', '/select,', p])
