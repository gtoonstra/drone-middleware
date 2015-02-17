import threading
import sys

from pymavlink import mavutil
import dmw
from dmw import dmwconversions
from vehicle_pb2 import Position

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
        self.mavlink.write( message )

def wait_heartbeat(m):
    '''wait for a heartbeat so we know the target system IDs'''
    msg = m.recv_match(type='HEARTBEAT', blocking=True)
    print("Heartbeat from APM (system %u component %u)" % (m.target_system, m.target_system))
    bytemsg = msg.get_msgbuf()
    dmw.publish( "mavlink", "opaque", bytemsg )

def process_messages(c,m):
    '''show incoming mavlink messages'''
    while True:
        msg = m.recv_match(blocking=True)
        if not msg:
            return
        else:
            if msg.get_type() == 'GLOBAL_POSITION_INT':
                pos = Position()
                pos.ecef_x, pos.ecef_y, pos.ecef_z = c.wgs2ecef( float(msg.lat) / 1E7, float(msg.lon) / 1E7, float(msg.alt) / 1000 )
                pos.vehicle_id = 255
                pos.vehicle_tag = "255"
                dmw.publish( "vehicle", "position", pos.SerializeToString() )

            bytemsg = msg.get_msgbuf()
            dmw.publish( "mavlink", "opaque", bytemsg )

if __name__ == "__main__":
    dmw.init()
    dmw.init_pub( "255" )

    conv = dmwconversions.Conversions()

    # create a mavlink tcp instance
    master = mavutil.mavlink_connection( "tcp:127.0.0.1:5760", baud=115200, source_system=255 )

    # Subscribe to messages from gcs.
    t = SubscriptionThread( master )
    t.setDaemon( True )
    t.start()

    # wait for the heartbeat msg to find the system ID
    wait_heartbeat(master)

    # Process messages received from apm and send them onto the bus in "opaque" format
    process_messages( conv, master )

