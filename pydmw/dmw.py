import zmq

MAX_APP_NAME = 32
MAX_TOPIC_LEN = 128

class DmwException(Exception):
    pass

appname = None
context = None
subscriber = None
publisher = None
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

def init_pub( name ):
    global appname

    if name == None or len(name) > MAX_APP_NAME:
        raise DmwException( "Application name too long." )
    if not name.isalnum() or name.isupper():
        raise DmwException( "Application name contains invalid character. Only lower-case and digits allowed." )

    appname = name
    if context == None:
        context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.connect( "tcp://localhost:5557" )

def init_sub():
    if context == None:
        context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect( "tcp://localhost:5558" )

def subscribe( msg_class, msg_name, sender, callback ):
    if subscriber == None:
        raise DmwException( "Subscribers are not initialized. Call dwm_init_sub first." )

    topic = get_topic( msg_class, msg_name, sender )
    subscriber.setsockopt(zmq.SUBSCRIBE, topic)

    subscriptions[ topic ] = callback

def unsubscribe( msg_class, msg_name, sender ):
    if subscriber == None:
        raise DmwException( "Subscribers are not initialized. Call dwm_init_sub first." )

    topic = get_topic( msg_class, msg_name, sender )
    subscriber.setsockopt(zmq.UNSUBSCRIBE, topic)

    del subscriptions[ topic ]

def publish( msg_class, msg_name, data ):
    if publisher == None:
        raise DmwException( "Publishing is not initialized. Call dwm_init_pub first." )

    topic = get_topic( msg_class, msg_name, sender )
    publisher.send(topic, flags=zmq.SNDMORE)
    publisher.send(data)

def loop():
    if subscriber == None:
        raise DmwException( "Subscribers are not initialized. Call dwm_init_sub first." )

    while True:
        msgs = zmq.recv_multipart()
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

