"""
Window.py - Modern OpenGL 3.3+ renderer for the Aether Physics Engine

Uses shaders and Vertex Buffer Objects (VBOs) so all vertex processing
runs on the GPU.  The legacy glBegin/glEnd/glVertex2f pipeline is gone.
"""

import glfw
from OpenGL.GL import *
from OpenGL.GL import shaders as gl_shaders
import numpy as np
import math
import ctypes
from typing import List, Tuple, TYPE_CHECKING
from Primitives import ShapeType, Circle, AABB, Polygon, Line
from Camera import Camera

if TYPE_CHECKING:
    from main import RigidBody


# ─── GLSL Shaders ────────────────────────────────────────────────────────────

VERTEX_SHADER_SRC = """
#version 330 core

layout(location = 0) in vec3 a_position;

uniform mat4 u_mvp;

void main() {
    gl_Position = u_mvp * vec4(a_position, 1.0);
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core

uniform vec3 u_color;
out vec4 frag_color;

void main() {
    frag_color = vec4(u_color, 1.0);
}
"""


# ─── Shader helpers ──────────────────────────────────────────────────────────

def _compile_shader(source: str, shader_type) -> int:
    """Compile a GLSL shader, raise on error"""
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        info = glGetShaderInfoLog(shader).decode()
        glDeleteShader(shader)
        raise RuntimeError(f"Shader compilation failed:\n{info}")
    return shader


def _link_program(vert: int, frag: int) -> int:
    """Link vertex + fragment shaders into a program"""
    program = glCreateProgram()
    glAttachShader(program, vert)
    glAttachShader(program, frag)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        info = glGetProgramInfoLog(program).decode()
        glDeleteProgram(program)
        raise RuntimeError(f"Shader link failed:\n{info}")
    # shaders can be deleted once linked
    glDeleteShader(vert)
    glDeleteShader(frag)
    return program


# ─── Renderer ────────────────────────────────────────────────────────────────

