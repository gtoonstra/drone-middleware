import threading
import sys

import dmw
import socket

class SubscriptionThread(threading.Thread):
    def __init__( self, conn ):
        threading.Thread.__init__(self)
        self.conn = conn

    def run(self):
        dmw.init_sub()
        dmw.subscribe( "mavlink", "opaque", "255", self.forward_message ) 
        dmw.loop()
        print "exited subscription thread"

    def cancel(self):
        dmw.stop()

    def forward_message( self, msg_class, msg_name, sender, message ):
        print "received ground msg from %s.%s.%s"% ( msg_class, msg_name, sender )
        self.conn.send( message )

if __name__ == "__main__":
    dmw.init()
    dmw.init_pub( "ground255" )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 5400 ))

    s.listen(1)
    while True:
        conn, addr = s.accept()

        # Subscribe to messages from gcs.
        t = SubscriptionThread( conn )
        t.setDaemon( True )
        t.start()

        print 'Connected by', addr

        while True:
            data = conn.recv(1024)
            if not data:
                continue
            else:
                dmw.publish( "mavlink", "opaque", data )
        t.cancel()


