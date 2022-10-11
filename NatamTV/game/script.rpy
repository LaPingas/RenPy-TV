# type: ignore

init python:
    import re


    def connect():
        import socket
        HOST = "127.0.0.1"  # localhost
        PORT = 65432  # non-privileged ports are > 1023
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        return s


    def get_data(s):
        try:
            data = s.recv(1024)
            s.sendall(b'recvd')
            regex = re.compile('[^a-zA-Zא-ת1-9,.? ]')
            return regex.sub('', data.decode())
        except:
            return 'Could not connect to server'


define current_channel = "Knesset"
define e = Character("[current_channel]")
define s = connect()

define generated_bg_name = "channel currframe"
image bg = "images/[generated_bg_name].png"

label start:
    while True:
        scene bg

        python:
            e(get_data(s)[::-1], interact=True) # Displaying subtitles in dialog box
            renpy.free_memory() # Required for run-time generated backgrounds

    return