class Renderer:
    """GPU-accelerated renderer using modern OpenGL 3.3+ core profile"""

    COLORS: List[Tuple[float, float, float]] = [
        (0.4, 0.7, 1.0),   # Light blue
        (1.0, 0.5, 0.3),   # Orange
        (0.5, 1.0, 0.5),   # Light green
        (1.0, 0.8, 0.2),   # Yellow
    ]

    def __init__(self):
        self.bg_color = (0.1, 0.1, 0.15, 1.0)
        self._program = None
        self._vao = None
        self._vbo = None
        self._loc_mvp = -1
        self._loc_color = -1
        self._camera: Camera = None

        # Pre-built unit circle vertices (reused for every circle draw)
        self._circle_segments = 32
        self._circle_verts = self._build_circle_verts(self._circle_segments)

    # ── Initialisation (called after GL context exists) ──────────────

    def init_gl(self) -> None:
        """Compile shaders, create VAO/VBO — call ONCE after context is made current"""
        vert = _compile_shader(VERTEX_SHADER_SRC, GL_VERTEX_SHADER)
        frag = _compile_shader(FRAGMENT_SHADER_SRC, GL_FRAGMENT_SHADER)
        self._program = _link_program(vert, frag)

        self._loc_mvp = glGetUniformLocation(self._program, "u_mvp")
        self._loc_color = glGetUniformLocation(self._program, "u_color")

        # Create a single VAO + dynamic VBO (we upload new verts each draw call)
        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)

        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        # position attribute — location 0, 3 floats
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glBindVertexArray(0)

        glEnable(GL_DEPTH_TEST)

    def set_camera(self, camera: Camera) -> None:
        self._camera = camera

    # ── Frame lifecycle ──────────────────────────────────────────────

    def clear(self) -> None:
        glClearColor(*self.bg_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # ── Low-level draw ────────────────────────────────────────────────

    def _upload_and_draw(self, vertices: np.ndarray, mode: int) -> None:
        """Upload vertex data to VBO and issue a draw call"""
        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
        glDrawArrays(mode, 0, len(vertices) // 3)
        glBindVertexArray(0)

    def _set_mvp(self, model_x: float, model_y: float, model_z: float) -> None:
        """Compute and upload the MVP matrix for an object at (x, y, z)"""
        from Matrix4 import Matrix4
        model = Matrix4.translation(model_x, model_y, model_z)
        vp = self._camera.get_vp_matrix() if self._camera else Matrix4.identity()
        mvp = vp @ model
        glUniformMatrix4fv(self._loc_mvp, 1, GL_FALSE, mvp.to_gl())

    def _set_color(self, r: float, g: float, b: float) -> None:
        glUniform3f(self._loc_color, r, g, b)

    # ── Shape drawing ─────────────────────────────────────────────────

    @staticmethod
    def _build_circle_verts(segments: int) -> np.ndarray:
        """Build a unit triangle-fan circle centred at origin (z=0)"""
        verts = [0.0, 0.0, 0.0]  # center
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            verts.extend([math.cos(angle), math.sin(angle), 0.0])
        return np.array(verts, dtype=np.float32)

    def draw_circle(self, x: float, y: float, z: float, radius: float) -> None:
        from Matrix4 import Matrix4
        model = Matrix4.translation(x, y, z) @ Matrix4.scale(radius, radius, radius)
        vp = self._camera.get_vp_matrix() if self._camera else Matrix4.identity()
        mvp = vp @ model
        glUniformMatrix4fv(self._loc_mvp, 1, GL_FALSE, mvp.to_gl())
        self._upload_and_draw(self._circle_verts, GL_TRIANGLE_FAN)

    def draw_rect(self, x: float, y: float, z: float,
                  half_w: float, half_h: float) -> None:
        verts = np.array([
            -half_w, -half_h, 0.0,
             half_w, -half_h, 0.0,
             half_w,  half_h, 0.0,
            -half_w, -half_h, 0.0,
             half_w,  half_h, 0.0,
            -half_w,  half_h, 0.0,
        ], dtype=np.float32)
        self._set_mvp(x, y, z)
        self._upload_and_draw(verts, GL_TRIANGLES)

    def draw_polygon(self, x: float, y: float, z: float, vertices: list) -> None:
        # Triangle fan from first vertex
        if len(vertices) < 3:
            return
        verts = []
        v0 = vertices[0]
        for i in range(1, len(vertices) - 1):
            v1 = vertices[i]
            v2 = vertices[i + 1]
            verts.extend([v0.x, v0.y, v0.z,
                          v1.x, v1.y, v1.z,
                          v2.x, v2.y, v2.z])
        data = np.array(verts, dtype=np.float32)
        self._set_mvp(x, y, z)
        self._upload_and_draw(data, GL_TRIANGLES)

    def draw_line(self, x: float, y: float, z: float,
                  start, end, thickness: float = 2.0) -> None:
        verts = np.array([
            start.x, start.y, start.z,
            end.x,   end.y,   end.z,
        ], dtype=np.float32)
        self._set_mvp(x, y, z)
        glLineWidth(thickness)
        self._upload_and_draw(verts, GL_LINES)
        glLineWidth(1.0)

    # ── High-level body rendering ─────────────────────────────────────

    def render_body(self, body: "RigidBody",
                    color: Tuple[float, float, float]) -> None:
        glUseProgram(self._program)
        self._set_color(*color)

        shape = body.shape
        x, y, z = body.position.x, body.position.y, body.position.z

        if shape is None:
            self.draw_circle(x, y, z, 1.0)
        elif shape.type == ShapeType.CIRCLE:
            self.draw_circle(x, y, z, shape.radius)
        elif shape.type == ShapeType.AABB:
            self.draw_rect(x, y, z, shape.half_width, shape.half_height)
        elif shape.type == ShapeType.POLYGON:
            self.draw_polygon(x, y, z, shape.vertices)
        elif shape.type == ShapeType.LINE:
            self.draw_line(x, y, z, shape.start, shape.end)

    def render_bodies(self, bodies: List["RigidBody"]) -> None:
        for idx, body in enumerate(bodies):
            color = self.COLORS[idx % len(self.COLORS)]
            self.render_body(body, color)


# ─── Window ──────────────────────────────────────────────────────────────────

class Window:
    """Manages GLFW window with OpenGL 3.3 core-profile context"""

    def __init__(self, width: int = 800, height: int = 600,
                 title: str = "Aether Physics Engine"):
        self.width = width
        self.height = height
        self.title = title
        self._window = None
        self.renderer = Renderer()

    def create(self) -> bool:
        """Initialise GLFW, request OpenGL 3.3 core, and create the window"""
        if not glfw.init():
            raise Exception("GLFW initialisation failed")

        # Request OpenGL 3.3 core profile for shader support
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

        self._window = glfw.create_window(self.width, self.height,
                                           self.title, None, None)
        if not self._window:
            glfw.terminate()
            raise Exception("Window creation failed")

        glfw.make_context_current(self._window)

        # Now that we have a GL context, compile shaders and set up GPU state
        self.renderer.init_gl()
        return True

    def should_close(self) -> bool:
        return glfw.window_should_close(self._window)

    def poll_events(self) -> None:
        glfw.poll_events()

    def swap_buffers(self) -> None:
        glfw.swap_buffers(self._window)

    def begin_frame(self) -> None:
        """Start a new frame — clear colour + depth buffers"""
        self.renderer.clear()

    def end_frame(self) -> None:
        """End the frame — swap buffers"""
        self.swap_buffers()

    def render(self, bodies: List["RigidBody"]) -> None:
        self.renderer.render_bodies(bodies)

    def destroy(self) -> None:
        glfw.terminate()

    @property
    def handle(self):
        return self._window