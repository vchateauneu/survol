#!/usr/bin/python

"""
Edits various Survol parameters.
Also, it servers JSON queries from the HTML pages doing the same features, but in JSON
"""

import sys

def Wrt(theStr):
    sys.stdout.write(theStr)

def Main():
    Wrt("""
    """)
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html><head><title>Configuration</title></head>



<body>Have the same "SURVOL" header<br><br>Edit Survol configuration<br><br>

<form method="post" action="server_configuration.py" name="ServerConfiguration">CGI server port number: <input name="server_port" value="8000"><br><br>
<input value="MySubmit" name="Hello" type="submit"><br></form>


<br><br>
Edit credentials file name<br>
<a href="credentials.htm">Edit credentials</a><br>
<a href="index.htm">Return to Survol</a>
</body></html>

Wrt("""
""")

Wrt("""
""")
