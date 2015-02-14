import dmw
import threading
import time

def print_rcvd_message( msg_class, msg_name, sender, message ):
    print "%s.%s.%s: %s"%( msg_class, msg_name, sender, message)

# called by each thread
class CountThread(threading.Thread):
    def run(self):
        print "initializing sub, subscribing and running"
        dmw.init_sub()
        dmw.subscribe( "telemetry", "position", "", print_rcvd_message ) 
        print "Subscribed. Let's run"
        dmw.loop()
        print "exited run"

if __name__ == "__main__":
    dmw.init_pub( "testinpython" )

    # Subscribe first
    t = CountThread()
    t.setDaemon( True )
    t.start()

    time.sleep(1)

    print "Now publishing new data"
    dmw.publish( "telemetry", "position", "hello" )

    print "done. Did we get anything?"

    time.sleep(3)

