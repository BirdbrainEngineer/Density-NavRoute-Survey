import json
from pathlib import Path
from typing import Any
import math
import matplotlib.pyplot as plt
from enum import Enum, auto


class SmoothingMode(Enum):
    simple = auto()
    harmonic = auto()
    NONE = auto()

type Coords = tuple[float, float, float]

data: dict[str, Any] = json.load(Path("test_route.json").open())
data2: dict[str, Any] = json.load(Path("test_route2.json").open())
data3: dict[str, Any] = json.load(Path("test_route3.json").open())

max_jump_range: float = data["MaxRange"]
max_jump_range2: float = data2["MaxRange"]
max_jump_range3: float = data3["MaxRange"]

SMOOTHING_MODE = SmoothingMode.harmonic

MAXIMUM_DENSITY: float = 20.0

# Not using numpy because its typing is an **absolutely degenerate mess**

def get_unit_vector(vec: Coords) -> Coords:
    inv_magnitude = 1/math.dist((0, 0, 0), vec)
    return (vec[0] * inv_magnitude, vec[1] * inv_magnitude, vec[2] * inv_magnitude)

def vec_subtract(a: Coords, b: Coords) -> Coords:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def vec_add(a: Coords, b: Coords) -> Coords:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def vec_scale(vec: Coords, scalar: float) -> Coords:
    return (vec[0] * scalar, vec[1] * scalar, vec[2] * scalar)

def get_vec(origin: Coords, destination: Coords) -> Coords:
    return vec_subtract(destination, origin)

def get_dist(origin: Coords, destination: Coords) -> float:
    return abs(math.dist(origin, destination))

def get_magnitude(vec: Coords) -> float:
    return math.dist((0, 0, 0), vec)

def move_along_vec(vec: Coords, dist: float) -> Coords:
    unit_vec = get_unit_vector(vec)
    return vec_scale(unit_vec, dist)

def get_point_along_leg(origin: Coords, destination: Coords, distance: float) -> tuple[Coords, float]: 
    # returns the point and the distance that is still required to reach destination. 
    # Negative numbers mean that the point lies beyond the destination. Positive numbers give the distance left to destination.
    vec = get_vec(origin, destination)
    vec_len = get_magnitude(vec)
    point = move_along_vec(vec, distance)
    return (point, vec_len - distance)

def vec_dot(a: Coords, b: Coords) -> float:
    return ((a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2]))

def vec_scalar_proj(a: Coords, b: Coords) -> float:
    dot_product = vec_dot(a, b)
    magnitude = math.dist((0, 0, 0), b)
    return dot_product / magnitude

def vec_scalar_frac_proj(a: Coords, b: Coords) -> float:
    dot_product = vec_dot(a, b)
    magnitude = math.dist((0, 0, 0), b)
    return dot_product / magnitude**2

def vec_proj(a: Coords, b: Coords) -> Coords:
    return vec_scale(b, vec_scalar_frac_proj(a, b))


class Tortuosity:
    tortuosity: float
    derivative: float
    derivative_integral: float

    def __init__(self, tortuosity: float = 0, derivative: float = 0, derivative_integral: float = 0) -> None:
        self.tortuosity = tortuosity
        self.derivative = derivative
        self.derivative_integral = derivative_integral


class Sample:
    origin_coords: Coords
    dest_coords: Coords
    jump_vector: Coords
    jump_distance: float
    distance_along_route: float
    density: float
    density_smoothed: float
    density_derivative: float
    centroid_coords: Coords
    tort_small: Tortuosity
    tort_medium: Tortuosity
    tort_large: Tortuosity

    def __init__(self, coords: Coords, destination_coords: Coords, route_start_coords: Coords, route_end_coords: Coords, max_jump_distance: float) -> None:
        self.origin_coords = coords
        self.dest_coords = destination_coords
        self.jump_vector = get_vec(coords, destination_coords)
        self.jump_distance = math.dist( coords, destination_coords)
        self.tort_small = Tortuosity()
        self.tort_medium = Tortuosity()
        self.tort_large = Tortuosity()
        self.density, self.centroid_coords = self.get_density_and_centroid(route_end_coords, max_jump_distance)
        if self.density > MAXIMUM_DENSITY: self.density = MAXIMUM_DENSITY # Always active filtering
        self.density_smoothed = self.density
        self.distance_along_route = abs(self.get_distance_along_route(route_start_coords, route_end_coords))
        self.density_derivative = 0

    def get_distance_along_route(self, start: Coords, end: Coords) -> float:
        route_vec = get_vec(start, end)
        return vec_scalar_proj(vec_subtract(start, self.centroid_coords), route_vec)

    def get_density_and_centroid(self, ideal_target_vec: Coords, max_jump_range: float) -> tuple[float, Coords]:
        d = get_magnitude(get_vec(self.origin_coords, ideal_target_vec))
        r_1 = max_jump_range
        r_2 = get_magnitude(get_vec(self.dest_coords, ideal_target_vec))
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
        centroid_direction = get_unit_vector(get_vec(self.origin_coords, ideal_target_vec))
        centroid = vec_add(vec_scale(centroid_direction, d_c), self.origin_coords)
        return (rho, centroid)
    
    def get_kernel_center(self, next_jump_target: Coords) -> Coords:
        j = self.origin_coords
        d = self.jump_vector
        c = get_vec(self.origin_coords, self.centroid_coords)
        u = get_unit_vector(get_vec(self.dest_coords, next_jump_target))
        s = vec_scalar_proj(c, d)
        k = vec_add(vec_add(vec_scale(u, (s - get_magnitude(d))), d), j)
        return k

        
