#!/usr/bin/env python
"""
This file DataStructures defines different data structures like Graph, Queue, etc whose classes, fields and methods are defined

The square grid, with weights and draw utility functions are direct implementation found in:
    www.redblobgames.com/pathfinding/a-star/implementation.html
"""

FUEL_COST_PER_BLOCK = 1

# Utility functions for dealing with square grids

def draw_tile(graph, id, style, width, truck_loc=list(), dumps_loc=list(), a_star_path=list()):
  r = "-"
  if 'number' in style and id in style['number']: r = "%d" %(style['number'][id])
  if 'point_to' in style and style['point_to'].get(id, None) is not None:
    (x1, y1) = id
    (x2, y2) = style['point_to'][id]
    if x2 == x1 + 1: r = u'\u2192'.encode('utf-8')
    if x2 == x1 - 1: r = u"\u2190".encode('utf-8')
    if y2 == y1 + 1: r = u"\u2193".encode('utf-8')
    if y2 == y1 - 1: r = u"\u2191".encode('utf-8')
  if 'start' in style and id == style['start']: r = "T"
  elif 'goal' in style and id == style['goal']: r = "D"
  elif 'path' in style and id in style['path']: r = "@"
  elif id in truck_loc: r = "T"
  elif id in dumps_loc: r = "D"
  elif id in graph.walls: r = "#" # Use elif so walls don't overwrite others
  elif id in a_star_path: r = "*"
  return r

def draw_grid(graph, width=2, **style):
  for y in range(graph.height):
    for x in range(graph.width):
      print "%%-%ds" % width % draw_tile(graph, (x, y), style, width),
    print ""

def string_grid(graph, state, t_truck, t_dumps, **style):
  ret_val = ""
  dumps_loc = []
  truck_loc = []
  a_star_path = []

  # Preprocess Components to get locations of trucks/dumpsters
  for component in state.values():
    if component["type"] == t_dumps:
      dumps_loc.append((component["location"]["x"], component["location"]["y"]))
    elif component["type"] == t_truck:
      truck_loc.append((component["location"]["x"], component["location"]["y"]))
      if len(component.get("a_star_path", list())) > 0:
        a_star_path = component["a_star_path"]

  # Draw each point on the map
  for y in range(graph.height):
    for x in range(graph.width):
      ret_val += draw_tile(graph, (x, y), style, 1, truck_loc, dumps_loc, a_star_path) + " "
    ret_val += "\n"

  return ret_val

class SquareGrid(object):
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.walls = []

  def in_bounds(self, id):
    (x, y) = id
    return 0 <= x <= self.width and 0 <= y < self.height

  def passable(self, id):
    return id not in self.walls

  def neighbors(self, id):
    (x, y) = id
    # Considering Diagonal grids as neighbors too
    results = [(x + 1, y), (x + 1, y + 1), (x, y - 1), (x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y + 1), (x + 1, y - 1)]
    if (x + y) % 2 == 0: results.reverse() # aesthetics
    results = filter(self.in_bounds, results)
    results = filter(self.passable, results)
    return results

  def diagonal_neighbors(self, id):
    (x, y) = id
    # Only diagonal grids
    results = [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
    results = filter(self.in_bounds, results)
    results = filter(self.passable, results)

class GridWithWeights(SquareGrid):
  def __init__(self, width, height):
    super(GridWithWeights, self).__init__(width, height)
    self.default_weights = {}
    self.dist_weights = {}
    self.fuel_weights = {}

  def default_cost(self, a, b):
    return self.default_weights.get(b, 1)

  def distance_cost(self, a, b):
    (x1, y1) = a
    (x2, y2) = b
    distance = abs(pow(x1, 1) - pow(x2, 1)) + abs(pow(y1, 1) - pow(y2, 1))
    return self.dist_weights.get(distance, 1)

  def fuel_cost(self, a, b):
    (x1, y1) = a
    (x2, y2) = b
    distance = abs(pow(x1, 1) - pow(x2, 1)) + abs(pow(y1, 1) - pow(y2, 1))
    fuel = distance * FUEL_COST_PER_BLOCK
    return self.fuel_weights.get(fuel, 1)

