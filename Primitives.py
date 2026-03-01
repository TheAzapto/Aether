"""
Primitives.py - Collision shapes for the Aether Physics Engine

This module contains various primitive shapes used for collision detection.
Each shape knows how to compute its bounding properties and collision data.
"""

from Vector import Vector3
from enum import Enum
from typing import List


class ShapeType(Enum):
    """Enumeration of available shape types"""
    CIRCLE = "circle"
    AABB = "aabb"  # Axis-Aligned Bounding Box (Rectangle)
    POLYGON = "polygon"
    LINE = "line"


class Shape:
    """Base class for all collision shapes"""
    
    def __init__(self, shape_type: ShapeType):
        self._type = shape_type
    
    @property
    def type(self) -> ShapeType:
        return self._type
    
    def get_bounding_radius(self) -> float:
        """Returns the radius of a circle that fully contains this shape"""
        raise NotImplementedError
    
    def get_area(self) -> float:
        """Returns the area of the shape"""
        raise NotImplementedError
    
    def contains_point(self, point: Vector3) -> bool:
        """Check if a point is inside this shape"""
        raise NotImplementedError


class Circle(Shape):
    """
    Circle primitive shape.
    
    Defined by a radius. The center is determined by the RigidBody's position.
    """
    
    def __init__(self, radius: float = 1.0):
        super().__init__(ShapeType.CIRCLE)
        self._radius = max(0.001, radius)  # Ensure positive radius
    
    @property
    def radius(self) -> float:
        return self._radius
    
    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = max(0.001, value)
    
    def get_bounding_radius(self) -> float:
        return self._radius
    
    def get_area(self) -> float:
        import math
        return math.pi * self._radius ** 2
    
    def contains_point(self, point: Vector3, center: Vector3 = None) -> bool:
        """Check if point is inside circle (relative to center or origin)"""
        if center is None:
            center = Vector3(0, 0)
        diff = point - center
        return diff.length_squared <= self._radius ** 2
    
    def __repr__(self) -> str:
        return f"Circle(radius={self._radius})"


class AABB(Shape):
    """
    Axis-Aligned Bounding Box (Rectangle).
    
    Defined by half-width and half-height from center.
    The center is determined by the RigidBody's position.
    """
    
    def __init__(self, half_width: float = 1.0, half_height: float = 1.0):
        super().__init__(ShapeType.AABB)
        self._half_width = max(0.001, half_width)
        self._half_height = max(0.001, half_height)
    
    @property
    def half_width(self) -> float:
        return self._half_width
    
    @property
    def half_height(self) -> float:
        return self._half_height
    
    @property
    def width(self) -> float:
        return self._half_width * 2
    
    @property
    def height(self) -> float:
        return self._half_height * 2
    
    def get_bounding_radius(self) -> float:
        """Diagonal distance from center to corner"""
        return (self._half_width ** 2 + self._half_height ** 2) ** 0.5
    
    def get_area(self) -> float:
        return self.width * self.height
    
    def get_min_max(self, center: Vector3 = None) -> tuple:
        """Returns (min_x, min_y, max_x, max_y) bounds"""
        if center is None:
            center = Vector3(0, 0)
        return (
            center.x - self._half_width,
            center.y - self._half_height,
            center.x + self._half_width,
            center.y + self._half_height
        )
    
    def contains_point(self, point: Vector3, center: Vector3 = None) -> bool:
        """Check if point is inside AABB"""
        min_x, min_y, max_x, max_y = self.get_min_max(center)
        return (min_x <= point.x <= max_x) and (min_y <= point.y <= max_y)
    
    def __repr__(self) -> str:
        return f"AABB(width={self.width}, height={self.height})"