class Route:
    max_jump_range: float
    route_start_coords: Coords
    route_end_coords: Coords
    kernel_small: float
    kernel_medium: float
    kernel_large: float
    route: list[Sample]     # route is shorter by 1 entry than 'raw_route', because the last jump in the route is always invalid

    def __init__(self, max_jump_range: float, raw_route: list[dict[str, Any]]) -> None:
        self.max_jump_range = max_jump_range
        self.kernel_small = max_jump_range * 2.44 # Based on Rayleigh criterion and Nyquist-Shannon sampling theorem
        #self.kernel_medium = max_jump_range * 2 * 2.88
        #self.kernel_large = max_jump_range * 4 * 2.44
        self.route_start_coords = raw_route[0]["StarPos"]
        self.route_end_coords = raw_route[len(raw_route) - 1]["StarPos"]
        self.route = []
        coords: Coords = raw_route[0]["StarPos"]
        dest_coords: Coords = coords
        # First pass - generate densities
        for i in range(len(raw_route) - 2):
            dest_coords = raw_route[i+1]["StarPos"]
            self.route.append(Sample(coords, dest_coords, self.route_start_coords, self.route_end_coords, self.max_jump_range))
            coords = dest_coords
        # Second pass - generate tortuosities and density derivatives
        # Third pass - generate derivatives of tortuosities
        # Fourth pass - generate space-wise integrals of derivatives of tortuosities

        # Fifth pass - Apply smoothing
        for i in range(len(self.route)):
            match SMOOTHING_MODE:
                case SmoothingMode.simple:
                    if i == len(self.route) - 1:
                        k = self.route[i].dest_coords
                        negative_distance_left = (self.kernel_small / 2) - get_dist(k, self.route[i].dest_coords)
                        positive_distance_left = self.kernel_small / 2
                        positive_area = 0
                        integrated_area = 0
                    else:
                        k = self.route[i].get_kernel_center(self.route[i+1].dest_coords)
                        negative_distance_left = (self.kernel_small / 2) - get_dist(k, self.route[i].dest_coords)
                        positive_distance_left = (self.kernel_small / 2) - get_dist(k, self.route[i+1].dest_coords)
                        integrated_area = ((self.route[i].density + self.route[i+1].density) / 2) * get_dist(self.route[i].dest_coords, self.route[i+1].dest_coords)
                    negative_area, negative_dist_remaining = self.recursive_average_integration(i, -1, negative_distance_left)
                    if i + 1 == len(self.route) - 1:
                        positive_area, positive_dist_remaining = (0, positive_distance_left)
                    else:
                        positive_area, positive_dist_remaining = self.recursive_average_integration(i+1, 1, positive_distance_left)
                    total_distance_remaining = negative_dist_remaining + positive_dist_remaining
                    total_area = integrated_area + negative_area + positive_area
                    average = total_area / (self.kernel_small - total_distance_remaining)
                    self.route[i].density_smoothed = average

                case SmoothingMode.harmonic:
                    exponent = 1
                    if i == len(self.route) - 1:
                        k = self.route[i].dest_coords
                        negative_distance_left = (self.kernel_small / 2) - get_dist(k, self.route[i].dest_coords)
                        positive_distance_left = self.kernel_small / 2
                        positive_area = 0
                        integrated_area = 0
                    else:
                        k = self.route[i].get_kernel_center(self.route[i+1].dest_coords)
                        negative_distance_left = (self.kernel_small / 2) - get_dist(k, self.route[i].dest_coords)
                        positive_distance_left = (self.kernel_small / 2) - get_dist(k, self.route[i+1].dest_coords)
                        integrated_area = (1 / ((self.route[i].density + self.route[i+1].density) / 2)) * get_dist(self.route[i].dest_coords, self.route[i+1].dest_coords)
                    negative_area, negative_dist_remaining = self.recursive_harmonic_average_integration(i, -1, negative_distance_left, exponent)
                    if i + 1 == len(self.route) - 1:
                        positive_area, positive_dist_remaining = (0, positive_distance_left)
                    else:
                        positive_area, positive_dist_remaining = self.recursive_harmonic_average_integration(i+1, 1, positive_distance_left, exponent)
                    total_distance_remaining = negative_dist_remaining + positive_dist_remaining
                    total_area = integrated_area + negative_area + positive_area
                    average = ((self.kernel_small - total_distance_remaining) / total_area)**(1/exponent)
                    self.route[i].density_smoothed = average

                case SmoothingMode.NONE:
                    pass

    def find_average(self, i: int, kernel_size: float) -> float:
        half_kernel_size = kernel_size / 2
        positive = self.recursive_average_integration(i, 1, half_kernel_size)
        negative = self.recursive_average_integration(i, -1, half_kernel_size)
        average = (positive[0] + negative[0]) / (kernel_size - (positive[1] + negative[1]))
        assert average > 0
        return average
 
    def recursive_average_integration(self, i: int, direction: int, kernel_size_left: float) -> tuple[float, float]: # returns (integrated area, kernel window size left if any)
        if i + direction <= 0 or i + direction >= len(self.route):  # truncates the kernel if it has hit one of the endpoints
            return (0, kernel_size_left)
        point, size_left = get_point_along_leg(self.route[i].origin_coords, self.route[i+direction].origin_coords, kernel_size_left)
        leg_length = get_dist(self.route[i].origin_coords, self.route[i+direction].origin_coords)
        if size_left <= 0:
            integrated_area: float = ((self.route[i].density + self.route[i+direction].density) / 2) * leg_length
            recursion = self.recursive_average_integration(i + direction, direction, abs(size_left))
            return (integrated_area + recursion[0], recursion[1])
        else:
            scalar: float = kernel_size_left / leg_length
            density_diff = self.route[i].density - self.route[i+direction].density
            density_diff *= scalar
            integrated_area: float = ((self.route[i+direction].density + density_diff) / 2) * kernel_size_left
            return (integrated_area, 0)
        
    def recursive_harmonic_average_integration(self, i: int, direction: int, kernel_size_left: float, exponent: float,) -> tuple[float, float]: # returns (integrated area, kernel window size left if any)
        if i + direction <= 0 or i + direction >= len(self.route):  # truncates the kernel if it has hit one of the endpoints
            return (0, kernel_size_left)
        point, size_left = get_point_along_leg(self.route[i].origin_coords, self.route[i+direction].origin_coords, kernel_size_left)
        leg_length = get_dist(self.route[i].origin_coords, self.route[i+direction].origin_coords)
        if size_left <= 0:
            integrated_area: float = (1 / ((self.route[i].density + self.route[i+direction].density) / 2))**exponent * leg_length
            recursion = self.recursive_average_integration(i + direction, direction, abs(size_left))
            return (integrated_area + recursion[0], recursion[1])
        else:
            scalar: float = kernel_size_left / leg_length
            density_diff = self.route[i].density - self.route[i+direction].density
            density_diff *= scalar
            integrated_area: float = (1 / ((self.route[i+direction].density + density_diff) / 2))**exponent * kernel_size_left
            return (integrated_area, 0)
        


