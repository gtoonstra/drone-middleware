import dmw
import threading
import time

def print_rcvd_message( msg_class, msg_name, sender, message ):
    print "%s.%s.%s: %s"%( msg_class, msg_name, sender, message)

# called by each thread
class SubscriptionThread(threading.Thread):
    def run(self):
        print "initializing sub, subscribing and running"
        dmw.init_sub()
        dmw.subscribe( "telemetry", "position", "", print_rcvd_message ) 
        dmw.loop()
        print "exited run"

if __name__ == "__main__":
    dmw.init()
    dmw.init_pub( "testinpython" )

    # Subscribe first
    t = SubscriptionThread()
    t.setDaemon( True )
    t.start()

    time.sleep(1)

    dmw.publish( "telemetry", "position", "14.1525354 102.23324324 25.3335" )

    time.sleep(3)

