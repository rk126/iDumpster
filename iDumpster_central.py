#!/usr/bin/env python

# iDumpster_central.py will run on the RPi server.
# It forks a web server and also starts subscribing to the trucks and dumpsters in the system.
# It is responsible to maintain the state information of the RPi server


import logging
import argparse
import re
import json
import pika
import pika.channel
import pika.exceptions
import signal
import sys
from util.component import truck
from util.component import dumpster
from util.component import environment_state
from util.component import as_enum
from util.component import component_type
from a_star.structs import GridWithWeights
from a_star.path_finder import A_Star_Search

# Create truck1
# truck1 = truck(name="truck1", location=(1, 0), status="Just got created", fuelFilled=120, fuelCapacity=150)

# Create dumpster1
# dumpster1 = dumpster(name="dumpster1", location=(3, 4), capacity=1000)
# dumpster1.updateTrashLevel(1.5)

class iDumpsterServerChannelHelper:
  """
  This helper class is used to manage a channel and invoke event handlers when signals are intercepted
  """

  def __init__(self, channel):
    """
    Create a new iDumpsterServerChannelHelper object

    :param channel: (pika.channel.Channel) The channel object to manage
    :raises ValueError: if channel does not appear to be valid
    :return: None
    """

    if isinstance(channel, pika.channel.Channel):
      self.__channel = channel

    else:
      raise ValueError("No valid channel to manage was passed in")

  def stop_iDumpster_server(self, signal=None, frame=None):
    """
    Stops the pika event loop for the managed channel

    :param signal: (int) A number if a intercepted signal caused this handler to be run, otherwise None
    :param frame: A Stack Frame object, if an intercepted signal caused this handler to be run
    :return: None
    """
    # Attempt to gracefully stop pika's event loop whenever a SIGINT is encountered
    self.__channel.stop_consuming()


def get_credentials(cred_cmd):
  """
  Parses a string of type <username>:<password> to a Pika credential

  :param cred_cmd: (str) String of format <username>:<password>
  :return Pika Credentials: (pika.PlainCredentials)
  """
  if isinstance(cred_cmd, str):
    cred_re = r"""(?P<un>.+)[:](?P<pw>.+)"""

    match = re.search(cred_re, cred_cmd)

    if match:
      return pika.PlainCredentials(match.group("un"), match.group("pw"), True)

    else:
      raise RuntimeError("Credentials Failed Regex Validation")

    # Guest Credentials as None
    return None

def get_dimensions(map_size_cmd):
  """
  Parses a string of type <m>x<n> to get a (m, n) tuple
  :param map_size_cmd: (str) String of format <m>x<n>
  :return map_size_tuple: (tuple) (m, n) tuples where m and n are of format integers
  """
  if isinstance(map_size_cmd, str):
    map_size_re = r"""(?P<m>\d+)[x](?P<n>\d+)"""
    match = re.search(map_size_re, map_size_cmd)

    if match:
      return (int(match.group("m")), int(match.group("n")))

    else:
      raise RuntimeError("Map Size Failed Regex Validation")

    # Default Map size as (10, 10)
    return (10, 10)

