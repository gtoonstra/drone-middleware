import threading
import sys

import dmw
from dmw import dmwconversions
from vehicle_pb2 import Position
from vehicle_pb2 import HeartBeat
from os import path, getenv
import signal
import time
from pymavlink import mavutil 
import math

from ivy.std_api import *

PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '../../../../')))
sys.path.append(PPRZ_SRC + "/sw/lib/python")

PPRZ_HOME = getenv("PAPARAZZI_HOME", PPRZ_SRC)

from ivy_msg_interface import IvyMessagesInterface
from pprz_msg.message import PprzMessage

interface = None
conv = dmwconversions.Conversions()
seq = 0
vehicle = None

ap_modes = {"MANUAL": mavutil.mavlink.MAV_MODE_FLAG_MANUAL_INPUT_ENABLED,
            "AUTO1": mavutil.mavlink.MAV_MODE_FLAG_STABILIZE_ENABLED,
            "AUTO2": mavutil.mavlink.MAV_MODE_FLAG_AUTO_ENABLED,
            "HOME": mavutil.mavlink.MAV_MODE_FLAG_AUTO_ENABLED,
            "FAILSAFE": mavutil.mavlink.MAV_MODE_FLAG_AUTO_ENABLED }

gps_modes = {"NOFIX": 0,
             "DRO": 1,
             "2D": 2,
             "3D": 3,
             "GPSDRO": 4 }

class Vehicle(object):
    def __init__( self, ac_id ):
        self.ac_id = ac_id
        self.ap_mode = ap_modes[ "MANUAL" ]
        self.gps_fix = gps_modes[ "NOFIX" ]
        self.killed = False
        self.heading = 0.0
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        self.relalt = 0.0
        self.unix_time = 0
        self.course = 0.0
        self.sog = 0.0
        self.airspeed = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

class SubscriptionThread(threading.Thread):
    def __init__( self, interface ):
        threading.Thread.__init__(self)
        self.interface = interface

    def run(self):
        global vehicle

        dmw.init_sub()
        dmw.subscribe( "pprz", "opaque", "ground%d"%( vehicle.ac_id ), self.forward_opaque ) 
        dmw.loop()
        print "exited subscription thread"

    def forward_opaque( self, msg_class, msg_name, sender, message ):
        self.interface.send( message )

def update_seq():
    global seq

    curseq = seq
    seq = seq + 1
    if seq > 255:
        seq = 0
    return curseq

def process_messages( ac_id, msg ):
    '''show incoming pprz messages'''
    global conv
    global seq
    global vehicle

    if ac_id != 0:
        return

    if msg.name == 'AP_STATUS':
        vehicle.ap_mode = ap_modes[ msg.ap_mode ]
        vehicle.gps_fix = gps_modes[ msg.gps_mode ]
        if msg.kill_mode == "ON":
            vehicle.killed = True
        else:
            vehicle.killed = False
        vehicle.flight_time = msg.flight_time
        # <field name="state_filter_mode" type="string" values="UNKNOWN|INIT|ALIGN|OK|GPS_LOST|IMU_LOST|COV_ERR|IR_CONTRAST|ERROR"/>

    elif msg.name == 'FLIGHT_PARAM':
        vehicle.heading = float(msg.heading)
        vehicle.lat = float(msg.lat)
        vehicle.lon = float(msg.long)
        vehicle.alt = float(msg.alt)
        vehicle.relalt = float(msg.agl)
        vehicle.unix_time = int(float(msg.unix_time))
        vehicle.course = float(msg.course)
        vehicle.sog = float(msg.speed)
        vehicle.airspeed = float(msg.airspeed)

        crsrad = (math.pi/180.0) * vehicle.course
        vehicle.vx = vehicle.sog * math.cos( crsrad )
        vehicle.vy = vehicle.sog * math.sin( crsrad )
        vehicle.vz = float(msg.climb)

        pos = Position()
        pos.ecef_x, pos.ecef_y, pos.ecef_z = conv.wgs2ecef( vehicle.lat, vehicle.lon, vehicle.alt )
        pos.lat, pos.lon, pos.alt = vehicle.lat, vehicle.lon, vehicle.alt
        pos.vehicle_id = vehicle.ac_id
        pos.vehicle_tag = str(vehicle.ac_id)
        pos.time_boot_ms = vehicle.unix_time;
        pos.relalt = vehicle.relalt

        pos.vx = vehicle.vx
        pos.vy = vehicle.vy
        pos.vz = vehicle.vz
        pos.vground = vehicle.sog
        pos.hdg = vehicle.heading
        pos.seq = update_seq()

        dmw.publish( "vehicle", "position", pos.SerializeToString() )
        dmw.store( "vehicle", "position", str(pos.vehicle_id), pos.SerializeToString() )

 #   <field name="roll"   type="float" unit="deg"/>
 #   <field name="pitch"  type="float" unit="deg"/>
  #  <field name="itow"   type="uint32" unit="ms"/>

    elif msg.name == 'TELEMETRY_STATUS':
        hb = HeartBeat()
        hb.uavtype = "GENERIC"
        hb.autopilot = "PPZ"
        hb.vehicle_id = vehicle.ac_id
        hb.vehicle_tag = str(vehicle.ac_id)
        hb.base_mode = vehicle.ap_mode
        hb.custom_mode = 0
        hb.system_status = mavutil.mavlink.MAV_STATE_ACTIVE
        hb.mavlink_version = 3
        hb.seq = update_seq()
        dmw.publish( "vehicle", "heartbeat", hb.SerializeToString() )
        dmw.store_set( "vehicle", "heartbeat", str(hb.vehicle_id), hb.SerializeToString(), expire=60 )
    else:
        dmw.publish( "pprz", "opaque", "%s %s %s"%( msg.msg_class, msg.name, msg.payload_to_ivy_string() ) )

def signal_handler(signal, frame):
    global interface
    print "Attempting to stop interface"
    interface.shutdown()

def on_aircrafts_msg( self, agent, *larg ):
    dmw.publish( "pprz", "opaque", "%s %s AIRCRAFTS %s"%( larg[0], larg[1], larg[2] ) )

def on_config_msg( self, agent, *larg ):
    dmw.publish( "pprz", "opaque", "%s %s CONFIG %s"%( larg[0], larg[1], larg[2] ) )

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) < 2:
        print "Must supply one argument (ac_id)"
        sys.exit(-1)
    
    vehicle = Vehicle( int( sys.argv[1] ) )

    dmw.init()
    dmw.init_pub( str(vehicle.ac_id) )

    interface = IvyMessagesInterface( process_messages, verbose=True )
    ivyId1 = IvyBindMsg( on_aircrafts_msg, '((\\S*) (\\S*) AIRCRAFTS (\\S*))')
    ivyId1 = IvyBindMsg( on_config_msg, '((\\S*) (\\S*) CONFIG (.*))')
    
    # Subscribe to messages from gcs.
    t = SubscriptionThread( interface )
    t.setDaemon( True )
    t.start()

    while True:
        time.sleep(0.1)

