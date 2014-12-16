#!/usr/bin/python
"""
This file contains iDumpster.py which will read the sensor values over I2C and
send them via RabbitMQ to the central server
"""
import argparse
import re
import pika
import pika.exceptions
import signal
import sys
import time
import json
from VCNL4000 import VCNL4000

from util.component import component_type
from util.component import EnumEncoder

# Global variable that controls running the app
publish_levels = True

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

# Initialise the VNCL4000 sensor
vcnl = VCNL4000(0x13)
result = 0
def read_Sensor():
    """
    Returns a value with the dumpster level

    :return: (val) The value returned will represent the level in the dumpster
    """
    global result
    try:
        x = vcnl.read_proximity()
        if x <= 2280:
                result = 0
        elif x >= 2290 and x <= 2399:
                result = 0.33
        elif x >= 2400 and x <= 2920:
                result = 0.66
        elif x >= 2950:
                result = 1
    except Exception:
        return result #if I2C doesn't respond, result value doesn't change
    return result

def get_credentials(cmd_cred):
    '''Translate a <username>:<password> string to a Pika credential'''
    if isinstance(cmd_cred, str):
        cred_re = r"(?P<un>.+)[:](?P<pw>.+)"

        match = re.search(cred_re, cmd_cred)

        if match:
            return pika.PlainCredentials(match.group("un"),
                                         match.group("pw"),
                                         True)
        else:
            raise RuntimeError("Credentials Failed Regex Validation")

    # Guest Credentials as None
    return None

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^^

# Guard try clause to catch any errors that aren't expected
try:
    # Create the argument parser
    parser = argparse.ArgumentParser()

    # Add All Desired Arguments to the Parser
    parser.add_argument("-b", "--broker_address",
            help="This is the ip address or domain of the message broker",
            metavar="message broker", default="omaha.local", type=str,
            required=True)
    parser.add_argument("-p", "--path",
            help="Path to Virtual Host to connect to on the message broker.",
            metavar="virtual host", default="/", type=str)
    parser.add_argument("-c", "--credentials",
            help="Credentials to use when logging in to message broker",
            metavar="login:password", default=None)
    parser.add_argument("-k", "--key",
            help="The routing key for publishing messages to the message broker",
            metavar="routing key", default="iDumpster", type=str, required=True)
    parser.add_argument("-v", "--capacity",
            help="Volume that this trash can will hold before becoming full",
            metavar="volume", default=0, type=int, required=True)
    parser.add_argument("-x", "--locx",
            help="Fake location of the dumpster on x axis", metavar="x",
            default="0", type=int, required=True)
    parser.add_argument("-y", "--locy",
            help="Fake location of the dumpster on y axis", metavar="y",
            default="0", type=int, required=True)

    # Parse arguments
    args = parser.parse_args()

    # Store Arguments
    host = args.broker_address
    vhost = args.path
    # This will throw a runtime exception with improper formatted cli
    credentials = get_credentials(args.credentials)
    topic = args.key
    capacity = args.capacity
    location_dict = {"x": args.locx, "y": args.locy}

    # Ensure that the user specified the required arguments
    if args.locx < 0 or args.locy < 0:
        print "You must specify a valid x,y coordinate for the dumpster"
        sys.exit()

    # Ensure there is dumpster capacity
    if not capacity > 0:
        print "The dumpster must have > 0 volume"
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
        channel.exchange_declare(exchange='iDumpster_exchange',type='direct')

        # Create a data structure to hold the dumpster data
        dumpster_data = {'capacity': capacity, 'level': None, 'location': location_dict, 'type': component_type.Dumpster}

        # Loop until the application is asked to quit
        while(publish_levels):

            #read sensor level
            level = read_Sensor()
            dumpster_data['level'] = level
            time.sleep(2)

            #   Publish the message in JSON format to the
            #   broker under the user specified topic.
            #   cls=EnumEncoder from stackoverflow.com/questions/3768895/python-how-to-make-a-class-json-serializable
            data = json.dumps(dumpster_data,indent=4,sort_keys=True,cls=EnumEncoder)#put dict into JSON format

            channel.basic_publish(exchange = 'iDumpster_exchange', routing_key = topic,
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