def monitor_dumpster_levels(channel, delivery_info, msg_properties, msg):
  """
  Event handler that processes new messages from the message broker

  :param channel: (pika.Channel) The channel object this message was received from
  :param delivery_info: (pika.spec.Basic.Deliver) Delivery information related to the message just received
  :param msg_properties: (pika.spec.BasicProperties) Additional metadata about the message just received
  :param msg: The message received from the server
  :return None
  """

  # Parse the JSON message into a dict
  # We use stackoverflow.com/questions/24481852/serializing-an-enum-member-to-json
  # We use the object_hook function "as_enum" defined in util.component
  try:
    status_msg = json.loads(msg, object_hook=as_enum)

    # Check that the message appears to be well formed

    if "type" not in status_msg:
        logger.warn("Ignoring message: Unknown message type")

    elif status_msg["type"] == component_type.Dumpster:
        if "capacity" not in status_msg:
            logger.warn("Ignoring message: Missing 'capacity' field")
        elif "location" not in status_msg:
            logger.warn("Ignoring message: Missing 'location' field")
        elif "level" not in status_msg:
            logger.warn("Ignoring message: Missing 'level' field")
        else:
            current_state = environment_current_state.getCurrentState()
            # logger.info("Dumpster data received")
            current_dumpster = dumpster(name=delivery_info.routing_key, location=status_msg["location"], capacity=status_msg["capacity"], level=status_msg["level"])
            if delivery_info.routing_key not in current_state:
                environment_current_state.add_component(current_dumpster)
                current_state = environment_current_state.getCurrentState()
            else:
                current_state = environment_current_state.updateComponentValue(current_dumpster, "level", status_msg["level"])
                current_state = environment_current_state.updateComponentLocation(current_dumpster, status_msg["location"])
            if current_dumpster.getTrashLevel() > current_dumpster.ThresholdLevel:
                # Call A* search functions to start finding optimized, currently assuming there is a truck in the state variable.
                # In actual program we will pick up a truck that is nearest and has good amount of fuel and is less filled with trash
                # In actual program we will pick up this info from the state information
                current_truck = truck(name="truck1", location={"x": 17,"y": 19}, status=9, fuelCapacity=150, fuelFilled=110)
                global a_star_running
                if not a_star_running:
                    A_Star_Search(environment_map, current_truck, current_dumpster)
                    a_star_running = 1

    elif status_msg["type"] == component_type.Truck:
        if "status" not in status_msg:
            logger.warn("Ignoring message: Missing 'status' field")
        elif "location" not in status_msg:
            logger.warn("Ignoring message: Missing 'location' field")
        else:
            logger.info("Truck  data received")
    else:
        logger.warn("Unknown type message received")

  except ValueError, ve:
    # Thrown by json.loads() if it couldn't parse a JSON object
    logger.warn("Discarding Message: received message couldn't be parsed")
  except NameError, ne:
    logger.error("Name Error has occured " + str(ne.message))
  except Exception, eee:
    logger.error("Unknown Error has occured " + str(eee.message))

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

environment_current_state = environment_state()
global a_star_running
a_star_running = 0

