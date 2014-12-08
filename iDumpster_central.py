#!/usr/bin/env python

# iDumpster_central.py will run on the RPi server.
# It forks a web server and also starts subscribing to the trucks and dumpsters in the system.
# It is responsible to maintain the state information of the RPi server


import argparse
import re
import json
import pika
import pika.channel
import pika.exceptions
import signal
import sys
import os
import logging
import threading

# Components in the system
from util.component import Map
from util.component import Truck
from util.component import Dumpster
from util.component import State

# Enumeration class types
from util.component import TruckState
from util.component import component_type

# Object hook for decoding enumeration class types
from util.component import as_enum
from util.component import EnumEncoder
from util.component import as_map
from util.component import MapEncoder

from util.grid_structs import GridWithWeights

from util.grid_structs import FUEL_COST_PER_BLOCK

# A * search algorithm
from a_star.path_finder import A_Star_Search


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

def getJSONTrucks ():
  """
  Used by the web_server application to get the latest truck position and fuel updates
  """
  JSONTrucks = []
  current_state = environment_current_state.getCurrentState()
  all_component_names = current_state.keys()
  for component in all_component_names:
    if current_state[component]["type"] == component_type.Truck:
      Truck_dict = dict([('name', component), ('location', current_state[component]['location']), ('status', current_state[component]['status']), ('fuel_level', current_state[component]['fuel_level']), ('trash_level', current_state[component]['trash_level'])])
      JSONTrucks.append(Truck_dict)

  return JSONTrucks

def getJSONDumpsters ():
  """
  Used by the web_server application to get the latest dumpster position, trash level
  """
  JSONDumpsters = []
  current_state = environment_current_state.getCurrentState()
  all_component_names = current_state.keys()
  for component in all_component_names:
    if current_state[component]["type"] == component_type.Dumpster:
      Dumpster_dict = dict([('name', component), ('location', current_state[component]['location']), ('trash_level', current_state[component]['trash_level'])])
      JSONDumpsters.append(Dumpster_dict)

  return JSONDumpsters

def getJSONMap ():
  """
  Used by the web_server application to get the latest map information, for rendering it in the web page
  """
  json_map_data = json.dumps(environment_map, cls=MapEncoder)
  return json_map_data


def manhattan_distance(start_loc, end_loc):
  """
  Calculate Manhattan distance

  """
  (x1, y1) = start_loc
  (x2, y2) = end_loc
  return abs(pow(x1, 1) - pow(x2, 1)) + abs(pow(y1, 1) - pow(y2, 1))

def manage_overflowing_dumpster (overflowing_dumpster, channel):
  """
  Worker thread to manage overflowing dumpster

  """
  logging.info(overflowing_dumpster.getName() + "'s Thread")
  for component_name in environment_current_state.getCurrentState():
      if environment_current_state.type(component_name) == component_type.Truck:
          if environment_current_state.get(component_name, key="status") == TruckState.IDLE:
              # Calculate the trash capacity - trash collected by truck so far and
              # see if that is greater current dumpster's trash
              current_truck_trash_level = environment_current_state.get(component_name, key="trash_level")
              current_truck_trash_capacity = environment_current_state.get(component_name, key="trash_capacity")
              current_truck_trash_collected = current_truck_trash_level / 10.0 * current_truck_trash_capacity
              overflowing_dumpster_trash_content = overflowing_dumpster.getTrashCollected()
              if current_truck_trash_collected + overflowing_dumpster_trash_content < current_truck_trash_capacity:
                  # Calculate the fuel estimate for the round trip and see if the truck
                  # has that much amount of fuel left to go for a drive
                  current_truck_loc = environment_current_state.get(component_name, key="location")
                  current_truck_fuel_level = environment_current_state.get(component_name, key="fuel_level")
                  current_truck_fuel_capacity = environment_current_state.get(component_name, key="fuel_capacity")
                  current_truck_fuel_left = current_truck_fuel_level/10.0 * current_truck_fuel_capacity
                  overflowing_dumpster_loc = overflowing_dumpster.getLocation()
                  estimated_distance = manhattan_distance(current_truck_loc, overflowing_dumpster_loc)
                  # Assuming unit fuel consumed for unit distance
                  # Also for round trip time, we consider 2 times the estimated distance
                  estimated_fuel_consumed = FUEL_COST_PER_BLOCK * (estimated_distance * 2)
                  if current_truck_fuel_left > estimated_fuel_consumed:
                      # Create truck object
                      logging.info("Creating " + component_name + " object to parse the information to the A * search")
                      current_truck_selected = Truck(name=component_name, location={"x":current_truck_loc[0], "y": current_truck_loc[1]}, fuel_capacity=current_truck_fuel_capacity, fuel_level=current_truck_fuel_level, trash_capacity=current_truck_trash_capacity, trash_level=current_truck_trash_level, status=TruckState.BUSY)
                      with state_variable_lock:
                          environment_current_state.put(current_truck_selected)
                      # Use A * search to get the route
                      logging.info("Calculating " + component_name + " to " + overflowing_dumpster.getName() + " path")
                      a_star_instance = A_Star_Search(environment_map.graph, current_truck_selected, overflowing_dumpster)
                      a_star_path = a_star_instance.get_a_star_path()
                      came_from = a_star_instance.get_came_from()
                      path_information = {"status": TruckState.BUSY, "a_star_path": a_star_path}
                      print path_information
                      data = json.dumps(path_information, indent = 4, sort_keys=True,cls=EnumEncoder)
                      # Send the route the desired routing key
                      channel.basic_publish(exchange = "iDumpster_exchange", routing_key=component_name, body=data)
                      # print data
                      logging.info("Calculated Path using A * search sent to the truck under consideration")


