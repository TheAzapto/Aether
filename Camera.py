"""
Camera.py - Fixed camera system for the Aether Physics Engine

Provides a camera with a fixed position, look-at target, and perspective projection.
Generates the View and Projection matrices consumed by the renderer.
"""

from Vector import Vector3
from Matrix4 import Matrix4


class Camera:
    """
    Fixed-position 3D camera.

    The camera sits at a given position, looks at a target point,
    and produces view + perspective projection matrices.
    """

    def __init__(self,
                 position: Vector3 = None,
                 target: Vector3 = None,
                 up: Vector3 = None,
                 fov: float = 60.0,
                 aspect: float = 16.0 / 9.0,
                 near: float = 0.1,
                 far: float = 1000.0):
        """
        :param position: Eye position in world space
        :param target: Point the camera looks at
        :param up: World up direction
        :param fov: Vertical field of view in degrees
        :param aspect: Viewport aspect ratio (width / height)
        :param near: Near clipping plane
        :param far: Far clipping plane
        """
        self._position = position if position is not None else Vector3(250, 250, 500)
        self._target = target if target is not None else Vector3(250, 250, 0)
        self._up = up if up is not None else Vector3(0, 1, 0)
        self._fov = fov
        self._aspect = aspect
        self._near = near
        self._far = far

        # Cache matrices (recomputed only when dirty)
        self._view_dirty = True
        self._proj_dirty = True
        self._view_matrix = None
        self._proj_matrix = None

    # ── Properties ───────────────────────────────────────────────────

    @property
    def position(self) -> Vector3:
        return self._position

    @property
    def target(self) -> Vector3:
        return self._target

    @property
    def up(self) -> Vector3:
        return self._up

    @property
    def fov(self) -> float:
        return self._fov

    @property
    def aspect(self) -> float:
        return self._aspect

    @property
    def near(self) -> float:
        return self._near

    @property
    def far(self) -> float:
        return self._far

    # ── Matrix Getters ───────────────────────────────────────────────

    def get_view_matrix(self) -> Matrix4:
        """Returns the view (look-at) matrix"""
        if self._view_dirty or self._view_matrix is None:
            self._view_matrix = Matrix4.look_at(self._position, self._target, self._up)
            self._view_dirty = False
        return self._view_matrix

    def get_projection_matrix(self) -> Matrix4:
        """Returns the perspective projection matrix"""
        if self._proj_dirty or self._proj_matrix is None:
            self._proj_matrix = Matrix4.perspective(
                self._fov, self._aspect, self._near, self._far
            )
            self._proj_dirty = False
        return self._proj_matrix

    def get_vp_matrix(self) -> Matrix4:
        """Returns the combined View-Projection matrix (P * V)"""
        return self.get_projection_matrix() @ self.get_view_matrix()

    def __repr__(self) -> str:
        return (f"Camera(pos={self._position}, target={self._target}, "
                f"fov={self._fov}, aspect={self._aspect:.2f})")
