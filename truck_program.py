#!/usr/bin/python
"""
This file contains truck_program.py which will send their status and receive paths which thereby they will follow to collect overflowing dumpsters
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
import threading

from random import randint
from random import uniform

from util.component import component_type
from util.component import TruckState

# Enumeration Encoder class inherits JSONEncoder to support enumerated types encoding
from util.component import EnumEncoder
from util.component import as_enum


# Global variable that controls running the app
publish_levels = True
prev_sensor_value = 0

class truckChannelHelper:
    """
    This helper class is used to manage a subscribing_channel and invoke handlers when signals are intercepted

    """

    def __init__(self, channel):
        """
        Create a new truckChannelHelper object

        :param channel: (pika.channel.Channel) The channel object to manage
        :raises ValueError: If channel does not appear to be valid
        :return: None
        """

        if isinstance(channel, pika.channel.Channel):
            self.__channel = channel

        else:
            raise ValueError("No valid channel to manage was passed in")

    def stop_truck_service(self, signal=None, frame=None):
        """
        Stops the pika event loop for the managed channel

        :param signal: (int) A number if a intercepted signal caused this handler to be run, otherwise None
        :param frame: A Stack Frame object, if an intercepted signall caused this handler to be run
        :return None
        """
        # Attempt to gracefully stop pika's event loop whenever a SIGINT is encountered
        # Subscribing loop is stopped by calling stop_consuming method of that respective channel
        self.__channel.stop_consuming()
        
        # Publishing loop is stopped by changing the global flag publish_levels which will stop publishing
        global publish_levels
        publish_levels = False



def publish_truck_status():
    data = json.dumps(truck_data,indent=4,sort_keys=True,cls=EnumEncoder)#put dict into JSON format
    publishing_channel.basic_publish(exchange = 'iDumpster_exchange', routing_key = topic,
                                  body = data)
    print "Sent: ", data

    # Sleep and then loop
    message_broker.add_timeout(2, publish_truck_status)

def receive_path_info(channel, delivery_info, msg_properties, msg):
    # if msg == None:
    #     return
    condition = msg != ""
    print msg
    print condition
    if msg is not "":
        try:
            recv_path_msg = json.loads(msg, object_hook=as_enum)

            if "status" not in recv_path_msg:
                print "Warning: Reply Message 'status' not found, Ignoring message"
            elif "a_star_path" not in recv_path_msg:
                print "Warning: Reply Message 'a_star_path' not found, Ignoring message"
            else:
                truck_data["status"] = recv_path_msg["status"]
                print recv_path_msg["a_star_path"]

        except ValueError, ve:
            print "Warning: Discarding message: received message couldn't be parsed" + str(ve.message)
        except NameError, ne:
            print "Warning: Name error has occurred " + str(ne.message)
        except Exception, eee:
            print "Error: Unknown error has occurred " + str(eee.message)


def stop_truck_service(signal, frame):
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
    # td.stop()

def get_truck_status():
    """
    Returns a dictionary with the fuel level, location, trash_level

    :return: (dict) The value returned will represent the level in the dumpster
    """
    # Will be triggered when we press keyboard keys,
    # w for going UP
    # s for going DOWN
    # a for going LEFT
    # d for going RIGHT
    # q for going diagonally UP-LEFT
    # e for going diagonally UP-RIGHT
    # z for going diagonally DOWN-LEFT
    # c for going diagonally DOWN-RIGHT
    # <space> to collect trash once in the dumpster block
    return dict()

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
            metavar="message broker", default="localhost", type=str,
            required=True)
    parser.add_argument("-p", "--path",
            help="Path to Virtual Host to connect to on the message broker.",
            metavar="virtual host", default="/", type=str)
    parser.add_argument("-c", "--credentials",
            help="Credentials to use when logging in to message broker",
            metavar="login:password", default=None)
    parser.add_argument("-k", "--key",
            help="The routing key for publishing messages to the message broker",
            metavar="routing key", default="iTruck", type=str, required=True)
    parser.add_argument("-tc", "--trash_capacity",
            help="Volume of trash that this truck will hold before becoming full",
            metavar="trash volume", default=0, type=int, required=True)
    parser.add_argument("-fc", "--fuel_capacity",
            help="Maximum Volume of fuel that this truck can hold",
            metavar="fuel volume", default=0, type=int, required=True)
    parser.add_argument("-ff", "--fuel_filled",
            help="Volume of fuel that is filled initially in the truck",
            metavar="fuel filled", default=0, type=int, required=True)
    parser.add_argument("-tf", "--trash_filled",
            help="Volume of trash that is filled initially in the truck",
            metavar="trash filled", default=0, type=int)
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
    trash_capacity = args.trash_capacity
    fuel_capacity = args.fuel_capacity
    fuel_filled = args.fuel_filled
    trash_filled = args.trash_filled
    location = [str(args.locx), str(args.locy)]

    # Ensure that the user specified the required arguments
    if args.locx < 0 or args.locy < 0:
        print "You must specify a valid x,y coordinate for the truck"
        sys.exit()

    # Ensure there is trash capacity
    if not trash_capacity > 0:
        print "The Truck's Trash capacity must have > 0 volume"
        sys.exit()

    # Ensure there is fuel capacity
    if not fuel_capacity > 0:
        print "The Truck's Fuel capacity mush have > 0 volume"
        sys.exit(-1)

    # Ensure there is fuel filled
    if not fuel_filled > 0:
        print "Please fill up some fuel so that the truck can start"
        sys.exit(-1)

    try:
        # Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials),
        # if provided
        pika_parameters = pika.ConnectionParameters(host=host,virtual_host=vhost,credentials=credentials)

        message_broker = pika.BlockingConnection(pika_parameters)
        

        # Setup the channel and exchange
        publishing_channel = message_broker.channel()
        publishing_channel.exchange_declare(exchange='iDumpster_exchange',type='direct')

        subscribing_channel = message_broker.channel()
        subscribing_channel.exchange_declare(exchange='Truck_exchange',type='direct')

        # td = Threaded_subscriber()

        # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
        # sent to this app
        signal_num = signal.SIGINT
        try:
            subscribing_channel_manager = truckChannelHelper(subscribing_channel)
            signal.signal(signal_num, subscribing_channel_manager.stop_truck_service)
            signal_num = signal.SIGTERM
            signal.signal(signal_num, subscribing_channel_manager.stop_truck_service)

        except ValueError, ve:
            print "Warning: Graceful shutdown may not be possible: Unsupported " \
                "Signal: " + signal_num       

        # location = ','.join(location) #make location a string
        location_dict = {"x": int(location[0]), "y": int(location[1])}
        # Create a data structure to hold the dumpster data
        truck_data = {'status': TruckState.IDLE, 'trash_capacity': trash_capacity, 'fuel_capacity': fuel_capacity, 'fuel_level': None, "trash_level": None, 'location': location_dict, 'type': component_type.Truck}
        truck_data["trash_level"] = trash_filled/float(trash_capacity) * 10.0
        truck_data["fuel_level"] = fuel_filled/float(fuel_capacity) * 10.0

        result = subscribing_channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        subscribing_channel.queue_bind(exchange='Truck_exchange', queue=queue_name, routing_key=topic)

        # threading.Thread(target=subscribing_for_path_info, args=(truck_data, subscribing_channel, queue_name, topic)).start()

        message_broker.add_timeout(2, publish_truck_status)

        subscribing_channel.basic_consume(receive_path_info, queue=queue_name, no_ack=True)

        subscribing_channel.start_consuming()

        # td.start()

        # Loop until the application is asked to quit

        # while(publish_levels):
        #     #   Publish the message (truck_msg) in JSON format to the
        #     #   broker under the user specified topic.
        #     #   cls=EnumEncoder from stackoverflow.com/questions/3768895/python-how-to-make-a-class-json-serializable
        #     data = json.dumps(truck_data,indent=4,sort_keys=True,cls=EnumEncoder)#put dict into JSON format
        #     publishing_channel.basic_publish(exchange = 'iDumpster_exchange', routing_key = topic,
        #                           body = data)
        #     # print "Sent: ", data

        #     # Sleep and then loop
        #     time.sleep(2.0)

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
        if publishing_channel is not None:
            publishing_channel.close()
        if subscribing_channel is not None:
            subscribing_channel.close()
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
