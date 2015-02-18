#!/usr/bin/python

import sys
import dmw

import vehicle_pb2

messageLookup = { "vehicle.position": vehicle_pb2.Position, "vehicle.heartbeat": vehicle_pb2.HeartBeat }

def print_message( msg_class, msg_name, sender, message ):
    print ("%s.%s.%s"%( msg_class, msg_name, sender ))
    msgkey = "%s.%s"%( msg_class, msg_name )
    if messageLookup.has_key( msgkey ):
        msg = messageLookup[ msgkey ]()
        msg.ParseFromString( message )
        print( "Contents: %s"%( msg ) )
    else:
        print( "Contents are unknown or opaque" )

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print ("Must supply message subscription path: python monitor.py x[.y[.z]]")
        sys.exit(-1)

    sub = sys.argv[1]
    elems = sub.split(".")

    dmw.init()
    dmw.init_sub()
    if len(elems) == 3:
        dmw.subscribe( elems[0], elems[1], elems[2], print_message ) 
    elif len(elems) == 2:
        dmw.subscribe( elems[0], elems[1], "", print_message ) 
    elif len(elems) == 1:
        dmw.subscribe( elems[0], "", "", print_message ) 
    else:
        print ("Invalid subscription path %s"%( sub ) )
        sys.exit(-1)
    dmw.loop()