def get_log_level(verbosity):
  """
  Parses an integer value between (0-4) to get the verbosity level

  :param verbosity: (int) Integer value between 0 - 4
  :return logging.LEVELS where LEVELS are defined inside logging module
  """
  if isinstance(verbosity, int):
    if verbosity == 0:
        return logging.CRITICAL
    elif verbosity == 1:
        return logging.ERROR
    elif verbosity == 2:
        return logging.WARNING
    elif verbosity == 3:
        return logging.INFO
    else:
        return logging.DEBUG
  return logging.DEBUG

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

def monitor_components(channel, delivery_info, msg_properties, msg):
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
        logging.warning("Ignoring message: Message type not found")

    elif status_msg["type"] == component_type.Dumpster:
        logging.info(delivery_info.routing_key + "'s Message Received")
        if "capacity" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'capacity' field")
        elif "location" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'location' field")
        elif "level" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'level' field")
        else:
            current_dumpster = Dumpster(name=delivery_info.routing_key, location=status_msg["location"], trash_capacity=status_msg["capacity"], trash_level=status_msg["level"])
            logging.info("Storing dumpster data in the state variable")
            environment_current_state.put(current_dumpster)

            if current_dumpster.getTrashLevel() > current_dumpster.ThresholdLevel:
                threading.Thread(target=manage_overflowing_dumpster, args=(current_dumpster, channel)).start()

    elif status_msg["type"] == component_type.Truck:
        logging.info(delivery_info.routing_key + "'s Message Received")
        if "trash_capacity" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'trash_capacity' field")
        elif "location" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'location' field")
        elif "trash_level" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'trash_level' field")
        elif "fuel_capacity" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'fuel_capacity' field")
        elif "fuel_level" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'fuel_level' field")
        elif "status" not in status_msg:
            logging.warning("Ignoring " + delivery_info.routing_key + "'s message: Missing 'status' field")
        else:
            current_truck = Truck(name=delivery_info.routing_key, location=status_msg["location"], trash_capacity=status_msg["trash_capacity"], trash_level=status_msg["trash_level"], fuel_level=status_msg["fuel_level"], fuel_capacity=status_msg["fuel_capacity"], status=status_msg["status"])
            logging.info("Storing truck data in the state variable")
            environment_current_state.put(current_truck)
            all_trucks_state[delivery_info.routing_key] = status_msg["status"]
    else:
        logging.warning("Ignoring message: Unknown type message received")

  except ValueError, ve:
    # Thrown by json.loads() if it couldn't parse a JSON object
    logging.warning("Discarding Message: received message couldn't be parsed")
  except NameError, ne:
    logging.error("Name Error has occured " + str(ne.message))
  except Exception, eee:
    logging.error("Unknown Error has occured " + str(eee.message))

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^

