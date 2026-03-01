"""
Collision.py - Shape-specific collision detection for the Aether Physics Engine

This module implements precise collision detection between different primitive shapes:
- Circle vs Circle
- Circle vs AABB
- AABB vs AABB
- Circle vs Polygon (SAT-based)
- AABB vs Polygon (SAT-based)
- Polygon vs Polygon (SAT-based)
"""

from Vector import Vector3
from Primitives import Shape, ShapeType, Circle, AABB, Polygon, Line
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class CollisionResult:
    """Result of a collision detection check"""
    colliding: bool
    normal: Vector3  # Collision normal (direction to push body_a away from body_b)
    penetration: float  # Overlap depth
    contact_point: Vector3  # Point of contact


def detect_collision(shape_a: Shape, pos_a: Vector3, 
                     shape_b: Shape, pos_b: Vector3) -> Optional[CollisionResult]:
    """
    Main collision detection dispatcher.
    Returns CollisionResult if shapes are colliding, None otherwise.
    """
    type_a = shape_a.type
    type_b = shape_b.type
    
    # Circle vs Circle
    if type_a == ShapeType.CIRCLE and type_b == ShapeType.CIRCLE:
        return circle_vs_circle(shape_a, pos_a, shape_b, pos_b)
    
    # Circle vs AABB (order matters for normal direction)
    if type_a == ShapeType.CIRCLE and type_b == ShapeType.AABB:
        return circle_vs_aabb(shape_a, pos_a, shape_b, pos_b)
    if type_a == ShapeType.AABB and type_b == ShapeType.CIRCLE:
        result = circle_vs_aabb(shape_b, pos_b, shape_a, pos_a)
        if result:
            # Flip normal since we swapped the order
            result.normal = result.normal * -1
        return result
    
    # AABB vs AABB
    if type_a == ShapeType.AABB and type_b == ShapeType.AABB:
        return aabb_vs_aabb(shape_a, pos_a, shape_b, pos_b)
    
    # Circle vs Polygon
    if type_a == ShapeType.CIRCLE and type_b == ShapeType.POLYGON:
        return circle_vs_polygon(shape_a, pos_a, shape_b, pos_b)
    if type_a == ShapeType.POLYGON and type_b == ShapeType.CIRCLE:
        result = circle_vs_polygon(shape_b, pos_b, shape_a, pos_a)
        if result:
            result.normal = result.normal * -1
        return result
    
    # AABB vs Polygon (treat AABB as polygon)
    if type_a == ShapeType.AABB and type_b == ShapeType.POLYGON:
        return aabb_vs_polygon(shape_a, pos_a, shape_b, pos_b)
    if type_a == ShapeType.POLYGON and type_b == ShapeType.AABB:
        result = aabb_vs_polygon(shape_b, pos_b, shape_a, pos_a)
        if result:
            result.normal = result.normal * -1
        return result
    
    # Polygon vs Polygon (SAT)
    if type_a == ShapeType.POLYGON and type_b == ShapeType.POLYGON:
        return polygon_vs_polygon(shape_a, pos_a, shape_b, pos_b)
    
    # Fallback: no collision for unsupported pairs (like LINE)
    return None


def circle_vs_circle(circle_a: Circle, pos_a: Vector3, 
                     circle_b: Circle, pos_b: Vector3) -> Optional[CollisionResult]:
    """Detect collision between two circles"""
    diff = pos_b - pos_a
    dist_sq = diff.length_squared
    radius_sum = circle_a.radius + circle_b.radius
    
    if dist_sq >= radius_sum * radius_sum:
        return None  # No collision
    
    dist = dist_sq ** 0.5
    
    if dist < Vector3._epsilon:
        # Circles are at same position, push apart along arbitrary axis
        normal = Vector3(1, 0)
        penetration = radius_sum
    else:
        normal = diff / dist
        penetration = radius_sum - dist
    
    # Contact point is on the surface of circle_a toward circle_b
    contact = pos_a + normal * circle_a.radius
    
    return CollisionResult(
        colliding=True,
        normal=normal,
        penetration=penetration,
        contact_point=contact
    )


