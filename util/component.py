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
from enum import Enum

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

class environment_state:
    def __init__(self):
        self.__state = {}

    def isComponentPresent(self, component):
        component_name = component.getName()
        return component_name in self.__state

    def add_component(self, component):
        component_name = component.getName()
        if component_name not in self.__state:
            self.__state[component_name] = component.getInfo()
        else:
            print "ERROR: Component already present"

    def remove_component(self, component):
        component_name = component.getName()
        if component_name in self.__state:
            del self.__state[component_name]
        else:
            print "ERROR: Trying to remove non-existing component"

    def getCurrentState(self):
        return self.__state

    def updateComponentValue(self, component, key, value):
        self.__state[component.getName()][key] = value
        return self.__state

    def updateComponentLocation(self, component, location):
        self.__state[component.getName()]["location"]["x"] = location["x"]
        self.__state[component.getName()]["location"]["y"] = location["y"]
        return self.__state

""" This python class, dumpster will provide both definition of fields and methods
for creating dumpster and maintaining the state of the dumpsters
"""

class dumpster:
    __info = {"name":None, "level":None, "location":{"x":None, "y":None}}
    __meta = {"dumpsterCapacity":5000,"trashLevel":0}
    ThresholdLevel = 8

    def __init__(self, name, location, capacity, level):
        self.__info["name"] = name
        self.__info["location"]["x"] = location["x"]
        self.__info["location"]["y"] = location["y"]
        self.__info["level"] = level
        self.__meta["dumpsterCapacity"] = capacity
        self.__meta["trashLevel"] = level/10.0 * capacity

    # def updateTrashLevel(self, value):
    #     self.__info["value"] = value
    #     self.__meta["trashLevel"] = value/100.0 * self.__meta["dumpsterCapacity"]

    def getLocation(self):
        return (self.__info["location"]["x"], self.__info["location"]["y"])

    def getName(self):
        return self.__info["name"]

    def getTrashLevel(self):
        return self.__info["level"]

    def getInfo(self):
        return self.__info

""" Class truck defines methods to create new truck, get location, get status, etc.
"""

class truck:
    # Truck dictionary to store the truck information
    __info = {"name":None, "status":None, "location":{"x":None, "y":None}}
    __meta = {"fuelCapacity":150, "fuelRemaining":0, "trashCapacity":30, "trashCollected":0}
    def __init__(self, name, location, status, fuelCapacity, fuelFilled):
        self.__info["name"] = name
        self.__info["location"]["x"] = location["x"]
        self.__info["location"]["y"] = location["y"]
        self.__info["status"] = status
        self.__meta["fuelCapacity"] = fuelCapacity

        if not fuelFilled:
            assert fuelFilled, "Forgot to add fuelCapacity"
        else:
            self.__meta["fuelRemaining"] = fuelCapacity - fuelFilled

    def getFuelStatus(self):
        return (self.__meta["fuelCapacity"] - self.__meta["fuelRemaining"])

    def getLocation(self):
        return (self.__info["location"]["x"], self.__info["location"]["y"])

    def getStatus(self):
        return self.__info["status"]

    def getName(self):
        return self.__info["name"]

    def getInfo(self):
        return self.__info