environment_current_state = State()
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
  parser.add_argument("-v", "--verbosity", help="The verbosity levels of logging ranging from 0 for ONLY CRITICAL logging to 4 for DEBUG", metavar="verbosity", default=4)
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

  verbosity = int(args.verbosity)
  log_level = get_log_level(verbosity)

  # Get both m and n dimensions of the map
  (m, n) = get_dimensions(map_size)

  # Truck State (IDLE or BUSY)

  all_trucks_state = {}

  # Bryse Flowers verbosity level code

  logging_format = '%(asctime)s ' + '%(msecs)d' + ' -- ' + '%(funcName)s(%(lineno)d)' + ' -- ' + ' %(levelname)s ' + ' -- ' + '%(message)s'
  logging_date_format = '%I:%M:%S %p'
  logging.basicConfig(level=log_level, format=logging_format, datefmt=logging_date_format)

  environment_map = Map(width=m, height=n, template='TEMPLATE_1')

  message_broker = None
  channel = None

  state_variable_lock = threading.Lock()

  try:
    # Connect to the message broker using the given broker address (host)
    # Use the virutal host (vhost) and credential information (credentials), if provided

    pika_parameters = pika.ConnectionParameters(host=host, virtual_host=vhost, credentials=credentials)
    message_broker = pika.BlockingConnection(pika_parameters)

    logging.info("A blocking connection named message_broker successfully created, now creating a channel")

    # Setup the channel and exchange
    channel = message_broker.channel()
    logging.info("Channel created, now declaring exchange 'iDumpster_exchange' of type 'direct'")

    # Exchange declaration, NOTE that this exchange is not a durable one
    channel.exchange_declare(exchange='iDumpster_exchange', type='direct')
    logging.info("Exchange declared successfully, now declaring an exclusive queue")


    # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is sent to this app
    signal_num = signal.SIGINT
    try:
      # Create a iDumpsterServerChannelEvents object to store a reference to the channel that will need to be shutdown if a signal is caught
      channel_manager = iDumpsterServerChannelHelper(channel)
      signal.signal(signal_num, channel_manager.stop_iDumpster_server)
      signal_num = signal.SIGTERM
      signal.signal(signal_num, channel_manager.stop_iDumpster_server)

    except ValueError, ve:
      logging.warning("Graceful shutdown may not be possible: Unsupported Signal: " + signal_num)

    # Create a queue
    # -------------------------
    # Creating an exclusive queue NOTE that the queue will only exists as long as the client is connected

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    logging.info("An exclusive queue declared successfully, now binding the queue and the exchange with the given routing key(s)")

    # Bind your queue to the message exchange, and register your new message event handler
    for topic in topics:
      channel.queue_bind(exchange='iDumpster_exchange', queue=queue_name, routing_key=topic)
    logging.info("Binding of exchange with the declared queue successful, now start pika's event loop by calling channel.basic_consume")

    # Start pika's event loop
    channel.basic_consume(monitor_components, queue=queue_name, no_ack=True)

    # Start pika's event loop
    logging.info("Pika's event loop started")

    channel.start_consuming()

  except pika.exceptions.ProbableAccessDeniedError, pade:
    logging.error("A Probable Access Denied Error occurred: " + str(pade.message))
    logging.info("Please enter a valid virtual host in the format '-p validhost'")

  except pika.exceptions.ProbableAuthenticationError, paue:
    logging.error("A Probable Authentication Error occurred: " + str(paue.message))
    logging.info("Please enter valid credentials in the format '-c username:password'")

  except pika.exceptions.AMQPChannelError, ache:
    logging.error("An AMQP Channel Error occurred: " + str(ache.message))

  except pika.exceptions.AMQPConnectionError, acoe:
    logging.error("An AMQP Connection Error occurred: " + str(acoe.message))
    logging.info("Please enter a valid RabbitMQ hostname in the format '-b RabbitMQHost'")

  except pika.exceptions.ChannelError, ce:
    logging.error("A Channel error occurred: " + str(ce.message))

  except pika.exceptions.AMQPError, ae:
    logging.error("An AMQP error occurred: " + str(ae.message))

  # General catch-all handler is our last resort
  except Exception, eee:
    logging.error("An unexpected exception occurred: " + str(eee.message))

  finally:
    # Attempt to gracefully shutdown the connection to the message broker
    # Closing the channel gracefully
    if channel is not None:
      logging.info("Exited pika event loop, closing channel and the message broker")
      channel.close()
      logging.info("Channel closed successfully")
    # For closing the connection gracefully
    if message_broker is not None:
      message_broker.close()
      logging.info("Message broker closed successfully, Shutting down gracefully!")
    sys.exit()

except NameError, ne:
  logging.error("A NameError has occurred: It is likely that an invalid command line" + str(ne.message))
  logging.info("Argument was passed. Please check your arguments and try again")
  sys.exit()
except Exception, ee:
  logging.error("An unexpected error occurred: " + str(ee.message))
  sys.exit()
