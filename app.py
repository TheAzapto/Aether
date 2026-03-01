from Vector import Vector3
from Primitives import Circle, AABB
from main import RigidBody, World, Gravity, Drag, Friction
from Window import Window
from Camera import Camera
import random

world = World(delta=0.016)  # ~60 FPS delta time

# Create window
window = Window(1280, 720, "Aether Physics Engine")
window.create()

# Set up fixed camera looking at the centre of the world
camera = Camera(
    position=Vector3(250, 250, 500),  # eye position
    target=Vector3(250, 250, 0),      # look-at point
    up=Vector3(0, 1, 0),
    fov=60.0,
    aspect=1280.0 / 720.0
)
window.renderer.set_camera(camera)

# Create rigid bodies with circle shapes
actives = [
    RigidBody(
        p=Vector3(random.randint(-100, 100), 200 + random.randint(-100, 100), random.randint(-100, 100)),
        v=Vector3(random.randint(-50, 50), random.randint(-50, 50), random.randint(-30, 30)),
        shape=Circle(1)
    ) for _ in range(50)
]

# Create a static rectangle body
static_rect = RigidBody(p=Vector3(250, 100, 0), v=Vector3(0, 0, 0), m=0, shape=AABB(50, 10))

for body in actives:
    world.add(body)
world.add(static_rect)

# Add forces
gravity = Gravity(-9.81)  # Scaled for visual effect
drag = Drag(0.05)
friction = Friction(mu=0.2, gravity=9.81)  # Coefficient of friction and gravity magnitude
world.add_force([gravity, drag, friction])

# Event loop
while not window.should_close():
    window.poll_events()

    # Step the physics simulation
    world.step()

    # Render the scene
    window.begin_frame()
    window.render(world.bodies)
    window.end_frame()

window.destroy()