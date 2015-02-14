# drone-middleware
Drone middleware aims to make it easier to develop or put your own ground station together.
Where normal ground stations are usually large, monolith applications with most of the code implemented
in the same process, drone middleware takes a distributed and heterogeneous approach to solving these problems.

The idea is that it's easier for non-expert users to adjust existing code, put their own ground stations together
by selecting which processes are running and of course make their own contributions.

The middleware uses a broker for sending messages across the entire platform. The idea is to create a set of processes
that solve specific planning/alerting/monitoring/retrieval problems and use your language of choice to solve those.

The main purpose of the middleware project is to make ground control software and algorithms reusable and to give it 
the ability to evolve over time without having to rewrite algorithms in different languages. 

## Objectives

* Provide an abstraction wrapper library for communications. The abstraction allows easier substitution of the underlying transport and solves some technical issues of the specific transport implementation.
* Provide a means for "mission data storage". Processes can come and go and they use this storage to figure out the current state of the mission.
* Provide a "task manager" that keeps track of running processes and which can reconfigure the platform when mission objectives change.
* Allow for failure and rebooting of processes. Any process should be able to determine current mission status without being required to synchronize this with a vehicle that may be in the air.
* Specify a standardized mechanism for storing large sets of mission data like pictures and how to get to those data items.
* Specify a set of messages for ground control communications using a formal message definition. These are high level message definitions, not low-level drone messages/commands.
* Provide "link" apps which, based on how the mission changes state in the middleware, can send messages towards the vehicle to update the mission plan.
* Create an opaque bus to allow a "link" app and a "gcs" to connect and for a gcs to query current mission state from the middleware rather than the drone.
* Zero config networking. The abstraction libraries use bonjour to find out where to connect.
* Provide an implementation of a simple ground control station as a set of interacting and cooperating processes on the middleware.
* Provide a nodeJS server which hooks into the communication layer, but converts all bus messages in a binary format to json and vice versa (only those that are subscribed by a subscriber).
* Allow reuse of the initial mission plan.
* Create compressed packages of the mission after execution: gcs logs, streamed pics and video, mission data, uav logs, user commands, KML files, etc.
* Allow a compressed package of log files to be replayed on the middleware with gcs and uav logs synchronized with each other.

## Current status

* There is a wrapper library for C/C++ and python. Checks need to be added and automated unit tests should be integrated into the build.
* The development platform is Linux. It would be good to see if this can be built and run on windows and Mac OSX too.
* No standard implementation yet.
* No message specifications yet.
* No bonjour (zero config) implementation yet.

## How to build

The build is only confirmed on Linux and you need to download, build and install zeromq v4.0.5 for this to work:

> `http://zeromq.org/intro:get-the-software`

Then you need to have python installed and working and install the python zmq bindings to use the python wrapper:

> `pip install pyzmq`

Then:

* Clone the drone-middleware project from the github page.
* Build the subprojects under 'broker' and 'libdmw' using autotools: 'autoconf', 'automake -a -c', './configure', 'make', 'sudo make install'
* Go into the 'pydmw' project and install it: 'python setup.py build', then 'sudo python setup.py install'

## Running the middleware

At the moment there's no task manager. You need to start the broker manually from the 'broker' directory and then applications
will connect to your broker from there. You can see these connections being established in netstat -ant, ports 5557 and 5558.
Eventually, the idea is to publish on bonjour where the broker is located, so it's easier to find other processes.

When the broker is started, you can simply import the 'dmw' module and use it like so:

`import dmw
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
    dmw.init_pub( "testinpython" )

    # Subscribe first
    t = SubscriptionThread()
    t.setDaemon( True )
    t.start()

    time.sleep(1)

    dmw.publish( "telemetry", "position", "hello" )

    time.sleep(3)
`


