# drone-middleware
Drone middleware aims to become a platform for developers, researchers and organizations that want to 
integrate uav data with their own processes, especially for more dynamic missions where the flight plan
and circumstances change all the time, like in SAR operations.

The drone middleware can also be used to separate the usual concerns of a GCS and provide a testing and
research bed on how those sub-processes can work together. This stimulates creating libraries in the process,
which makes reuse in the same project and in different projects a lot easier.

The middleware also specifies a set of basic data messages that are received from other systems, like
drawing lines, icons and areas that are used to specify search areas, no-fly zones or points of interest
to circle. This supports the uav operator to replan their flight, as they have that data on-screen already.

## License

The license of this middleware uses ISC, a modified version of the very permissive BSD license.

> http://en.wikipedia.org/wiki/ISC_license

It further (for now) uses protobuf and ZeroMQ, both with permissive licenses too.

Protobuf uses the new BSD license:

> https://code.google.com/p/protobuf/

ZeroMQ uses the LGPL + static linking exception:

> http://zeromq.org/area:licensing

In short, you can use drone middleware in commercial applications and you only need to retain the copyright notice.

As per the licenses specification:

> Permission to use, copy, modify, and/or distribute this software for any
> purpose with or without fee is hereby granted, provided that the above
> copyright notice and this permission notice appear in all copies.

## Objectives

* Provide an abstraction wrapper library for uav communications. This abstraction is minimal and only contains the most critical of uav data like position and flight plan.
* Provide a means for "mission data storage". Processes can come and go and they use this storage to figure out the current state of the mission and uav's.
* Provide a "task manager" that keeps track of running processes and which can reconfigure the platform when mission objectives change.
* Allow for failure and rebooting of processes. Any process should be able to determine current mission status without being required to synchronize this with a vehicle that may be in the air.
* Make it easier for organizations to integrate a uav into their simulations.
* Specify a standardized mechanism for storing sets of data and make it easier to retrieve them.
* Specify a small set of drone commands that are common and allow the middleware to send those.
* Use "opaque" tunnels to hook up a gcs and uav talking the same protocol, so you still have full access to all functionality.
* Zero config networking. The abstraction libraries use bonjour to find out where to connect.
* Provide a nodeJS server which hooks into the communication layer and converts this from protobuf to json, so that browsers and tablets are easier to integrate.
* Create compressed packages of the mission after execution: gcs logs, streamed pics and video, mission data, uav logs, user commands, KML files, etc.
* Allow a compressed package of log files to be replayed on the middleware with gcs and uav logs synchronized with each other for review.

## Current status

* There is a wrapper library for C/C++ and python. More testing is required on the reliability of those libraries and wrappers.
* The development platform is Linux. It has not been tested on windows or mac osx yet.
* There is not yet a standard, default implementation that can serve as a very basic gcs running on the middleware.
* There are now vehicle messages, but many other messages need to be added.
* Bonjour integration is done.
* It's possible to send pprz vehicle data to either mavlink or pprz gcs's, where they show the position of that uav.
* Opaque tunnels exist for mavlink and pprz drones. Pprz tunnels need some extra work due to complexities in the protocol.

## How to build

The build is only confirmed on Linux and you need to download, build and install zeromq v4.0.5 for this to work:

> `http://zeromq.org/intro:get-the-software`

Then you need to have python installed and working and install the python zmq bindings to use the python wrapper:

> `pip install pyzmq`

Then:

* Clone the drone-middleware project from the github page.
* Build the subprojects under 'broker' and 'libdmw' using autotools: `autoconf`, `automake -a -c`, `./configure`, `make`, `sudo make install`
* Go into the 'pydmw' project and install it: `python setup.py build`, then `sudo python setup.py install`
* Install python bonjour: `pip install py-bonjour`

## Running the middleware

At the moment there's no task manager. You need to start the broker manually from the 'broker' directory and then applications
will connect to your broker from there. You can see these connections being established in `netstat -ant`, ports 5557 and 5558.

You can install the avahi service file in the `etc` directory into '/etc/avahi/services', which will allow the libraries to
connect to the broker automatically.

When the broker is started, you can simply import the 'dmw' module and use it like so:

    import dmw
    import threading
    import time

    def print_rcvd_message( msg_class, msg_name, sender, message ):
        print "%s.%s.%s: %s"%( msg_class, msg_name, sender, message)

    class SubscriptionThread(threading.Thread):
        def run(self):
            dmw.init_sub()
            dmw.subscribe( "telemetry", "position", "", print_rcvd_message ) 
            dmw.loop()

    if __name__ == "__main__":
        dmw.init()
        dmw.init_pub( "testinpython" )
        # Subscribe first on a separate thread (it enters a notification loop afterwards).
        t = SubscriptionThread()
        t.setDaemon( True )
        t.start()
        # Give the subscription time to start and subscribe.
        time.sleep(1)
        dmw.publish( "telemetry", "position", "14.1525354 102.23324324 25.3335" )
        # Give the thread time to process and receive the message.
        time.sleep(1)

In GUI applications you'll need to consider how data/model changes on the bus can be applied to the screen, because only the
app's main thread can update those components. The best way to do that is to receive the messages in any thread and then post
them onto a queue to be processed when the app is idle.

In other cases, you can just create a thread as shown and process them in their own thread. 

