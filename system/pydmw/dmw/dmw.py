import zmq
from dmw_zeroconf import ServiceResolver

#
# sudo apt-get install libavahi-compat-libdnssd-dev
# 
# sudo pip install pybonjour --allow-external pybonjour --allow-unverified pybonjour
# 

MAX_APP_NAME = 32
MAX_TOPIC_LEN = 128

class DmwException(Exception):
    pass

appname = None
context = None
subscriber = None
publisher = None
subip = None
subport = None
pubip = None
pubport = None
running = True

subscriptions = {}

def get_topic( msg_class, msg_name, sender ):
    topic = ""
    lenstr = 2
    if msg_class == None or len(msg_class) == 0:
        raise DmwException( "The message class must have a value." )
    lenstr += len(msg_class)
    if msg_name != None and len(msg_name) > 0:
        lenstr += len(msg_name)
        if ( lenstr > MAX_TOPIC_LEN ):
            raise DmwException( "The topic name would be too long (max 128 characters)." )
        
        if sender != None and len(sender) > 0:
            lenstr += len(sender)
            if ( lenstr > MAX_TOPIC_LEN ):
                raise DmwException( "The topic name would be too long (max 128 characters)." )

            topic = "%s.%s.%s"%( msg_class, msg_name, sender )

        else:
            topic = "%s.%s"%( msg_class, msg_name )
    else:
        topic = "%s"%( msg_class )

    return topic

def init():
    global context
    global subip
    global subport
    global pubip 
    global pubport

    if context != None:
        raise DmwException( "Library already initialized." )
    context = zmq.Context()


    resolver = ServiceResolver()
    subip, subport = resolver.resolve_record( "_dmwsub._tcp" )
    pubip, pubport = resolver.resolve_record( "_dmwpub._tcp" )

def init_pub( name ):
    global appname
    global context
    global publisher

    if name == None or len(name) > MAX_APP_NAME:
        raise DmwException( "Application name too long." )
    if not name.isalnum() or name.isupper():
        raise DmwException( "Application name contains invalid character. Only lower-case and digits allowed." )

    if context == None:
        raise DmwException( "Initialize library first with init()." )

    if publisher != None:
        raise DmwException( "Publishing side already initialized." )

    appname = name
    publisher = context.socket(zmq.PUB)
    publisher.connect( "tcp://%s:%d"%( pubip, pubport ) )

def init_sub():
    global context
    global subscriber
    global running 

    if context == None:
        raise DmwException( "Initialize library first with init()." )
    running = True

    if subscriber != None:
        raise DmwException( "Subscription side already initialized." )

    subscriber = context.socket(zmq.SUB)
    subscriber.connect( "tcp://%s:%d"%( subip, subport ) )

def subscribe( msg_class, msg_name, sender, callback ):
    global subscriber

    if subscriber == None:
        raise DmwException( "Subscribers are not initialized. Call dwm_init_sub first." )

    topic = get_topic( msg_class, msg_name, sender )
    subscriber.setsockopt(zmq.SUBSCRIBE, topic)

    subscriptions[ topic ] = callback

def unsubscribe( msg_class, msg_name, sender ):
    global subscriber

    if subscriber == None:
        raise DmwException( "Subscribers are not initialized. Call dwm_init_sub first." )

    topic = get_topic( msg_class, msg_name, sender )
    subscriber.setsockopt(zmq.UNSUBSCRIBE, topic)

    del subscriptions[ topic ]

def publish( msg_class, msg_name, data ):
    global publisher
    global appname

    if publisher == None:
        raise DmwException( "Publishing is not initialized. Call dwm_init_pub first." )

    topic = get_topic( msg_class, msg_name, appname )
    publisher.send(topic, flags=zmq.SNDMORE)
    publisher.send(data)

def loop():
    global subscriber
    global running 

    if subscriber == None:
        raise DmwException( "Subscribers are not initialized. Call dwm_init_sub first." )

    while running:
        msgs = subscriber.recv_multipart()
        topic = msgs[0]
        data = msgs[1]

        elems = topic.split( "." )
        if subscriptions.has_key( topic ):
            cb = subscriptions[ topic ]
            cb( elems[0], elems[1], elems[2], data )
        elif subscriptions.has_key( "%s.%s"%( elems[0], elems[1] )):
            cb = subscriptions[ "%s.%s"%( elems[0], elems[1] ) ]
            cb( elems[0], elems[1], elems[2], data )            
        elif subscriptions.has_key( elems[0] ):
            cb = subscriptions[ elems[0] ]
            cb( elems[0], elems[1], elems[2], data )

def cancel():
    global running

    running = False

