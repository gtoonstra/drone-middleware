import threading
import sys

import dmw
import socket
from pymavlink import mavutil

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
            aptypes[ val ] = key

def enumApTypes():
    global uavtypes

    allEnums = dir(common)    
    for entry in allEnums:
        if entry.startswith( "MAV_TYPE_" ):
            val = entry[ len("MAV_TYPE_" ): ]
            key = getattr( common, entry )
            uavtypes[ val ] = key

def find_uav_type( key ):
    if uavtypes.has_key( key ):
        return uavtypes[ key ]
    return 0

def find_ap_type( key ):
    if aptypes.has_key( key ):
        return aptypes[ key ]
    return 0

class SubscriptionThread(threading.Thread):
    def __init__( self, conn, ac_id ):
        threading.Thread.__init__(self)
        self.aircraft_id = str(ac_id)
        self.master = mavutil.mavlink_connection( "udp:127.0.0.1:12345", source_system=1 )
        self.master.mav = mavutil.mavlink.MAVLink(self.master, srcSystem=self.master.source_system, srcComponent=1)
        self.conn = conn

    def run(self):
        dmw.init_sub()
        dmw.subscribe( "mavlink", "opaque", self.aircraft_id, self.forward_opaque ) 
        dmw.subscribe( "vehicle", "heartbeat", self.aircraft_id, self.forward_heartbeat ) 
        dmw.subscribe( "vehicle", "position", self.aircraft_id, self.forward_position ) 
        dmw.loop()
        print "exited subscription thread"

    def cancel(self):
        dmw.stop()

    def forward_opaque( self, msg_class, msg_name, sender, message ):
        self.conn.send( message )

    def forward_heartbeat( self, msg_class, msg_name, sender, message ):
        hb = HeartBeat()
        hb.ParseFromString( message )
        self.master.mav.seq = hb.seq
        print "heartbeat"
        msg = self.master.mav.heartbeat_encode( find_uav_type( hb.uavtype ), find_ap_type( hb.autopilot ), hb.base_mode, hb.custom_mode, hb.system_status )
        self.conn.send( msg.get_msgbuf() )

    def forward_position( self, msg_class, msg_name, sender, message ):
        pos = Position()
        pos.ParseFromString( message )
        self.master.mav.seq = pos.seq
        msg = self.master.mav.global_position_int_encode( pos.time_boot_ms, int( pos.lat * 1E7 ), int( pos.lon * 1E7 ), int(pos.alt * 1000), int(pos.relalt * 1000), int(pos.vx*100), int(pos.vy*100), int(pos.vz*100), int(pos.hdg * 100))
        print msg.alt, pos.alt
        self.conn.send( msg.get_msgbuf() )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Must supply one argument (ac_id)"
        sys.exit(-1)
    
    aircraft_id = int( sys.argv[1] )

    enumUavTypes()
    enumApTypes()

    dmw.init()
    dmw.init_pub( "ground%d"%( aircraft_id ) )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 5400 ))

    s.listen(1)
    while True:
        conn, addr = s.accept()

        # Subscribe to messages from gcs.
        t = SubscriptionThread( conn, aircraft_id )
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


