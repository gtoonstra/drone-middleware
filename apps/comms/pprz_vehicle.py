import threading
import sys

import dmw
from dmw import dmwconversions
from vehicle_pb2 import Position
from vehicle_pb2 import HeartBeat
from os import path, getenv
import signal
import time

PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '../../../../')))
sys.path.append(PPRZ_SRC + "/sw/lib/python")

PPRZ_HOME = getenv("PAPARAZZI_HOME", PPRZ_SRC)

from ivy_msg_interface import IvyMessagesInterface
from pprz_msg.message import PprzMessage

interface = None
conv = dmwconversions.Conversions()

class SubscriptionThread(threading.Thread):
    def __init__( self, interface ):
        threading.Thread.__init__(self)
        self.interface = interface

    def run(self):
        dmw.init_sub()
        dmw.subscribe( "pprz", "opaque", "ground254", self.forward_opaque ) 
        dmw.loop()
        print "exited subscription thread"

    def forward_opaque( self, msg_class, msg_name, sender, message ):
        self.interface.send( message )

def process_messages( ac_id, msg ):
    '''show incoming pprz messages'''
    global conv

    if msg.get_classname() != "telemetry":
        return

   # if msg.get_type() == 'GLOBAL_POSITION_INT':
   #     pos = Position()
   #     pos.ecef_x, pos.ecef_y, pos.ecef_z = c.wgs2ecef( float(msg.lat) / 1E7, float(msg.lon) / 1E7, float(msg.alt) / 1000 )
   #     pos.lat, pos.lon, pos.alt = msg.lat, msg.lon, msg.alt / 1000
   #     pos.vehicle_id = 255
   #     pos.vehicle_tag = "255"
   #     dmw.publish( "vehicle", "position", pos.SerializeToString() )
   #     dmw.store( "vehicle", "position", str(pos.vehicle_id), pos.SerializeToString() )

    if msg.get_msgname() == 'ALIVE':
        hb = HeartBeat()
        hb.uavtype = "unknown"
        hb.autopilot = "pprz"
        hb.vehicle_id = ac_id
        hb.vehicle_tag = str(ac_id)
        hb.base_mode = 0
        hb.custom_mode = 0
        hb.system_status = 0
        hb.mavlink_version = 3
        hb.custom = msg.get_field( 0 )
        dmw.publish( "vehicle", "heartbeat", hb.SerializeToString() )
        dmw.store_set( "vehicle", "heartbeat", str(hb.vehicle_id), hb.SerializeToString(), expire=60 )
    else:
        dmw.publish( "pprz", "opaque", "%d %s"%( ac_id, msg.payload_to_ivy_string() ) )

def signal_handler(signal, frame):
    global interface
    print "Attempting to stop interface"
    interface.shutdown()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    dmw.init()
    dmw.init_pub( "254" )

    interface = IvyMessagesInterface( process_messages )

    # Subscribe to messages from gcs.
    t = SubscriptionThread( interface )
    t.setDaemon( True )
    t.start()

    while True:
        time.sleep(0.1)

