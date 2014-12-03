# This is a python module that handles the data structure for the system's components.
# Any new component are defined here by creating a class and a constructor for initializing itself.
# For e.g. A truck when defined as a component can be defined as
# class truck:
#  current_location = None
#  fuel = None
#  garbage = None
#  status = None
#  def __init__(location_tuple, fuel_level, garbage_level, status):
#


# ^^^^^^^^^^^^^^^ For serializing enum class objects ^^^^^^^^^^^^^^^^^^^

# Class type objects are not serializabe using json, so we create a
# custom encoder and inherit the JSONEncoder's default method and
# convert the object into string and return encode using JSONEncoder
# We also define as_enum, an object_hook method which helps in
# decoding the string based object to enum object. Referred from:
# stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

import json
# import logging
from copy import deepcopy
from enum import Enum
from grid_structs import GridWithWeights


FUEL_COST_PER_STEP = 2

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)

def as_enum(d):
    if "__enum__" in d:
        name, member = d["__enum__"].split(".")
        return getattr(globals()[name], member)
    else:
        return d

class component_type(Enum):
    Dumpster = 1
    Truck = 2

class TruckState(Enum):
    IDLE = 0
    BUSY = 1

class State:
    def __init__(self):
        self.__state = {}
        # logging.info("Initializing environment")
        print "Initializing Environment State"

    def put(self, component):
        component_name = component.getName()
        if component_name not in self.__state:
            self.__state[component_name] = component.getInfo()
        # Updating existing component entirely
        else:
            # print "WARNING: Updating existing component"
            self.__state[component_name] = component.getInfo()

    def update(self, component_name, key, value):
        if component_name not in self.__state:
            print "ERROR: Updating component that is not present in the current state"
        else:
            if key == "location":
                self.__state[component_name][key]["x"] = value[0]
                self.__state[component_name][key]["y"] = value[1]
            else:
                self.__state[component_name][key] = value

    def get(self, component_name, **optional_parameters):
        if component_name not in self.__state:
            print "ERROR: Component not present in the State object"
            return
        else:
            if "key" in optional_parameters:
                if "location" in optional_parameters["key"]:
                    return (self.__state[component_name]["location"]["x"], self.__state[component_name]["location"]["y"])
                else:
                    return self.__state[component_name][optional_parameters["key"]]
            else:
                return self.__state[component_name]

    def exist(self, component_name):
        return component_name in self.__state

    def delete(self, component_name):
        if component_name in self.__state:
            del self.__state[component_name]
        else:
            # logging.error("Trying to remove non-existing component")
            print "ERROR: Component not present in the State object"

    def getCurrentState(self):
        return deepcopy(self.__state)

    def type(self, component_name):
        return self.__state[component_name]["type"]

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.graph = GridWithWeights(width, height)
        self.add_template('TEMPLATE_1')

    def add_template(self, design_type):
        if design_type == 'TEMPLATE_1':
            # Adding walls
            for x in range(self.width):
                for y in range(self.height):
                    if ((x * y) + ((x + 1) * y) + (x * (y + 1)) + ((x + 1) * (y + 1))) % 3:
                        self.graph.walls.append((x, y))

            # Adding default weights
            passable_nodes = []
            for x in range(self.width):
                for y in range(self.height):
                    if (x, y) not in self.graph.walls:
                        passable_nodes.append((x, y))
            self.graph.default_weights = {location: 0 for location in passable_nodes}

            # TODO Adding distance weights
            # Diagonal movement costs 14 units and orthogonal movement costs 10 units
            # diag_block_dist = abs(pow(1, 1) - pow(0, 1)) + abs(pow(0, 1) - pow(1, 1))
            # ortho_block_dist = abs(pow(1, 1) - pow(0, 1)) + abs(pow(0, 1) - pow(0, 1))
            # self.graph.dist_weights = {diag_block_dist: 14, ortho_block_dist: 10}

            # TODO Adding fuel weights
            # diag_fuel_cost = diag_block_dist * FUEL_COST_PER_STEP
            # ortho_fuel_cost = diag_block_dist * FUEL_COST_PER_STEP
            # self.graph.dist_weights = {diag_fuel_cost: 7, ortho_fuel_cost: 5}


""" This python class, dumpster will provide both definition of fields and methods
for creating dumpster and maintaining the state of the dumpsters
"""

class Dumpster:
    __info = {"location": {"x": None, "y": None}, "type": component_type.Dumpster}
    ThresholdLevel = 5
    def __init__(self, name, location, trash_capacity, trash_level):
        self.__info["name"] = name
        self.__info["location"]["x"] = location["x"]
        self.__info["location"]["y"] = location["y"]
        self.__info["trash_level"] = trash_level
        self.__info["trash_capacity"] = trash_capacity

    def getTrashLevel(self):
        return self.__info["trash_level"]

    def getTrashCollected(self):
        return self.__info["trash_level"]/10.0 * self.__info["trash_capacity"]

    def getLocation(self):
        return (self.__info["location"]["x"], self.__info["location"]["y"])

    def getName(self):
        return self.__info["name"]

    def getInfo(self):
        return deepcopy(self.__info)

""" Class truck defines methods to create new truck, get location, get status, etc.
"""

class Truck:
    # Truck dictionary to store the truck information
    __info = {"location": {"x": None, "y": None}, "type": component_type.Truck}

    def __init__(self, name, location, fuel_capacity, trash_capacity, fuel_level, trash_level, status):
        self.__info["name"] = name
        self.__info["location"]["x"] = location["x"]
        self.__info["location"]["y"] = location["y"]
        self.__info["trash_level"] = trash_level
        self.__info["trash_capacity"] = trash_capacity
        self.__info["fuel_level"] = fuel_level
        self.__info["fuel_capacity"] = fuel_capacity
        self.__info["status"] = status

    def getFuelLevel(self):
        return self.__info["fuel_level"]

    def getFuelConsumed(self):
        return self.__info["fuel_level"]/10.0 * self.__info["fuel_capacity"]

    def getTrashLevel(self):
        return self.__info["trash_level"]

    def getTrashCollected(self):
        return self.__info["trash_level"]/10.0 * self.__info["trash_capacity"]

    def getLocation(self):
        return (self.__info["location"]["x"], self.__info["location"]["y"])

    def getName(self):
        return self.__info["name"]

    def getInfo(self):
        return deepcopy(self.__info)

    def getStatus(self):
        return self.__info["status"]
