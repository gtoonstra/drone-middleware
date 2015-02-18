import threading
import sys
import errno
import signal
import time

import dmw
from dmw import DmwException
from pymavlink import mavutil
from os import path, getenv

from vehicle_pb2 import Position
from vehicle_pb2 import HeartBeat

from ivy.std_api import *

PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '../../../../')))
sys.path.append(PPRZ_SRC + "/sw/lib/python")

PPRZ_HOME = getenv("PAPARAZZI_HOME", PPRZ_SRC)

from ivy_msg_interface import IvyMessagesInterface
from pprz_msg.message import PprzMessage

ap_modes = {mavutil.mavlink.MAV_MODE_FLAG_MANUAL_INPUT_ENABLED: "MANUAL",
            mavutil.mavlink.MAV_MODE_FLAG_STABILIZE_ENABLED: "AUTO1",
            mavutil.mavlink.MAV_MODE_FLAG_AUTO_ENABLED: "AUTO2" }

gps_modes = {0: "NOFIX",
             1: "DRO",
             2: "2D",
             3: "3D",
             4: "GPSDRO" }

aircraft_id = 0
interface = None

class SubscriptionThread(threading.Thread):
    def __init__( self, interface, ac_id ):
        threading.Thread.__init__(self)
        self.aircraft_id = str(ac_id)
        self.interface = interface

    def run(self):
        try:
            dmw.init_sub()
        except DmwException:
            pass

        dmw.subscribe( "pprz", "opaque", self.aircraft_id, self.forward_opaque ) 
        dmw.subscribe( "vehicle", "heartbeat", self.aircraft_id, self.forward_heartbeat ) 
        dmw.subscribe( "vehicle", "position", self.aircraft_id, self.forward_position ) 
        dmw.loop()
        print( "exited subscription thread" )

    def cancel(self):
        dmw.cancel()

    def forward_opaque( self, msg_class, msg_name, sender, message ):
        self.interface.send( message )

    def forward_heartbeat( self, msg_class, msg_name, sender, message ):
        hb = HeartBeat()
        hb.ParseFromString( message )
        # TELEMETRY_STATUS message
        msg = PprzMessage("ground", "TELEMETRY_STATUS")
        values = [ str(self.aircraft_id), "no_id", "0.02", "0", "0", "0.0", "0", "0", "0", "0", "0", "9999.0" ]
        msg.set_values(values)
        self.interface.send( msg )

    def forward_position( self, msg_class, msg_name, sender, message ):
        pos = Position()
        pos.ParseFromString( message )
        # FLIGHT_PARAM message
        msg = PprzMessage("ground", "FLIGHT_PARAM")
        values = [ str(self.aircraft_id), "0.0", "0.0", str(pos.hdg), str(pos.lat), str(pos.lon), str(pos.vground), "0.0", str(pos.alt), str(pos.vz), str(pos.relalt), "0.0", "0", "0.0" ]
        msg.set_values(values)
        self.interface.send( msg )

def process_messages( ac_id, msg ):
    '''show incoming pprz messages'''
    global conv
    global seq
    global vehicle
    global interface

    if not isinstance( ac_id, str ):
        return

    if "REQ" in msg.name:
        ivystr = "gcs %s %s %s"%( str(ac_id), msg.name, msg.payload_to_ivy_string() )
        ivystr = ivystr.strip()
        dmw.publish( "pprz", "opaque", ivystr )

def signal_handler(signal, frame):
    global interface
    print "Attempting to stop interface"
    interface.shutdown()

def on_aircraft_req_msg( self, agent, *larg ):
    dmw.publish( "pprz", "opaque", "%s %s AIRCRAFTS_REQ"%( larg[0], larg[1] ) )

def on_config_req_msg( self, agent, *larg ):
    dmw.publish( "pprz", "opaque", "%s %s CONFIG_REQ %s"%( larg[0], larg[1], larg[2] ) )

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) < 2:
        print "Must supply one argument (ac_id)"
        sys.exit(-1)
    
    aircraft_id = int( sys.argv[1] )

    dmw.init()
    dmw.init_pub( "ground%d"%( aircraft_id ) )
    
    interface = IvyMessagesInterface( process_messages, bind_regex='(.*)', verbose=True )
    ivyId1 = IvyBindMsg( on_aircraft_req_msg, '((\\S*) (\\S*) AIRCRAFTS_REQ)')
    ivyId2 = IvyBindMsg( on_config_req_msg, '((\\S*) (\\S*) CONFIG_REQ (\\S*))')

    # Subscribe to messages from gcs.
    t = SubscriptionThread( interface, aircraft_id )
    t.setDaemon( True )
    t.start()

    while True:
        time.sleep(0.1)

    print ("Exiting app")

