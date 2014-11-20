#!/usr/bin/python
"""
This file contains iDumpster.py which will read the sensor values over I2C and
send them via RabbitMQ to the central server
"""

import pika
import pika.exceptions
import signal
import sys
import time
import json
from random import randint

# Global variable that controls running the app
publish_levels = True
result = 1
def stop_dumpster_service(signal, frame):
    """
    A signal handler, that will cause the main execution loop to stop

    :param signal: (int) A number if a intercepted signal caused this handler
                   to be run, otherwise None
    :param frame: A Stack Frame object, if an intercepted signal caused this
                  handler to be run
    :return: None
    """
    global publish_levels
    publish_levels = False

def read_Sensor():
    """
    Returns a value with the dumpster level

    :return: (val) The value returned will represent the level in the dumpster
    """
    global result
    result = randint(1,9)
    return result

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^^

# Guard try clause to catch any errors that aren't expected
try:
    #Set each of the default values
    # The message broker host name or IP address
    host = None
    # The virtual host to connect to
    vhost = "/" # Defaults to the root virtual host
    # The credentials to use
    credentials = None
    # The topic to subscribe to
    topic = None
    # Capacity of the dumpster (must be greater than zero) units: yards^3
    capacity = 0
    # Location of the dumpster (must be entered as "x,y" coordinate
    location = [-1,-1]

    #parse through command line arguments and assign parameters
    #if nothing is passed, defaults as set above are used
    if sys.argv:
        for i in range(0,len(sys.argv)):
            if sys.argv[i] == "-b":
                host = sys.argv[i+1]
            elif sys.argv[i] == "-p":
                vhost = sys.argv[i+1]
            elif sys.argv[i] == "-c":
                credentials = sys.argv[i+1]
		credentials = credentials.split(':')
		username = credentials[0]
		password = credentials[1]
		credentials = pika.PlainCredentials(username, password)
            elif sys.argv[i] == "-k":
                topic = sys.argv[i+1]
            elif sys.argv[i] == "-v":
                capacity = sys.argv[i+1]
            elif sys.argv[i] == "-m":
                location = sys.argv[i+1]
                location = location.split(',')

    # Ensure that the user specified the required arguments
    if host is None:
        print "You must specify a message broker to connect to"
        sys.exit()

    if topic is None:
        print "You must specify a topic to subscribe to"
        sys.exit()

    if capacity == 0:
        print "You must specify the dumpster capacity"
        sys.exit()
    if location[0] < 0 or location[1] < 0:
        print "You must specify a valid x,y coordinate for the dumpster"
        sys.exit()
        
    # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
    # sent to this app
    signal_num = signal.SIGINT
    try:
        signal.signal(signal_num, stop_dumpster_service)
        signal_num = signal.SIGTERM
        signal.signal(signal_num, stop_dumpster_service)

    except ValueError, ve:
        print "Warning: Graceful shutdown may not be possible: Unsupported " \
                "Signal: " + signal_num    

    try:
        # Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials),
        # if provided
        message_broker = pika.BlockingConnection(pika.ConnectionParameters(
        host,virtual_host=vhost,credentials=credentials))
        # Setup the channel and exchange
        channel = message_broker.channel()
        channel.exchange_declare(exchange='dumpster_data',type='direct')

        location = ','.join(location) #make location a string
        # Create a data structure to hold the dumpster data
        dumpster_data = {'capacity': capacity, 'level': None, 'location': location}
        # Create a list of levels so level can be averaged over past 5 values
        level = []
        #grab first 5 values for level data
        for i in range(0,5):
            level.insert(0,read_Sensor())
            time.sleep(2)
        print level
            
        # Loop until the application is asked to quit
        while(publish_levels):
            # Read level
            level.insert(0,read_Sensor()) #inserts new reading at start of list
            level.pop() #removes last item in list
            print level
            
            #compute average of previous 5 values
            x = float(sum(level))
            y = float(len(level))
            dumpster_data['level'] = x/y
            print dumpster_data['level']
            #   Publish the message (utilization_msg) in JSON format to the
            #   broker under the user specified topic.
            data = json.dumps(dumpster_data,indent=4,sort_keys=True)#put dict into JSON format
            
            channel.basic_publish(exchange = 'dumpster_data', routing_key = topic,
                                  body = data)
            print "Sent: ", data

            # Sleep and then loop
            time.sleep(2.0)

    except pika.exceptions.ProbableAccessDeniedError, pade:
        print >> sys.stderr, "Error: A Probable Access Denied Error occured: " + str(pade.message)
        print "Please enter a valid virtual host in the format '-p validhost'"

    except pika.exceptions.ProbableAuthenticationError, aue:
        print >> sys.stderr, "Error: A Probable Authentication error occured: " + str(aue.message)
        print "Please enter a valid username/password in the format '-c username:password'"
        
    except pika.exceptions.AMQPConnectionError, acoe:
        print >> sys.stderr, "Error: An AMQP Connection Error occured: " + str(acoe.message)
        print "Please enter a valid RabbitMQ host name in the format '-b WabbitHost'"

    except pika.exceptions.AMQPChannelError, ache:
        print >> sys.stderr, "Error: An AMQP Channel Error occured: " + str(ache.message)
    
    except pika.exceptions.ChannelError, ce:
        print >> sys.stderr, "Error: A channel error occured: " + str(ce.message)
    except pika.exceptions.AMQPError, ae:
        print >> sys.stderr, "Error: An AMQP Error occured: " + str(ae.message)
    #General catch-all handler as last resort
    except Exception, eee:
        print >> sys.stderr, "Error: An unexpected exception occured: " + str(eee.message)
    
    finally:
        # Attempt to gracefully shutdown the connection to the message broker
        print "Application Shutting Down..."
        if channel is not None:
            channel.close()
        if message_broker is not None:
            message_broker.close()
        sys.exit()
except NameError, ne:
    print "Error: A NameError has occured: It is likely that an invalid command line"
    print "argument was passed.Please check your arguments and try again"
    print "Error message: " + ne.message
    sys.exit()
except Exception, ee:
    print "Error: An unexpected error occurred: " + ee.message
    sys.exit()