class Polygon(Shape):
    """
    Convex polygon shape.
    
    Defined by a list of vertices in local space (relative to center).
    Vertices should be in counter-clockwise order.
    """
    
    def __init__(self, vertices: List[Vector3]):
        super().__init__(ShapeType.POLYGON)
        if len(vertices) < 3:
            raise ValueError("Polygon must have at least 3 vertices")
        self._vertices = vertices
        self._compute_properties()
    
    def _compute_properties(self) -> None:
        """Pre-compute bounding radius and area"""
        # Bounding radius: max distance from origin to any vertex
        self._bounding_radius = max(v.length for v in self._vertices)
        
        # Area using shoelace formula
        n = len(self._vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self._vertices[i].x * self._vertices[j].y
            area -= self._vertices[j].x * self._vertices[i].y
        self._area = abs(area) / 2.0
    
    @property
    def vertices(self) -> List[Vector3]:
        return self._vertices
    
    @property
    def vertex_count(self) -> int:
        return len(self._vertices)
    
    def get_bounding_radius(self) -> float:
        return self._bounding_radius
    
    def get_area(self) -> float:
        return self._area
    
    def get_edge(self, index: int) -> tuple:
        """Returns (start_vertex, end_vertex) for edge at index"""
        n = len(self._vertices)
        return (self._vertices[index], self._vertices[(index + 1) % n])
    
    def get_edge_normal(self, index: int) -> Vector3:
        """Returns outward-facing normal for edge at index"""
        start, end = self.get_edge(index)
        edge = end - start
        # Perpendicular: rotate 90 degrees clockwise for outward normal (CCW vertices)
        normal = Vector3(edge.y, -edge.x)
        return normal.normalized()
    
    def contains_point(self, point: Vector3, center: Vector3 = None) -> bool:
        """Check if point is inside polygon using cross product method"""
        if center is None:
            center = Vector3(0, 0)
        
        # Translate point to local space
        local_point = point - center
        
        # Check if point is on the same side of all edges
        n = len(self._vertices)
        for i in range(n):
            start = self._vertices[i]
            end = self._vertices[(i + 1) % n]
            edge = end - start
            to_point = local_point - start
            # Cross product z-component (2D)
            cross = edge.x * to_point.y - edge.y * to_point.x
            if cross < 0:  # Point is on wrong side of edge
                return False
        return True
    
    def __repr__(self) -> str:
        return f"Polygon(vertices={self.vertex_count})"
    
    # Factory methods for common polygon shapes
    @staticmethod
    def create_regular(sides: int, radius: float) -> 'Polygon':
        """Create a regular polygon with given number of sides and circumradius"""
        import math
        if sides < 3:
            raise ValueError("Regular polygon must have at least 3 sides")
        
        vertices = []
        angle_step = 2 * math.pi / sides
        for i in range(sides):
            angle = i * angle_step - math.pi / 2  # Start from top
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append(Vector3(x, y))
        return Polygon(vertices)
    
    @staticmethod
    def create_triangle(base: float, height: float) -> 'Polygon':
        """Create an isosceles triangle centered at origin"""
        half_base = base / 2
        # Center the triangle vertically
        top_y = height * 2/3
        bottom_y = -height * 1/3
        return Polygon([
            Vector3(0, top_y),
            Vector3(-half_base, bottom_y),
            Vector3(half_base, bottom_y)
        ])


class Line(Shape):
    """
    Line segment shape (for walls, platforms, etc.)
    
    Defined by start and end points relative to center.
    """
    
    def __init__(self, start: Vector3, end: Vector3):
        super().__init__(ShapeType.LINE)
        self._start = start
        self._end = end
        self._length = (end - start).length
        self._normal = self._compute_normal()
    
    def _compute_normal(self) -> Vector3:
        """Compute perpendicular normal to line"""
        direction = self._end - self._start
        # Perpendicular (rotate 90 degrees)
        return Vector3(-direction.y, direction.x).normalized()
    
    @property
    def start(self) -> Vector3:
        return self._start
    
    @property
    def end(self) -> Vector3:
        return self._end
    
    @property
    def length(self) -> float:
        return self._length
    
    @property
    def normal(self) -> Vector3:
        return self._normal
    
    @property
    def direction(self) -> Vector3:
        return (self._end - self._start).normalized()
    
    def get_bounding_radius(self) -> float:
        """Max distance from origin to either endpoint"""
        return max(self._start.length, self._end.length)
    
    def get_area(self) -> float:
        """Lines have no area"""
        return 0.0
    
    def closest_point(self, point: Vector3, center: Vector3 = None) -> Vector3:
        """Find closest point on line segment to given point"""
        if center is None:
            center = Vector3(0, 0)
        
        world_start = self._start + center
        world_end = self._end + center
        
        line_vec = world_end - world_start
        point_vec = point - world_start
        
        line_len_sq = line_vec.length_squared
        if line_len_sq < Vector3._epsilon:
            return world_start
        
        # Project point onto line
        t = max(0, min(1, point_vec.dot(line_vec) / line_len_sq))
        return world_start + line_vec * t
    
    def contains_point(self, point: Vector3, center: Vector3 = None, tolerance: float = 0.01) -> bool:
        """Check if point is on line within tolerance"""
        closest = self.closest_point(point, center)
        return (point - closest).length <= tolerance
    
    def __repr__(self) -> str:
        return f"Line(start={self._start}, end={self._end})"
