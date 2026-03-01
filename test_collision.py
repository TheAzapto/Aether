"""
Simple test to debug collision detection
"""
from Vector import Vector3
from Primitives import Circle, AABB
from main import RigidBody, World, Gravity, Drag, Friction
from Window import Window

# World now uses internal sub-stepping for accurate collision
world = World(delta=0.016)

# Create window
window = Window(1280, 720, "Collision Debug Test")
window.create()

# Create just 2 bodies for testing
# One circle that will fall onto a static rectangle
test_circle = RigidBody(
    p=Vector3(250, 200),  # Start above the rectangle
    v=Vector3(0, 0),
    m=1.0,
    shape=Circle(10)  # Larger circle for visibility
)

# Static rectangle platform
static_rect = RigidBody(
    p=Vector3(250, 100),
    v=Vector3(0, 0),
    m=0,  # Static
    shape=AABB(50, 10)  # 100x20 rectangle
)

world.add(test_circle)
world.add(static_rect)

# Add only gravity
gravity = Gravity(-50)  # Slower gravity for debugging
world.add_force(gravity)

print("=== STARTING DEBUG TEST ===")
print(f"Circle: pos={test_circle.position}, radius={test_circle.shape.radius}")
print(f"AABB: pos={static_rect.position}, half_w={static_rect.shape.half_width}, half_h={static_rect.shape.half_height}")
print(f"AABB bounds: x=[{static_rect.position.x - 50}, {static_rect.position.x + 50}], y=[{static_rect.position.y - 10}, {static_rect.position.y + 10}]")
print()

frame_count = 0
max_frames = 300  # Run for 300 frames then stop

# Event loop
while not window.should_close() and frame_count < max_frames:
    window.poll_events()
    
    # Step the physics simulation
    world.step()
    
    # Render the scene
    window.begin_frame()
    window.render(world.bodies)
    window.end_frame()
    
    frame_count += 1
    
    # Print circle position every 30 frames
    if frame_count % 30 == 0:
        print(f"Frame {frame_count}: Circle pos={test_circle.position}, vel={test_circle.velocity}")

print("=== TEST COMPLETE ===")
window.destroy()
