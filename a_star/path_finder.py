#!/usr/bin/env python
"""
Creates instances of truck/overflowing-dumpster/landfill and calculates route information according to the state information with the entire path finding triggered by a threshold

The algorithm can calculate multiple independent truck - overflowing dumpster - landfill triad and takes optimized decisions

Took help from the existing algorithm implementation from: www.redblobgames.com/pathfinding/a-star/implementation.html
In both learning and implementing A * search algorithm in Python

The algorithm also takes care of the environmental object like trees, other components, etc
"""

from structs import PriorityQueue
# TODO Either merge draw_grid utilities with SquareGrid data structure or put it in util module
from structs import draw_grid
import logging

TEST_PROGRAM_ACTIVE = 1
FUEL_COST_PER_STEP = 2

class A_Star_Search:
  __came_from = {}
  __cost_so_far = {}
  __a_star_path = []
  __compA = None
  __compB = None
  def __init__(self, graph, compA, compB):
    self.__compA = compA
    self.__compB = compB
    start = self.__compA.getLocation()
    goal = self.__compB.getLocation()
    if not (graph.in_bounds(start) and graph.in_bounds(goal)):
      logger.error("Either of the component is out of bounds")
    else:
      self.__came_from, self.__cost_so_far = self.a_star_search(graph, start, goal)
      self.__a_star_path = self.reconstruct_path(self.__came_from, start, goal)
    if TEST_PROGRAM_ACTIVE:
      draw_grid(graph, width=1, path=self.__a_star_path, start=start, goal=goal)

  def reconstruct_path(self, came_from, start, goal):
    current = goal
    path = [current]
    while current != start:
      current = came_from[current]
      path.append(current)
    return path

  def distance_estimate(self, a, b):
    (x1, y1) = a
    (x2, y2) = b
    estimated_distance = abs(pow(x1, 1) - pow(x2, 1)) + abs(pow(y1, 1) - pow(y2, 1))
    return estimated_distance

  def fuel_estimate(self, a, b):
    return self.distance_estimate(a, b) * FUEL_COST_PER_STEP

  def a_star_search(self, graph, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    # TODO change cost_so_far[start] to account for fuel cost
    # cost_so_far[start] = self.__compA.getFuelStatus()

    while not frontier.empty():
      current = frontier.get()

      if current == goal:
        break

      for next in graph.neighbors(current):
        new_cost = cost_so_far[current] + graph.default_cost(current, next) + graph.distance_cost(current, next) + graph.fuel_cost(current, next)
        if next not in cost_so_far or new_cost < cost_so_far[next]:
          cost_so_far[next] = new_cost
          priority = new_cost + self.distance_estimate(goal, next) + self.fuel_estimate(goal, next) # heuristics
          frontier.put(next, priority)
          came_from[next] = current

    return came_from, cost_so_far

  def get_cost_so_far(self, id):
    return self.__cost_so_far[id]

  def get_a_star_path(self):
    reversed_path = self.__a_star_path
    reversed_path.reverse()
    return reversed_path
