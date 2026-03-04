/* ═══════════════════════════════════════════════════════════
   Aether Physics Engine — Showcase Website Scripts
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initHeroParticles();
    initPhysicsDemo();
    initScrollReveal();
    initCodeTabs();
    initStatCounters();
});

/* ══════════════════════════════════════════════════════════
   NAVBAR
   ══════════════════════════════════════════════════════════ */
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    const hamburger = document.querySelector('.nav-hamburger');
    const navLinks = document.querySelector('.nav-links');

    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 60);
    });

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            const spans = hamburger.querySelectorAll('span');
            if (navLinks.classList.contains('open')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            }
        });
    }

    // Smooth scroll nav links
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(a.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (navLinks) navLinks.classList.remove('open');
            }
        });
    });
}

/* ══════════════════════════════════════════════════════════
   HERO PARTICLE CANVAS
   ══════════════════════════════════════════════════════════ */
function initHeroParticles() {
    const canvas = document.getElementById('hero-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let particles = [];
    const PARTICLE_COUNT = 80;
    const CONNECT_DIST = 140;
    let mouse = { x: -1000, y: -1000 };

    function resize() {
        canvas.width = canvas.offsetWidth * devicePixelRatio;
        canvas.height = canvas.offsetHeight * devicePixelRatio;
        ctx.scale(devicePixelRatio, devicePixelRatio);
    }

    function createParticles() {
        particles = [];
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                r: Math.random() * 2 + 0.5,
                alpha: Math.random() * 0.5 + 0.2
            });
        }
    }

    function draw() {
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        ctx.clearRect(0, 0, w, h);

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < CONNECT_DIST) {
                    const alpha = (1 - dist / CONNECT_DIST) * 0.12;
                    ctx.strokeStyle = `rgba(0, 212, 255, ${alpha})`;
                    ctx.lineWidth = 0.6;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw & update particles
        for (const p of particles) {
            // Mouse repulsion
            const mdx = p.x - mouse.x;
            const mdy = p.y - mouse.y;
            const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
            if (mDist < 120 && mDist > 0) {
                const force = (120 - mDist) / 120 * 0.8;
                p.vx += (mdx / mDist) * force;
                p.vy += (mdy / mDist) * force;
            }

            p.x += p.vx;
            p.y += p.vy;
            p.vx *= 0.99;
            p.vy *= 0.99;

            // Wrap
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 212, 255, ${p.alpha})`;
            ctx.fill();
        }

        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', () => {
        resize();
        createParticles();
    });

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
    });

    canvas.addEventListener('mouseleave', () => {
        mouse.x = -1000;
        mouse.y = -1000;
    });

    resize();
    createParticles();
    draw();
}

/* ══════════════════════════════════════════════════════════
   INTERACTIVE PHYSICS DEMO
   ══════════════════════════════════════════════════════════ */
function initPhysicsDemo() {
    const canvas = document.getElementById('demo-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const W = 900;
    const H = 450;
    canvas.width = W;
    canvas.height = H;

    const GRAVITY = 400;
    const RESTITUTION = 0.65;
    const DRAG = 0.999;
    const COLORS = [
        '#00d4ff', '#7b5cff', '#ff3c8e', '#3d7eff',
        '#28c840', '#ffbd2e', '#e5c07b', '#61afef'
    ];

    let bodies = [];
    let running = true;
    let lastTime = performance.now();

    // Body info DOM
    const bodyCountEl = document.getElementById('demo-body-count');
    const fpsEl = document.getElementById('demo-fps');
    let frameCount = 0;
    let fpsTimer = 0;
    let currentFps = 60;

    class PhysicsBody {
        constructor(x, y, radius, vx = 0, vy = 0, isStatic = false) {
            this.x = x;
            this.y = y;
            this.radius = radius;
            this.vx = vx;
            this.vy = vy;
            this.isStatic = isStatic;
            this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
            this.trail = [];
            this.mass = isStatic ? 0 : radius * radius;
        }
    }

    function spawnInitial() {
        bodies = [];
        // Spawn some random circles
        for (let i = 0; i < 20; i++) {
            const r = 6 + Math.random() * 14;
            const x = r + Math.random() * (W - 2 * r);
            const y = r + Math.random() * (H * 0.5);
            const vx = (Math.random() - 0.5) * 150;
            const vy = (Math.random() - 0.5) * 80;
            bodies.push(new PhysicsBody(x, y, r, vx, vy));
        }
        // Static platform
        bodies.push(new PhysicsBody(W / 2, H - 15, 0, 0, 0, true));
    }

    function step(dt) {
        if (!running) return;
        dt = Math.min(dt, 0.033); // cap delta

        for (const b of bodies) {
            if (b.isStatic) continue;

            // Gravity
            b.vy += GRAVITY * dt;

            // Drag
            b.vx *= DRAG;
            b.vy *= DRAG;

            // Integrate
            b.x += b.vx * dt;
            b.y += b.vy * dt;

            // Trail
            b.trail.push({ x: b.x, y: b.y });
            if (b.trail.length > 8) b.trail.shift();

            // Boundary collisions
            if (b.y + b.radius > H) {
                b.y = H - b.radius;
                b.vy = -b.vy * RESTITUTION;
            }
            if (b.y - b.radius < 0) {
                b.y = b.radius;
                b.vy = -b.vy * RESTITUTION;
            }
            if (b.x + b.radius > W) {
                b.x = W - b.radius;
                b.vx = -b.vx * RESTITUTION;
            }
            if (b.x - b.radius < 0) {
                b.x = b.radius;
                b.vx = -b.vx * RESTITUTION;
            }
        }

        // Circle vs Circle collisions
        for (let i = 0; i < bodies.length; i++) {
            for (let j = i + 1; j < bodies.length; j++) {
                const a = bodies[i];
                const b = bodies[j];
                if (a.isStatic && b.isStatic) continue;

                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const minDist = a.radius + b.radius;

                if (dist < minDist && dist > 0.001) {
                    const nx = dx / dist;
                    const ny = dy / dist;
                    const overlap = minDist - dist;

                    // Separate
                    const totalMass = a.mass + b.mass;
                    if (totalMass > 0) {
                        const ratioA = a.isStatic ? 0 : (b.isStatic ? 1 : b.mass / totalMass);
                        const ratioB = b.isStatic ? 0 : (a.isStatic ? 1 : a.mass / totalMass);
                        a.x -= nx * overlap * ratioA;
                        a.y -= ny * overlap * ratioA;
                        b.x += nx * overlap * ratioB;
                        b.y += ny * overlap * ratioB;
                    }

                    // Velocity resolution
                    const dvx = a.vx - b.vx;
                    const dvy = a.vy - b.vy;
                    const dvDotN = dvx * nx + dvy * ny;

                    if (dvDotN > 0) {
                        const restitution = RESTITUTION;
                        const impulse = -(1 + restitution) * dvDotN / (
                            (a.isStatic ? 0 : 1 / a.mass) + (b.isStatic ? 0 : 1 / b.mass)
                        );

                        if (!a.isStatic) {
                            a.vx += impulse / a.mass * nx;
                            a.vy += impulse / a.mass * ny;
                        }
                        if (!b.isStatic) {
                            b.vx -= impulse / b.mass * nx;
                            b.vy -= impulse / b.mass * ny;
                        }
                    }
                }
            }
        }
    }

    function render() {
        ctx.clearRect(0, 0, W, H);

        // Draw grid
        ctx.strokeStyle = 'rgba(100, 180, 255, 0.03)';
        ctx.lineWidth = 1;
        for (let x = 0; x <= W; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, H);
            ctx.stroke();
        }
        for (let y = 0; y <= H; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(W, y);
            ctx.stroke();
        }

        // Draw bodies
        for (const b of bodies) {
            if (b.isStatic) continue;

            // Trail
            for (let i = 0; i < b.trail.length; i++) {
                const t = b.trail[i];
                const alpha = (i / b.trail.length) * 0.15;
                ctx.beginPath();
                ctx.arc(t.x, t.y, b.radius * 0.6, 0, Math.PI * 2);
                ctx.fillStyle = b.color.replace(')', `, ${alpha})`).replace('rgb', 'rgba').replace('#', '');
                // Use hex to rgba
                const r = parseInt(b.color.slice(1, 3), 16);
                const g = parseInt(b.color.slice(3, 5), 16);
                const bl = parseInt(b.color.slice(5, 7), 16);
                ctx.fillStyle = `rgba(${r}, ${g}, ${bl}, ${alpha})`;
                ctx.fill();
            }

            // Glow
            const grd = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.radius * 2.5);
            grd.addColorStop(0, b.color + '18');
            grd.addColorStop(1, 'transparent');
            ctx.fillStyle = grd;
            ctx.fillRect(b.x - b.radius * 3, b.y - b.radius * 3, b.radius * 6, b.radius * 6);

            // Body
            ctx.beginPath();
            ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
            ctx.fillStyle = b.color;
            ctx.fill();

            // Inner highlight
            ctx.beginPath();
            ctx.arc(b.x - b.radius * 0.25, b.y - b.radius * 0.25, b.radius * 0.4, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,255,255,0.15)';
            ctx.fill();
        }
    }

    function loop(now) {
        const dt = (now - lastTime) / 1000;
        lastTime = now;

        // FPS counter
        frameCount++;
        fpsTimer += dt;
        if (fpsTimer >= 1) {
            currentFps = frameCount;
            frameCount = 0;
            fpsTimer = 0;
            if (fpsEl) fpsEl.textContent = currentFps;
        }

        step(dt);
        render();

        if (bodyCountEl) bodyCountEl.textContent = bodies.filter(b => !b.isStatic).length;

        requestAnimationFrame(loop);
    }

    // Click to add body
    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = W / rect.width;
        const scaleY = H / rect.height;
        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;
        const r = 6 + Math.random() * 14;
        const vx = (Math.random() - 0.5) * 200;
        const vy = -100 - Math.random() * 150;
        bodies.push(new PhysicsBody(x, y, r, vx, vy));

        // Cap total bodies so performance stays good
        while (bodies.filter(b => !b.isStatic).length > 80) {
            const idx = bodies.findIndex(b => !b.isStatic);
            if (idx >= 0) bodies.splice(idx, 1);
        }
    });

    // Controls
    const resetBtn = document.getElementById('demo-reset');
    const pauseBtn = document.getElementById('demo-pause');
    const gravityBtn = document.getElementById('demo-gravity');

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            spawnInitial();
        });
    }

    if (pauseBtn) {
        pauseBtn.addEventListener('click', () => {
            running = !running;
            pauseBtn.textContent = running ? '⏸ Pause' : '▶ Play';
            pauseBtn.classList.toggle('active', !running);
        });
    }

    let gravityFlipped = false;
    if (gravityBtn) {
        gravityBtn.addEventListener('click', () => {
            gravityFlipped = !gravityFlipped;
            // We modify the gravity constant reference — but since GRAVITY is const,
            // we'll use a closure trick
            gravityBtn.classList.toggle('active', gravityFlipped);
            gravityBtn.textContent = gravityFlipped ? '⬆ Gravity' : '⬇ Gravity';
        });
    }

    // Override step to use flipped gravity
    const originalStep = step;
    const wrappedStep = function (dt) {
        if (!running) return;
        dt = Math.min(dt, 0.033);

        const g = gravityFlipped ? -GRAVITY : GRAVITY;

        for (const b of bodies) {
            if (b.isStatic) continue;
            b.vy += g * dt;
            b.vx *= DRAG;
            b.vy *= DRAG;
            b.x += b.vx * dt;
            b.y += b.vy * dt;

            b.trail.push({ x: b.x, y: b.y });
            if (b.trail.length > 8) b.trail.shift();

            if (b.y + b.radius > H) {
                b.y = H - b.radius;
                b.vy = -b.vy * RESTITUTION;
            }
            if (b.y - b.radius < 0) {
                b.y = b.radius;
                b.vy = -b.vy * RESTITUTION;
            }
            if (b.x + b.radius > W) {
                b.x = W - b.radius;
                b.vx = -b.vx * RESTITUTION;
            }
            if (b.x - b.radius < 0) {
                b.x = b.radius;
                b.vx = -b.vx * RESTITUTION;
            }
        }

        for (let i = 0; i < bodies.length; i++) {
            for (let j = i + 1; j < bodies.length; j++) {
                const a = bodies[i];
                const bBody = bodies[j];
                if (a.isStatic && bBody.isStatic) continue;

                const dx = bBody.x - a.x;
                const dy = bBody.y - a.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const minDist = a.radius + bBody.radius;

                if (dist < minDist && dist > 0.001) {
                    const nx = dx / dist;
                    const ny = dy / dist;
                    const overlap = minDist - dist;

                    const totalMass = a.mass + bBody.mass;
                    if (totalMass > 0) {
                        const ratioA = a.isStatic ? 0 : (bBody.isStatic ? 1 : bBody.mass / totalMass);
                        const ratioB = bBody.isStatic ? 0 : (a.isStatic ? 1 : a.mass / totalMass);
                        a.x -= nx * overlap * ratioA;
                        a.y -= ny * overlap * ratioA;
                        bBody.x += nx * overlap * ratioB;
                        bBody.y += ny * overlap * ratioB;
                    }

                    const dvx = a.vx - bBody.vx;
                    const dvy = a.vy - bBody.vy;
                    const dvDotN = dvx * nx + dvy * ny;

                    if (dvDotN > 0) {
                        const restitution = RESTITUTION;
                        const impulse = -(1 + restitution) * dvDotN / (
                            (a.isStatic ? 0 : 1 / a.mass) + (bBody.isStatic ? 0 : 1 / bBody.mass)
                        );

                        if (!a.isStatic) {
                            a.vx += impulse / a.mass * nx;
                            a.vy += impulse / a.mass * ny;
                        }
                        if (!bBody.isStatic) {
                            bBody.vx -= impulse / bBody.mass * nx;
                            bBody.vy -= impulse / bBody.mass * ny;
                        }
                    }
                }
            }
        }
    };

    // Replace step
    const mainLoop = function (now) {
        const dt = (now - lastTime) / 1000;
        lastTime = now;

        frameCount++;
        fpsTimer += dt;
        if (fpsTimer >= 1) {
            currentFps = frameCount;
            frameCount = 0;
            fpsTimer = 0;
            if (fpsEl) fpsEl.textContent = currentFps;
        }

        wrappedStep(dt);
        render();

        if (bodyCountEl) bodyCountEl.textContent = bodies.filter(b => !b.isStatic).length;

        requestAnimationFrame(mainLoop);
    };

    spawnInitial();
    requestAnimationFrame(mainLoop);
}

/* ══════════════════════════════════════════════════════════
   SCROLL REVEAL (Intersection Observer)
   ══════════════════════════════════════════════════════════ */
function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    reveals.forEach(el => observer.observe(el));
}

/* ══════════════════════════════════════════════════════════
   CODE TABS
   ══════════════════════════════════════════════════════════ */
function initCodeTabs() {
    const tabs = document.querySelectorAll('.code-tab');
    const panels = document.querySelectorAll('.code-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.panel);
            if (target) target.classList.add('active');
        });
    });
}

/* ══════════════════════════════════════════════════════════
   STAT COUNTERS (Animated)
   ══════════════════════════════════════════════════════════ */
function initStatCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const finalVal = parseInt(el.getAttribute('data-count'), 10);
                animateCounter(el, 0, finalVal, 1500);
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(el => observer.observe(el));
}

function animateCounter(el, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();

    function tick(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(start + range * eased);
        el.textContent = value;

        if (progress < 1) {
            requestAnimationFrame(tick);
        }
    }

    requestAnimationFrame(tick);
}
