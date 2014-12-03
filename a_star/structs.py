#!/usr/bin/env python
"""
This file DataStructures defines different data structures like Graph, Queue, etc whose classes, fields and methods are defined

The square grid, with weights and draw utility functions are direct implementation found in:
    www.redblobgames.com/pathfinding/a-star/implementation.html
"""

import heapq
from enum import Enum

# Utility functions for dealing with square grids

def draw_tile(graph, id, style, width):
  r = "."
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
  if id in graph.walls: r = "#" # * width
  return r

def draw_grid(graph, width=2, **style):
  for y in range(graph.height):
    for x in range(graph.width):
      print "%%-%ds" % width % draw_tile(graph, (x, y), style, width),
    print ""

class PriorityQueue:
  def __init__(self):
    self.elements = []

  def empty(self):
    return len(self.elements) == 0

  def put(self, item, priority):
    heapq.heappush(self.elements, (priority, item))

  def get(self):
    return heapq.heappop(self.elements)[1]


