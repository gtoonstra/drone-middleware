import threading
import sys

from pymavlink import mavutil
import dmw
from dmw import dmwconversions
from vehicle_pb2 import Position
from vehicle_pb2 import HeartBeat

from pymavlink.dialects.v10 import common

uavtypes = {}
aptypes = {}
aircraft_id = 0

def enumUavTypes():
    global aptypes

    allEnums = dir(common)    
    for entry in allEnums:
        if entry.startswith( "MAV_AUTOPILOT_" ):
            val = entry[ len("MAV_AUTOPILOT_" ): ]
            key = getattr( common, entry )
            aptypes[ key ] = val

def enumApTypes():
    global uavtypes

    allEnums = dir(common)    
    for entry in allEnums:
        if entry.startswith( "MAV_TYPE_" ):
            val = entry[ len("MAV_TYPE_" ): ]
            key = getattr( common, entry )
            uavtypes[ key ] = val

def find_uav_type( key ):
    if uavtypes.has_key( key ):
        return uavtypes[ key ]
    return "unknown"

def find_ap_type( key ):
    if aptypes.has_key( key ):
        return aptypes[ key ]
    return "unknown"

class SubscriptionThread(threading.Thread):
    def __init__( self, mavlink ):
        threading.Thread.__init__(self)
        self.mavlink = mavlink

    def run(self):
        global aircraft_id

        dmw.init_sub()
        dmw.subscribe( "mavlink", "opaque", "ground%d"%( aircraft_id ), self.forward_message ) 
        dmw.loop()
        print "exited subscription thread"

    def forward_message( self, msg_class, msg_name, sender, message ):
        self.mavlink.write( message )

def wait_heartbeat(m):
    '''wait for a heartbeat so we know the target system IDs'''
    msg = m.recv_match(type='HEARTBEAT', blocking=True)
    print("Heartbeat from APM (system %u component %u)" % (m.target_system, m.target_system))
    bytemsg = msg.get_msgbuf()
    print "Heartbeat [", bytemsg.encode('hex')
    dmw.publish( "mavlink", "opaque", bytemsg )

def process_messages(c,m):
    global aircraft_id

    '''show incoming mavlink messages'''
    while True:
        msg = m.recv_match(blocking=True)
        if not msg:
            return
        else:
            if msg.get_type() == 'GLOBAL_POSITION_INT':
                pos = Position()
                pos.ecef_x, pos.ecef_y, pos.ecef_z = c.wgs2ecef( float(msg.lat) / 1E7, float(msg.lon) / 1E7, float(msg.alt) / 1000.0 )
                pos.lat, pos.lon, pos.alt = float(msg.lat) / 1E7, float(msg.lon) / 1E7, float(msg.alt) / 1000.0
                pos.vehicle_id = aircraft_id
                pos.vehicle_tag = str(aircraft_id)
                pos.time_boot_ms = msg.time_boot_ms;
                pos.relalt = float( msg.relative_alt ) / 1000.0
                pos.vx = float(msg.vx) / 100.0;
                pos.vy = float(msg.vy) / 100.0;
                pos.vz = float(msg.vz) / 100.0;
                pos.hdg = float( msg.hdg ) / 100.0
                pos.seq = msg.get_seq()

                print msg.alt, pos.alt

                dmw.publish( "vehicle", "position", pos.SerializeToString() )
                dmw.store( "vehicle", "position", str(pos.vehicle_id), pos.SerializeToString() )
            elif msg.get_type() == 'HEARTBEAT':
                hb = HeartBeat()
                hb.uavtype = find_uav_type( msg.type )
                hb.autopilot = find_ap_type( msg.autopilot )
                hb.vehicle_id = aircraft_id
                hb.vehicle_tag = str( aircraft_id )
                hb.base_mode = msg.base_mode
                hb.custom_mode = msg.custom_mode
                hb.system_status = msg.system_status
                hb.mavlink_version = msg.mavlink_version
                hb.custom = ''
                hb.seq = msg.get_seq()
                dmw.publish( "vehicle", "heartbeat", hb.SerializeToString() )
                dmw.store_set( "vehicle", "heartbeat", str(hb.vehicle_id), hb.SerializeToString(), expire=60 )
            else:
                dmw.publish( "mavlink", "opaque", msg.get_msgbuf() )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Must supply one argument (ac_id)"
        sys.exit(-1)
    
    aircraft_id = int( sys.argv[1] )

    enumUavTypes()
    enumApTypes()

    dmw.init()
    dmw.init_pub( str(aircraft_id) )

    conv = dmwconversions.Conversions()

    # create a mavlink tcp instance
    master = mavutil.mavlink_connection( "tcp:127.0.0.1:5760", baud=115200, source_system=aircraft_id )

    # Subscribe to messages from gcs.
    t = SubscriptionThread( master )
    t.setDaemon( True )
    t.start()

    # wait for the heartbeat msg to find the system ID
    wait_heartbeat(master)

    # Process messages received from apm and send them onto the bus in "opaque" format
    process_messages( conv, master )