def circle_vs_aabb(circle: Circle, circle_pos: Vector3, 
                   aabb: AABB, aabb_pos: Vector3) -> Optional[CollisionResult]:
    """
    Detect collision between a circle and an AABB using Minkowski sum approach.
    
    The idea: expand the AABB by the circle radius, then check if the circle
    CENTER is inside the expanded bounds. The collision normal is determined
    by which face of the expanded AABB the center penetrates.
    """
    half_w = aabb.half_width
    half_h = aabb.half_height
    radius = circle.radius
    
    # Relative position of circle center to AABB center
    rel_x = circle_pos.x - aabb_pos.x
    rel_y = circle_pos.y - aabb_pos.y
    
    # Expanded half-dimensions (Minkowski sum)
    ex_w = half_w + radius
    ex_h = half_h + radius
    
    # Check if circle center is inside expanded AABB
    if abs(rel_x) > ex_w or abs(rel_y) > ex_h:
        return None  # No collision - center is outside expanded bounds
    
    # Calculate penetration on each axis
    pen_x = ex_w - abs(rel_x)
    pen_y = ex_h - abs(rel_y)
    
    # Check for corner case: if both penetrations are less than radius,
    # the circle might be at a corner and we need to check distance
    if pen_x < radius and pen_y < radius:
        # Corner collision - check distance to corner
        corner_x = aabb_pos.x + (half_w if rel_x > 0 else -half_w)
        corner_y = aabb_pos.y + (half_h if rel_y > 0 else -half_h)
        
        dx = circle_pos.x - corner_x
        dy = circle_pos.y - corner_y
        dist_sq = dx * dx + dy * dy
        
        if dist_sq >= radius * radius:
            return None  # No collision at corner
        
        dist = dist_sq ** 0.5
        if dist < Vector3._epsilon:
            normal = Vector3(1 if rel_x > 0 else -1, 1 if rel_y > 0 else -1).normalized()
        else:
            normal = Vector3(dx / dist, dy / dist)
        penetration = radius - dist
        contact = Vector3(corner_x, corner_y)
    else:
        # Face collision - use axis of minimum penetration
        if pen_x < pen_y:
            # X-axis collision
            normal = Vector3(1 if rel_x > 0 else -1, 0)
            penetration = pen_x
            contact = Vector3(
                aabb_pos.x + (half_w if rel_x > 0 else -half_w),
                circle_pos.y
            )
        else:
            # Y-axis collision  
            normal = Vector3(0, 1 if rel_y > 0 else -1)
            penetration = pen_y
            contact = Vector3(
                circle_pos.x,
                aabb_pos.y + (half_h if rel_y > 0 else -half_h)
            )
    
    return CollisionResult(
        colliding=True,
        normal=normal,
        penetration=penetration,
        contact_point=contact
    )


def aabb_vs_aabb(aabb_a: AABB, pos_a: Vector3, 
                 aabb_b: AABB, pos_b: Vector3) -> Optional[CollisionResult]:
    """Detect collision between two AABBs"""
    # Calculate overlap on each axis
    dx = pos_b.x - pos_a.x
    dy = pos_b.y - pos_a.y
    
    overlap_x = aabb_a.half_width + aabb_b.half_width - abs(dx)
    overlap_y = aabb_a.half_height + aabb_b.half_height - abs(dy)
    
    if overlap_x <= 0 or overlap_y <= 0:
        return None  # No collision
    
    # Use axis of minimum penetration
    if overlap_x < overlap_y:
        # Separate on X axis
        if dx > 0:
            normal = Vector3(1, 0)
        else:
            normal = Vector3(-1, 0)
        penetration = overlap_x
        contact = Vector3(pos_a.x + normal.x * aabb_a.half_width, 
                         (pos_a.y + pos_b.y) / 2)
    else:
        # Separate on Y axis
        if dy > 0:
            normal = Vector3(0, 1)
        else:
            normal = Vector3(0, -1)
        penetration = overlap_y
        contact = Vector3((pos_a.x + pos_b.x) / 2, 
                         pos_a.y + normal.y * aabb_a.half_height)
    
    return CollisionResult(
        colliding=True,
        normal=normal,
        penetration=penetration,
        contact_point=contact
    )


