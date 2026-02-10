import json
from pathlib import Path
from typing import Any
import math


data: dict[str, Any] = json.load(Path("test_route.json").open())

max_jump_range: float = data["MaxRange"]

# Not using numpy because its typing is an **absolutely degenerate mess**

def get_unit_vector(vec: tuple[float, float, float]) -> tuple[float, float, float]:
    inv_magnitude = 1/math.dist((0, 0, 0), vec)
    return (vec[0] * inv_magnitude, vec[1] * inv_magnitude, vec[2] * inv_magnitude)

def vec_subtract(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def vec_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def vec_scale(vec: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return (vec[0] * scalar, vec[1] * scalar, vec[2] * scalar)

def get_vector(origin: tuple[float, float, float], destination: tuple[float, float, float]) -> tuple[float, float, float]:
    return vec_subtract(destination, origin)

def get_dist_ab(origin: tuple[float, float, float], destination: tuple[float, float, float]) -> float:
    return math.dist(origin, destination)

def get_dist(vec: tuple[float, float, float]) -> float:
    return math.dist((0, 0, 0), vec)

def move_along_vec(vec: tuple[float, float, float], dist: float) -> tuple[float, float, float]:
    unit_vec = get_unit_vector(vec)
    return vec_scale(unit_vec, dist)

def get_point_along_leg(origin: tuple[float, float, float], destination: tuple[float, float, float], distance: float) -> tuple[tuple[float, float, float], float]: 
    # returns the point and the distance that is still required to reach destination. 
    # Negative numbers mean that the point lies beyond the destination. Positive numbers give the distance left to destination.
    vec = get_vector(origin, destination)
    vec_len = get_dist(vec)
    point = move_along_vec(vec, distance)
    return (point, vec_len - distance)


class Tortuosity:
    tortuosity: float
    derivative: float
    derivative_integral: float

    def __init__(self, tortuosity: float = 0, derivative: float = 0, derivative_integral: float = 0) -> None:
        self.tortuosity = tortuosity
        self.derivative = derivative
        self.derivative_integral = derivative_integral


class Sample:
    origin_coords: tuple[float, float, float]
    dest_coords: tuple[float, float, float]
    jump_vector: tuple[float, float, float]
    distance: float
    density: float
    centroid_coords: tuple[float, float, float]
    tort_small: Tortuosity
    tort_medium: Tortuosity
    tort_large: Tortuosity

    def __init__(self, coords: tuple[float, float, float], destination_coords: tuple[float, float, float], route_end_coords: tuple[float, float, float], max_jump_distance: float) -> None:
        self.origin_coords = coords
        self.dest_coords = destination_coords
        self.jump_vector = get_vector(coords, destination_coords)
        self.distance = math.dist( coords, destination_coords)
        self.tort_small = Tortuosity()
        self.tort_medium = Tortuosity()
        self.tort_large = Tortuosity()
        self.density, self.centroid_coords = self.get_density_and_centroid(route_end_coords, max_jump_distance)

    def get_density_and_centroid(self, ideal_target_vec: tuple[float, float, float], max_jump_range: float) -> tuple[float, tuple[float, float, float]]:
        d = get_dist(get_vector(self.origin_coords, ideal_target_vec))
        r_1 = max_jump_range
        r_2 = get_dist(get_vector(self.dest_coords, ideal_target_vec))
        d_1 = (d**2 + r_1**2 - r_2**2) / (2 * d)
        d_2 = (d**2 + r_2**2 - r_1**2) / (2 * d)
        h_1 = r_1 - d_1
        h_2 = r_2 - d_2
        vol_1 = (math.pi * h_1**2 * (3 * r_1 - h_1)) / 3
        vol_2 = (math.pi * h_2**2 * (3 * r_2 - h_2)) / 3
        vol_ex = vol_1 + vol_2
        rho = 1 / vol_ex
        h_c = (h_1 + h_2) / 2
        d_c = max_jump_range - h_c
        centroid_direction = get_unit_vector(ideal_target_vec)
        centroid = vec_scale(centroid_direction, d_c)
        return (rho, centroid)

        

class Route:
    max_jump_range: float
    kernel_small: float
    kernel_medium: float
    kernel_large: float
    route: list[Sample]

    def __init__(self, max_jump_range: float) -> None:
        self.max_jump_range = max_jump_range
        self.kernel_small = max_jump_range * 2.44 # Based on Rayleigh criterion and Nyquist-Shannon sampling theorem
        self.kernel_medium = max_jump_range * 4.88
        self.kernel_large = max_jump_range * 9.76
        self.route = []

    