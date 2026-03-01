from Vector import Vector3
from Primitives import Shape, Circle, AABB, ShapeType
from Collision import detect_collision

class RigidBody:
    def __init__(self, p:Vector3=Vector3(0,0), v:Vector3 = Vector3(0,0), m:float=1.0, shape:Shape=None):
        """
        Rigid Body class can be used to define an object's state. values of this class will update using Vector3 operations
    
        :param p: location coordinates of a Body object. Inital default is set to ( 0 , 0 )
        :type p: Vector3

        :param v: velocity of an object, this will generlly update with force, but an inital velocity can be set during instancing of object. Inital default is set to ( 0 , 0 )
        :type v: Vector3

        :param m: mass of an object. the stored value id inv_mass, to optimize for calculation efficency, this cannot be changed later. **Use 0 (or any number less than 0) to set mass for static objects.**
        :type m: float
        
        :param shape: collision shape for the body. Defaults to Circle(1.0) if not specified.
        :type shape: Shape
        """ 
        self._position:Vector3 = p
        self._velocity:Vector3 = v
        self._inv_mass:float = 1/m if m > 0 else 0
        self._force:Vector3 = Vector3(0,0)
        self._shape:Shape = shape if shape is not None else Circle(1.0)
        self._restitution:float = 0.5 # bounciness

    @property
    def position(self) -> Vector3:
        return self._position
        
    @position.setter
    def position(self, p:Vector3) -> None:
        self._position = p

    @property
    def velocity(self) -> Vector3:
        return self._velocity

    @velocity.setter
    def velocity(self, v:Vector3) -> None:
        self._velocity = v

    @property
    def shape(self) -> Shape:
        return self._shape

    @property
    def inv_mass(self) -> float:
        return self._inv_mass

    @property
    def force(self) -> Vector3:
        return self._force
    
    @property
    def restitution(self) -> float:
        return self._restitution
    
    def apply_force(self, f:Vector3) -> None:
        self._force += f

class ForceGenerator:
    def apply(self, body: RigidBody) -> None:
        raise NotImplementedError

class Gravity(ForceGenerator):
    def __init__(self, g:float = -9.8):
        self.g = Vector3(0, g)

    def apply(self, body: RigidBody) -> None:
        if body.inv_mass > 0:  # Only affects dynamic bodies
            body.apply_force(self.g * (1/body.inv_mass))  # F = mg

class Drag(ForceGenerator):
    def __init__(self, k: float = 0.1):
        self.k = k
    
    def apply(self, body: RigidBody) -> None:
        if body.inv_mass > 0:
            drag_force = body.velocity * -self.k
            body.apply_force(drag_force)

class Friction(ForceGenerator):
    """
    Realistic friction force generator.
    
    Friction opposes motion with a magnitude proportional to the normal force:
    F_friction = -μ * N * direction_of_motion
    
    Where:
    - μ (mu) is the coefficient of friction
    - N is the normal force (mass * gravity for objects on a surface)
    - direction_of_motion is the unit vector of velocity
    """
    def __init__(self, mu: float = 0.3, gravity: float = 9.81):
        """
        :param mu: Coefficient of friction (0 = no friction, 1 = high friction)
        :param gravity: Gravity magnitude for calculating normal force
        """
        self.mu = mu
        self.gravity = abs(gravity)

    def apply(self, body: RigidBody) -> None:
        if body.inv_mass <= 0:
            return  # Static bodies don't experience friction
        
        speed = body.velocity.length
        if speed < Vector3._epsilon:
            return  # No friction if not moving
        
        # Calculate normal force (N = mg for horizontal surface)
        mass = 1.0 / body.inv_mass
        normal_force = mass * self.gravity
        
        # Friction magnitude: F = μ * N
        friction_magnitude = self.mu * normal_force
        
        # Friction direction: opposite to velocity
        velocity_direction = body.velocity.normalized()
        
        # Clamp friction to not exceed current momentum (prevents jitter)
        max_friction = mass * speed / 0.016  # Approximate based on typical delta
        friction_magnitude = min(friction_magnitude, max_friction)
        
        # Apply friction force opposite to motion
        friction_force = velocity_direction * -friction_magnitude
        body.apply_force(friction_force)

