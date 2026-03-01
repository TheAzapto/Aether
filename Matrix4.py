"""
Matrix4.py - 4x4 Matrix operations for the Aether Physics Engine

Provides transformation matrices for 3D rendering:
perspective projection, orthographic projection, view (look-at),
translation, rotation, and scale.

Backed by numpy for performance and OpenGL compatibility.
"""

import numpy as np
import math
from Vector import Vector3


class Matrix4:
    """4x4 transformation matrix using column-major order (OpenGL convention)"""

    def __init__(self, data=None):
        """
        Create a Matrix4 from a 4x4 numpy array.
        If no data provided, creates an identity matrix.
        
        :param data: 4x4 numpy array (column-major for OpenGL)
        :type data: numpy.ndarray or None
        """
        if data is not None:
            self._data = np.array(data, dtype=np.float32).reshape(4, 4)
        else:
            self._data = np.eye(4, dtype=np.float32)

    @property
    def data(self) -> np.ndarray:
        return self._data

    # ── Factory Methods ──────────────────────────────────────────────

    @staticmethod
    def identity() -> 'Matrix4':
        """Create a 4x4 identity matrix"""
        return Matrix4()

    @staticmethod
    def perspective(fov_degrees: float, aspect: float,
                    near: float, far: float) -> 'Matrix4':
        """
        Create a perspective projection matrix.

        :param fov_degrees: Vertical field of view in degrees
        :param aspect: Aspect ratio (width / height)
        :param near: Near clipping plane distance
        :param far: Far clipping plane distance
        """
        fov_rad = math.radians(fov_degrees)
        f = 1.0 / math.tan(fov_rad / 2.0)

        m = np.zeros((4, 4), dtype=np.float32)
        m[0][0] = f / aspect
        m[1][1] = f
        m[2][2] = (far + near) / (near - far)
        m[2][3] = (2.0 * far * near) / (near - far)
        m[3][2] = -1.0
        return Matrix4(m)

    @staticmethod
    def orthographic(left: float, right: float, bottom: float,
                     top: float, near: float, far: float) -> 'Matrix4':
        """
        Create an orthographic projection matrix.

        :param left: Left clipping plane
        :param right: Right clipping plane
        :param bottom: Bottom clipping plane
        :param top: Top clipping plane
        :param near: Near clipping plane
        :param far: Far clipping plane
        """
        m = np.zeros((4, 4), dtype=np.float32)
        m[0][0] = 2.0 / (right - left)
        m[1][1] = 2.0 / (top - bottom)
        m[2][2] = -2.0 / (far - near)
        m[0][3] = -(right + left) / (right - left)
        m[1][3] = -(top + bottom) / (top - bottom)
        m[2][3] = -(far + near) / (far - near)
        m[3][3] = 1.0
        return Matrix4(m)

    @staticmethod
    def look_at(eye: Vector3, target: Vector3, up: Vector3) -> 'Matrix4':
        """
        Create a view matrix using eye position, target point, and up direction.

        :param eye: Camera position in world space
        :param target: Point the camera looks at
        :param up: Up direction vector
        """
        forward = (eye - target).normalized()
        right = up.cross(forward).normalized()
        new_up = forward.cross(right)

        m = np.eye(4, dtype=np.float32)
        m[0][0] = right.x
        m[0][1] = right.y
        m[0][2] = right.z
        m[0][3] = -right.dot(eye)
        m[1][0] = new_up.x
        m[1][1] = new_up.y
        m[1][2] = new_up.z
        m[1][3] = -new_up.dot(eye)
        m[2][0] = forward.x
        m[2][1] = forward.y
        m[2][2] = forward.z
        m[2][3] = -forward.dot(eye)
        return Matrix4(m)

    @staticmethod
    def translation(x: float, y: float, z: float) -> 'Matrix4':
        """Create a translation matrix"""
        m = np.eye(4, dtype=np.float32)
        m[0][3] = x
        m[1][3] = y
        m[2][3] = z
        return Matrix4(m)

    @staticmethod
    def scale(x: float, y: float, z: float) -> 'Matrix4':
        """Create a scale matrix"""
        m = np.zeros((4, 4), dtype=np.float32)
        m[0][0] = x
        m[1][1] = y
        m[2][2] = z
        m[3][3] = 1.0
        return Matrix4(m)

    @staticmethod
    def rotation_x(angle_degrees: float) -> 'Matrix4':
        """Create a rotation matrix around the X axis"""
        rad = math.radians(angle_degrees)
        c, s = math.cos(rad), math.sin(rad)
        m = np.eye(4, dtype=np.float32)
        m[1][1] = c
        m[1][2] = -s
        m[2][1] = s
        m[2][2] = c
        return Matrix4(m)

    @staticmethod
    def rotation_y(angle_degrees: float) -> 'Matrix4':
        """Create a rotation matrix around the Y axis"""
        rad = math.radians(angle_degrees)
        c, s = math.cos(rad), math.sin(rad)
        m = np.eye(4, dtype=np.float32)
        m[0][0] = c
        m[0][2] = s
        m[2][0] = -s
        m[2][2] = c
        return Matrix4(m)

    @staticmethod
    def rotation_z(angle_degrees: float) -> 'Matrix4':
        """Create a rotation matrix around the Z axis"""
        rad = math.radians(angle_degrees)
        c, s = math.cos(rad), math.sin(rad)
        m = np.eye(4, dtype=np.float32)
        m[0][0] = c
        m[0][1] = -s
        m[1][0] = s
        m[1][1] = c
        return Matrix4(m)

    # ── Operations ───────────────────────────────────────────────────

    def multiply(self, other: 'Matrix4') -> 'Matrix4':
        """Multiply this matrix by another (self * other)"""
        return Matrix4(self._data @ other._data)

    def __matmul__(self, other: 'Matrix4') -> 'Matrix4':
        """Support @ operator for matrix multiplication"""
        return self.multiply(other)

    def transform_point(self, point: Vector3) -> Vector3:
        """
        Transform a 3D point by this matrix (w=1 for points).
        Performs perspective divide if w != 1.
        """
        v = np.array([point.x, point.y, point.z, 1.0], dtype=np.float32)
        result = self._data @ v
        w = result[3]
        if abs(w) > 1e-6:
            return Vector3(result[0] / w, result[1] / w, result[2] / w)
        return Vector3(result[0], result[1], result[2])

    def transform_direction(self, direction: Vector3) -> Vector3:
        """
        Transform a direction vector (w=0, no translation applied).
        """
        v = np.array([direction.x, direction.y, direction.z, 0.0], dtype=np.float32)
        result = self._data @ v
        return Vector3(result[0], result[1], result[2])

    def to_gl(self) -> np.ndarray:
        """
        Return matrix as column-major flat array for glUniformMatrix4fv.
        OpenGL expects column-major order, so we transpose row-major data.
        """
        return np.ascontiguousarray(self._data.T, dtype=np.float32)

    def __repr__(self) -> str:
        return f"Matrix4(\n{self._data}\n)"