route = Route(max_jump_range, data["Route"])
route2 = Route(max_jump_range2, data2["Route"])
route3 = Route(max_jump_range3, data3["Route"])

#for i, leg in enumerate(route.route):
#    print(f"{i:<4}- rho: {round(leg.density_smoothed, 8):<20}route_dist: {leg.distance_along_route}")


#x_axis = [sample.distance_along_route for sample in route.route]
#y_axis = [sample.density for sample in route.route]
y_axis_smoothed = [sample.density_smoothed for sample in route.route]
x_axis = [sample.distance_along_route for sample in route.route]
y_axis = [sample.density for sample in route.route]

x_axis2 = [sample.distance_along_route for sample in route2.route]
y_axis2 = [sample.density_smoothed for sample in route2.route]

x_axis3 = [sample.distance_along_route for sample in route3.route]
y_axis3 = [sample.density_smoothed for sample in route3.route]


plt.figure(figsize=(18, 8))
plt.yscale('log')
plt.plot(x_axis, y_axis, alpha=0.25, label=f"Raw densities ({round(route.max_jump_range, 2)}ly)")
plt.plot(x_axis, y_axis_smoothed, 'g', label='Rayleigh-distance harmonic average')
#plt.plot(x_axis, y_axis, 'r', label=f"{round(route.max_jump_range, 2)}ly")
#plt.plot(x_axis2, y_axis2, 'g', label=f"{round(route2.max_jump_range, 2)}ly")
#plt.plot(x_axis3, y_axis3, 'b', label=f"{round(route3.max_jump_range, 2)}ly")

plt.legend()  # Shows the labels
plt.xlabel('Distance (ly)')
plt.ylabel('Density (stars/ly^3)')
plt.show()