class World:
    # Fixed internal timestep for collision accuracy (prevents tunneling)
    _INTERNAL_DELTA = 0.002  # 2ms internal step
    
    def __init__(self, delta:float=1e-2):
        self._bodies:list[RigidBody] = []
        self._delta:float = delta
        self._force_generators:list[ForceGenerator] = []
        self._accumulator:float = 0.0  # Time accumulator for sub-stepping

    def add_force(self, force:ForceGenerator | list[ForceGenerator]) -> None:
        if isinstance(force, list):
            self._force_generators.extend(force)
        else:
            self._force_generators.append(force)

    def remove_force(self, force:ForceGenerator) -> None:
        self._force_generators.remove(force)

    @property
    def bodies(self) -> list[RigidBody]:
        return self._bodies

    def add(self, body:RigidBody) -> None:
        self._bodies.append(body)
    
    def step(self) -> None:
        """Update physics using fixed timestep sub-stepping for accuracy"""
        # Add frame delta to accumulator
        self._accumulator += self._delta
        
        # Run sub-steps at fixed internal delta
        while self._accumulator >= World._INTERNAL_DELTA:
            self._internal_step(World._INTERNAL_DELTA)
            self._accumulator -= World._INTERNAL_DELTA
    
    def _internal_step(self, dt: float) -> None:
        """Single physics step with given delta time"""
        for body in self._bodies:

            if body.inv_mass <= 0:
                continue

            for generator in self._force_generators:
                generator.apply(body)

            body.velocity += body.force * body.inv_mass * dt
            body.position += body.velocity * dt

            # Simple boundary collision (floor)
            if body.position.y <= 0 and body.velocity.y < -Vector3._epsilon:
                body.position = Vector3(body.position.x, 0, body.position.z)
                body.velocity = Vector3(body.velocity.x, -body.velocity.y * body.restitution, body.velocity.z)

            # Simple boundary collision (left wall)
            if body.position.x <= 0 and body.velocity.x < -Vector3._epsilon:
                body.position = Vector3(0, body.position.y, body.position.z)
                body.velocity = Vector3(-body.velocity.x * body.restitution, body.velocity.y, body.velocity.z)

            # Simple boundary collision (right wall)
            if body.position.x >= 500 and body.velocity.x > Vector3._epsilon:
                body.position = Vector3(500, body.position.y, body.position.z)
                body.velocity = Vector3(-body.velocity.x * body.restitution, body.velocity.y, body.velocity.z)

            # Simple boundary collision (ceiling)
            if body.position.y >= 500 and body.velocity.y > Vector3._epsilon:
                body.position = Vector3(body.position.x, 500, body.position.z)
                body.velocity = Vector3(body.velocity.x, -body.velocity.y * body.restitution, body.velocity.z)

            # Simple boundary collision (back wall, z <= 0)
            if body.position.z <= -250 and body.velocity.z < -Vector3._epsilon:
                body.position = Vector3(body.position.x, body.position.y, -250)
                body.velocity = Vector3(body.velocity.x, body.velocity.y, -body.velocity.z * body.restitution)

            # Simple boundary collision (front wall, z >= 250)
            if body.position.z >= 250 and body.velocity.z > Vector3._epsilon:
                body.position = Vector3(body.position.x, body.position.y, 250)
                body.velocity = Vector3(body.velocity.x, body.velocity.y, -body.velocity.z * body.restitution)

            # Reset force for the next step
            body._force = Vector3(0, 0, 0)

        # Detect and resolve collisions between bodies
        self._resolve_collisions()

    def _resolve_collisions(self) -> None:
        """Detect and resolve collisions between all bodies"""
        for i in range(len(self._bodies)):
            for j in range(i + 1, len(self._bodies)):
                body_a = self._bodies[i]
                body_b = self._bodies[j]

                # Use shape-specific collision detection
                result = detect_collision(
                    body_a.shape, body_a.position,
                    body_b.shape, body_b.position
                )

                if result is None or not result.colliding:
                    continue

                # DEBUG: Print collision info
                print(f"COLLISION: A.pos={body_a.position}, B.pos={body_b.position}")
                print(f"  normal={result.normal}, pen={result.penetration:.2f}")

                normal = result.normal
                penetration = result.penetration
                total_inv_mass = body_a.inv_mass + body_b.inv_mass

                if total_inv_mass > 0:
                    # Separate the bodies based on their mass ratio
                    correction = normal * penetration
                    body_a.position = body_a.position - correction * (body_a.inv_mass / total_inv_mass)
                    body_b.position = body_b.position + correction * (body_b.inv_mass / total_inv_mass)

                    # Reflect velocities along collision normal
                    restitution = min(body_a.restitution, body_b.restitution)
                    
                    # For body_a: reflect velocity component along normal
                    if body_a.inv_mass > 0:
                        vel_a_normal = body_a.velocity.dot(normal)
                        if vel_a_normal > 0:  # Moving toward body_b
                            body_a.velocity = body_a.velocity - normal * vel_a_normal * (1 + restitution)
                    
                    # For body_b: reflect velocity component along normal
                    if body_b.inv_mass > 0:
                        vel_b_normal = body_b.velocity.dot(normal)
                        if vel_b_normal < 0:  # Moving toward body_a
                            body_b.velocity = body_b.velocity - normal * vel_b_normal * (1 + restitution)