def circle_vs_polygon(circle: Circle, circle_pos: Vector3,
                      polygon: Polygon, poly_pos: Vector3) -> Optional[CollisionResult]:
    """Detect collision between a circle and a convex polygon using SAT"""
    vertices = polygon.vertices
    n = len(vertices)
    
    min_overlap = float('inf')
    min_normal = None
    
    # Test polygon edge normals
    for i in range(n):
        normal = polygon.get_edge_normal(i)
        
        # Project polygon onto axis
        poly_min, poly_max = _project_polygon(vertices, poly_pos, normal)
        
        # Project circle onto axis
        circle_proj = circle_pos.dot(normal)
        circle_min = circle_proj - circle.radius
        circle_max = circle_proj + circle.radius
        
        # Check for gap
        if poly_max < circle_min or circle_max < poly_min:
            return None  # Separating axis found
        
        # Calculate overlap
        overlap = min(poly_max - circle_min, circle_max - poly_min)
        if overlap < min_overlap:
            min_overlap = overlap
            min_normal = normal
    
    # Test axis from polygon to circle center (for circle vs vertex cases)
    closest_vertex = None
    closest_dist_sq = float('inf')
    
    for v in vertices:
        world_v = v + poly_pos
        dist_sq = (circle_pos - world_v).length_squared
        if dist_sq < closest_dist_sq:
            closest_dist_sq = dist_sq
            closest_vertex = world_v
    
    if closest_vertex:
        diff = circle_pos - closest_vertex
        dist = diff.length
        if dist > Vector3._epsilon:
            axis = diff / dist
            
            poly_min, poly_max = _project_polygon(vertices, poly_pos, axis)
            circle_proj = circle_pos.dot(axis)
            circle_min = circle_proj - circle.radius
            circle_max = circle_proj + circle.radius
            
            if poly_max < circle_min or circle_max < poly_min:
                return None
            
            overlap = min(poly_max - circle_min, circle_max - poly_min)
            if overlap < min_overlap:
                min_overlap = overlap
                min_normal = axis
    
    # Ensure normal points from polygon to circle
    if min_normal and (circle_pos - poly_pos).dot(min_normal) < 0:
        min_normal = min_normal * -1
    
    contact = circle_pos - min_normal * circle.radius
    
    return CollisionResult(
        colliding=True,
        normal=min_normal if min_normal else Vector3(1, 0),
        penetration=min_overlap,
        contact_point=contact
    )


def aabb_vs_polygon(aabb: AABB, aabb_pos: Vector3,
                    polygon: Polygon, poly_pos: Vector3) -> Optional[CollisionResult]:
    """Detect collision between an AABB and a polygon by treating AABB as polygon"""
    # Convert AABB to polygon vertices
    hw, hh = aabb.half_width, aabb.half_height
    aabb_verts = [
        Vector3(-hw, -hh),
        Vector3(hw, -hh),
        Vector3(hw, hh),
        Vector3(-hw, hh)
    ]
    
    return _sat_polygons(aabb_verts, aabb_pos, polygon.vertices, poly_pos)


def polygon_vs_polygon(poly_a: Polygon, pos_a: Vector3,
                       poly_b: Polygon, pos_b: Vector3) -> Optional[CollisionResult]:
    """Detect collision between two convex polygons using SAT"""
    return _sat_polygons(poly_a.vertices, pos_a, poly_b.vertices, pos_b)


def _project_polygon(vertices: list, offset: Vector3, axis: Vector3) -> Tuple[float, float]:
    """Project polygon vertices onto an axis, return (min, max)"""
    proj_min = float('inf')
    proj_max = float('-inf')
    
    for v in vertices:
        world_v = v + offset
        proj = world_v.dot(axis)
        proj_min = min(proj_min, proj)
        proj_max = max(proj_max, proj)
    
    return proj_min, proj_max


def _sat_polygons(verts_a: list, pos_a: Vector3, 
                  verts_b: list, pos_b: Vector3) -> Optional[CollisionResult]:
    """SAT collision detection between two convex polygons"""
    min_overlap = float('inf')
    min_normal = None
    
    # Test all edge normals from both polygons
    for verts, pos in [(verts_a, pos_a), (verts_b, pos_b)]:
        n = len(verts)
        for i in range(n):
            # Edge normal
            edge = verts[(i + 1) % n] - verts[i]
            normal = Vector3(-edge.y, edge.x).normalized()
            
            if normal.length < Vector3._epsilon:
                continue
            
            # Project both polygons
            min_a, max_a = _project_polygon(verts_a, pos_a, normal)
            min_b, max_b = _project_polygon(verts_b, pos_b, normal)
            
            # Check for gap
            if max_a < min_b or max_b < min_a:
                return None  # Separating axis found
            
            # Calculate overlap
            overlap = min(max_a - min_b, max_b - min_a)
            if overlap < min_overlap:
                min_overlap = overlap
                min_normal = normal
    
    # Ensure normal points from A to B
    if min_normal:
        direction = pos_b - pos_a
        if direction.dot(min_normal) < 0:
            min_normal = min_normal * -1
    
    # Approximate contact point (center between shapes)
    contact = (pos_a + pos_b) * 0.5
    
    return CollisionResult(
        colliding=True,
        normal=min_normal if min_normal else Vector3(1, 0),
        penetration=min_overlap,
        contact_point=contact
    )
