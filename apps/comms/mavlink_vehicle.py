import threading
import sys

from pymavlink import mavutil
import dmw

class SubscriptionThread(threading.Thread):
    def __init__( self, mavlink ):
        threading.Thread.__init__(self)
        self.mavlink = mavlink

    def run(self):
        dmw.init_sub()
        dmw.subscribe( "mavlink", "opaque", "ground255", self.forward_message ) 
        dmw.loop()
        print "exited subscription thread"

    def forward_message( self, msg_class, msg_name, sender, message ):
        print "received vehicle msg from %s.%s.%s"%( msg_class, msg_name, sender )
        self.mavlink.write( message )

def wait_heartbeat(m):
    '''wait for a heartbeat so we know the target system IDs'''
    msg = m.recv_match(type='HEARTBEAT', blocking=True)
    print("Heartbeat from APM (system %u component %u)" % (m.target_system, m.target_system))
    bytemsg = msg.get_msgbuf()
    dmw.publish( "mavlink", "opaque", bytemsg )

def process_messages(m):
    '''show incoming mavlink messages'''
    while True:
        msg = m.recv_match(blocking=True)
        if not msg:
            return
        if msg.get_type() == "BAD_DATA":
            if mavutil.all_printable(msg.data):
                sys.stdout.write(msg.data)
                sys.stdout.flush()
        else:
            bytemsg = msg.get_msgbuf()
            dmw.publish( "mavlink", "opaque", bytemsg )

if __name__ == "__main__":
    dmw.init()
    dmw.init_pub( "255" )

    # create a mavlink tcp instance
    master = mavutil.mavlink_connection( "tcp:127.0.0.1:5760", baud=115200, source_system=255 )

    # Subscribe to messages from gcs.
    t = SubscriptionThread( master )
    t.setDaemon( True )
    t.start()

    # wait for the heartbeat msg to find the system ID
    wait_heartbeat(master)

    # Process messages received from apm and send them onto the bus in "opaque" format
    process_messages( master )

