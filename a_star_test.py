#!/usr/bin/env python

from a_star.path_finder import A_Star_Search
from util.grid_structs import GridWithWeights
from util.grid_structs import draw_grid
from util.component import Truck
from util.component import Dumpster
import sys

graph = GridWithWeights(19, 19)

# Adding walls to the grid

for x in range(graph.width - 1):
    for y in range(graph.height - 1):
        if ((x * y) + ((x + 1) * y) + (x * (y + 1)) + ((x + 1) * (y + 1))) % 3:
            graph.walls.append((x, y))

# current_truck = Truck(name="truck1", location={"x": 17, "y": 19}, status="Happy", fuelCapacity=150, fuelFilled=110)
# current_dumpster = Dumpster(name="dumpster1", location={"x": 1, "y": 2}, capacity=1500, level=8.5)

draw_grid(graph)


print "Grids prepared with walls, Truck(s) at position T and Dumpster(s) at position D in picture"

draw_grid(graph, width=1, start=(0, 1), goal=(18, 16))
sys.exit(-1)


print "Grids prepared with walls, Truck(s) at position T and Dumpster(s) at position D in picture"

draw_grid(graph, width=1, start=(22, 16), goal=(36, 39))

# print "Applying A star search and finally getting the reconstructed path from truck to dumpster"

# a_star_instance1 = A_Star_Search(graph, current_truck, current_dumpster)
# print a_star_instance1.get_cost_so_far(dumpster2)
# print a_star_instance1.get_a_star_path()
