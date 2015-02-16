import libpydmw
import threading
import time

def print_rcvd_message( msg_class, msg_name, sender, message ):
    print "%s.%s.%s: %s"%( msg_class, msg_name, sender, message)

# called by each thread
class CountThread(threading.Thread):
    def run(self):
        print "initializing sub, subscribing and running"
        libpydmw.init_sub()
        libpydmw.subscribe( "telemetry", "position", "", print_rcvd_message ) 
        print "Subscribed. Let's run"
        libpydmw.run()
        print "exited run"

if __name__ == "__main__":
    import stacktracer
    stacktracer.trace_start("trace.html")

    libpydmw.init_pub( "testinpython" )

    # Subscribe first
    t = CountThread()
    t.setDaemon( True )
    t.start()

    time.sleep(1)

    print "Now publishing new data"
    libpydmw.publish( "telemetry", "position", "hello", len("hello") )

    print "done. Did we get anything?"

    time.sleep(3)