# Guard try clause to catch any errors that aren't expected
try:
  # Create the argument parser
  parser = argparse.ArgumentParser()

  # Add All Desired Arguments to the Parser
  parser.add_argument("-b", "--broker_address", help="This is the IP address or Hostname of the message broker", metavar="message broker", default="localhost", type=str, required=True)
  parser.add_argument("-p", "--virtual_host", help="Virtual host to connect to the message broker", metavar="virtual host", default="/", type=str)
  parser.add_argument("-c", "--credentials", help="Credentials to use when logging in to the message broker", metavar="login:password", default=None, type=str)
  parser.add_argument("-k", "--routing_key", help="The routing key that are subscribed to the message broker", metavar="routing key", nargs="*", default="iDumpster", type=str, required=True)
  # Parsing map dimensions using argparser,
  # TODO read it using yaml so that even map environment can be loaded, else have to parse everything through command line which is cumbersome
  parser.add_argument("-s", "--map_size", help="The mxn dimension map size that will be generated at start", metavar="map dimensions", default="10x10", type=str, required=True)

  # Parse arguments
  args = parser.parse_args()

  # Store Arguments
  host = args.broker_address
  vhost = args.virtual_host

  # This will throw a runtime exception with improper formatted cli TODO credits to Bryse
  credentials = get_credentials(args.credentials)
  topics = args.routing_key
  map_size = args.map_size

  # Get both m and n dimensions of the map
  (m, n) = get_dimensions(map_size)

  environment_map = GridWithWeights(m, n)

  logger.info("Before channel creation")

  message_broker = None
  channel = None

  try:
    # Connect to the message broker using the given broker address (host)
    # Use the virutal host (vhost) and credential information (credentials), if provided

    pika_parameters = pika.ConnectionParameters(host=host, virtual_host=vhost, credentials=credentials)
    message_broker = pika.BlockingConnection(pika_parameters)

    logger.info("A blocking connection named message_broker successfully created, now creating a channel")

    # Setup the channel and exchange
    channel = message_broker.channel()
    logger.info("Channel created, now declaring exchange 'dumpster_data' of type 'direct'")

    # Exchange declaration, NOTE that this exchange is not a durable one
    channel.exchange_declare(exchange='dumpster_data', type='direct')
    logger.info("Exchange declared successfully, now declaring an exclusive queue")


    # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is sent to this app
    signal_num = signal.SIGINT
    try:
      # Create a iDumpsterServerChannelEvents object to store a reference to the channel that will need to be shutdown if a signal is caught
      channel_manager = iDumpsterServerChannelHelper(channel)
      signal.signal(signal_num, channel_manager.stop_iDumpster_server)
      signal_num = signal.SIGTERM
      signal.signal(signal_num, channel_manager.stop_iDumpster_server)

    except ValueError, ve:
      logger.warn("Graceful shutdown may not be possible: Unsupported Signal: " + signal_num)

    # Create a queue
    # -------------------------
    # Creating an exclusive queue NOTE that the queue will only exists as long as the client is connected

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    logger.info("An exclusive queue declared successfully, now binding the queue and the exchange with the given routing key(s)")

    # Bind your queue to the message exchange, and register your new message event handler
    for topic in topics:
      channel.queue_bind(exchange='dumpster_data', queue=queue_name, routing_key=topic)
    logger.info("Binding of exchange with the declared queue successful, now start pika's event loop by calling channel.basic_consume")

    # Start pika's event loop
    channel.basic_consume(monitor_dumpster_levels, queue=queue_name, no_ack=True)

    # Start pika's event loop
    logger.info("Pika's event loop started")

    channel.start_consuming()

  except pika.exceptions.ProbableAccessDeniedError, pade:
    logger.error("A Probable Access Denied Error occurred: " + str(pade.message))
    logger.info("Please enter a valid virtual host in the format '-p validhost'")

  except pika.exceptions.ProbableAuthenticationError, paue:
    logger.error("A Probable Authentication Error occurred: " + str(paue.message))
    logger.info("Please enter valid credentials in the format '-c username:password'")

  except pika.exceptions.AMQPChannelError, ache:
    logger.error("An AMQP Channel Error occurred: " + str(ache.message))

  except pika.exceptions.AMQPConnectionError, acoe:
    logger.error("An AMQP Connection Error occurred: " + str(acoe.message))
    logger.info("Please enter a valid RabbitMQ hostname in the format '-b RabbitMQHost'")

  except pika.exceptions.ChannelError, ce:
    logger.error("A Channel error occurred: " + str(ce.message))

  except pika.exceptions.AMQPError, ae:
    logger.error("An AMQP error occurred: " + str(ae.message))

  # General catch-all handler is our last resort
  except Exception, eee:
    logger.error("An unexpected exception occurred: " + str(eee.message))

  finally:
    # Attempt to gracefully shutdown the connection to the message broker
    # Closing the channel gracefully
    if channel is not None:
      logger.info("Exited pika event loop, closing channel and the message broker")
      channel.close()
      logger.info("Channel closed successfully")
    # For closing the connection gracefully
    if message_broker is not None:
      message_broker.close()
      logger.info("Message broker closed successfully, Shutting down gracefully!")
    sys.exit()

except NameError, ee:
  logger.error("A NameError has occurred: It is likely that an invalid command line" + str(ne.message))
  logger.info("Argument was passed. Please check your arguments and try again")
  sys.exit()
except Exception, ee:
  logger.error("An unexpected error occurred: " + ee.message)
  sys.exit()
