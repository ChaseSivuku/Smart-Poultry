"""
Smart Chicken Farm Simulation (Core Simulation + Flask Sync)

This module simulates a smart chicken farm environment with live sensors and automation.
It visualizes the coop, chickens, and devices using Pygame,
and synchronizes sensor data + events to a Flask backend dashboard.
"""

import pygame
import random
import math
import requests

# --- Constants ---
WIDTH, HEIGHT = 800, 500
FPS = 30
CHICKEN_COUNT = 5
SERVER_URL = "http://127.0.0.1:5000/update-sensor"  # Flask backend endpoint

# --- Colors ---
WHITE = (255, 255, 255)
BLUE = (100, 149, 237)
GREEN = (34, 177, 76)
LIGHT_GREEN = (144, 238, 144)
RED = (200, 50, 50)
YELLOW = (255, 255, 100)
LIGHT_YELLOW = (255, 255, 180)
GRAY = (70, 70, 70)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
LIGHT_BLUE = (173, 216, 230)

# --- Radar System for Hotspot Detection ---
class RadarSystem:
    def __init__(self):
        self.hotspots = []
        self.scan_radius = 50  # Radar scan radius in pixels
        self.hotspot_threshold = 2  # Minimum chickens to form a hotspot (lowered for demo)
        
    def scan_hotspots(self, chickens):
        """Scan for chicken hotspots using radar simulation"""
        self.hotspots = []
        
        # Create a grid for hotspot detection
        grid_size = 15  # Smaller grid for better detection
        grid_width = WIDTH // grid_size
        grid_height = HEIGHT // grid_size
        chicken_counts = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Count chickens in each grid cell
        for chicken in chickens:
            grid_x = min(int(chicken.x // grid_size), grid_width - 1)
            grid_y = min(int(chicken.y // grid_size), grid_height - 1)
            chicken_counts[grid_y][grid_x] += 1
        
        # Add persistent demo hotspots for demonstration
        demo_hotspots = [
            {"x": 25, "y": 40, "intensity": 75, "name": "Feed Area"},
            {"x": 75, "y": 60, "intensity": 60, "name": "Water Area"},
            {"x": 50, "y": 30, "intensity": 45, "name": "Resting Zone"}
        ]
        self.hotspots.extend(demo_hotspots)
        
        # Identify hotspots (areas with multiple chickens)
        for y in range(grid_height):
            for x in range(grid_width):
                if chicken_counts[y][x] >= self.hotspot_threshold:
                    # Calculate hotspot center and intensity
                    center_x = (x * grid_size) + (grid_size // 2)
                    center_y = (y * grid_size) + (grid_size // 2)
                    
                    # Convert to percentage coordinates for frontend
                    x_percent = (center_x / WIDTH) * 100
                    y_percent = (center_y / HEIGHT) * 100
                    
                    # Calculate intensity based on chicken count and activity
                    intensity = min(100, chicken_counts[y][x] * 20 + random.uniform(0, 20))
                    
                    hotspot_name = f"Hotspot {len(self.hotspots) + 1}"
                    if x_percent < 30:
                        hotspot_name = "Feed Area"
                    elif x_percent > 70:
                        hotspot_name = "Water Area"
                    elif y_percent < 30:
                        hotspot_name = "Resting Zone"
                    else:
                        hotspot_name = "Activity Zone"
                    
                    self.hotspots.append({
                        "x": x_percent,
                        "y": y_percent,
                        "intensity": intensity,
                        "name": hotspot_name
                    })
        
        return self.hotspots

# --- Simulation State ---
class FarmState:
    def __init__(self):
        self.temperature = 26.0
        self.light = 320
        self.water_level = 85
        self.feed_level = 75
        self.pump = False
        self.fan = False
        self.light_on = False
        self.time = 0
        self.status_message = ""
        self.MAX_HISTORY = 60
        self.radar_system = RadarSystem()

        self.history = {k: [] for k in ["temperature", "light", "water_level", "feed_level"]}

    def update(self):
        """Simulate natural environmental changes and internal dynamics."""
        self.time += 1

        # --- Temperature variation ---
        ambient_drift = math.sin(self.time / 60) * 0.3 + random.uniform(-0.15, 0.25)
        if self.fan:
            self.temperature -= random.uniform(0.2, 0.4)
        else:
            self.temperature += ambient_drift

        # --- Light variation ---
        if self.light_on:
            self.light += random.uniform(3, 6)
        else:
            # simulate daytime pattern
            cycle = math.sin(self.time / 100) * 100
            self.light += cycle * 0.02 + random.uniform(-5, 5)

        # --- Water level variation ---
        evap_rate = 0.1 + (0.05 * max(0, (self.temperature - 25) / 10))
        if self.pump:
            self.water_level += random.uniform(0.01, 1.5)
        else:
            self.water_level -= evap_rate

        # --- Feed consumption ---
        consumption = random.uniform(0.01, 0.12)
        self.feed_level -= consumption

        # --- Clamp values ---
        self.temperature = max(15, min(40, self.temperature))
        self.light = max(0, min(600, self.light))
        self.water_level = max(0, min(100, self.water_level))
        self.feed_level = max(0, min(100, self.feed_level))

        # --- Record history for graph ---
        if self.time % 5 == 0:
            for k, v in {
                "temperature": self.temperature,
                "light": self.light,
                "water_level": self.water_level,
                "feed_level": self.feed_level,
            }.items():
                self.history[k].append(v)
                if len(self.history[k]) > self.MAX_HISTORY:
                    self.history[k].pop(0)

    def automation_agent(self):

        """Simple automation logic for light, fan, pump, and feed alerts."""
       

        self.status_message = ""
        events = []

        # --- Initialize one-time flags ---
        if not hasattr(self, "light_alert_sent"):
            self.light_alert_sent = False
            self.temp_alert_sent = False
            self.water_alert_sent = False
            self.feed_alert_sent = False

        # --- Light Control ---
        if self.light <= 350 and not self.light_on:
            self.light_on = True
            events.append(("Light", "Activated", "yellow"))
        elif self.light >= 550 and self.light_on:
            self.light_on = False
            events.append(("Light", "Deactivated", "yellow"))

        # --- Temperature Control ---
        if self.temperature >= 27 and not self.fan:
            self.fan = True
            if not self.temp_alert_sent:
                self.temp_alert_sent = True
                events.append(("Fan", "Activated", "red"))
        elif self.temperature <= 15 and self.fan:
            self.fan = False
            if self.temp_alert_sent:
                self.temp_alert_sent = False
                events.append(("Fan", "Deactivated", "green"))

        # --- Water Pump Control ---
        if self.water_level < 50 and not self.pump:
            self.pump = True
            if not self.water_alert_sent:
                self.water_alert_sent = True
                events.append(("Pump", "Activated", "blue"))
        elif self.water_level >= 90 and self.pump:
            self.pump = False
            if self.water_alert_sent:
                self.water_alert_sent = False
                events.append(("Pump", "Deactivated", "blue"))

        # --- Feed Alert ---
        if self.feed_level < 20 and not self.feed_alert_sent:
            self.feed_alert_sent = True
            events.append(("Feed", "Low Feed Alert", "red"))
        elif self.feed_level > 30 and self.feed_alert_sent:
            self.feed_alert_sent = False

        # --- Send first triggered event ---
        if events:
            event = events[0]
            try:
                requests.post(
                    "http://127.0.0.1:5000/activity-event",
                    json={"title": event[0], "detail": event[1], "color": event[2]},
                    timeout=1,
                )
                print("Activity Event Sent:", event)
            except Exception as e:
                print("Failed to send event:", e)

        # --- Always send device state to frontend ---
        try:
            state = {
                "fan": self.fan,
                "pump": self.pump,
                "light_on": self.light_on,
                "feed_alert": self.feed_alert_sent,
            }
            requests.post("http://127.0.0.1:5000/system-state", json=state, timeout=1)
            print("Sent system state:", state)
        except Exception as e:
            print("Failed to send system state:", e)

# --- Chicken Class ---
class Chicken:
    def __init__(self):
        self.x = random.randint(100, 700)
        self.y = random.randint(250, 400)
        self.direction = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.5, 1.5)
        self.step_timer = 0
        self.step_max = random.randint(20, 60)

    def move(self):
        self.step_timer += 1
        if self.step_timer >= self.step_max:
            self.direction = random.uniform(0, 2 * math.pi)
            self.speed = random.uniform(0.5, 2)
            self.step_timer = 0
            self.step_max = random.randint(20, 60)
        self.x += math.cos(self.direction) * self.speed
        self.y += math.sin(self.direction) * self.speed
        self.x = max(80, min(WIDTH - 80, self.x))
        self.y = max(220, min(HEIGHT - 80, self.y))
        if self.x <= 80 or self.x >= WIDTH - 80:
            self.direction = math.pi - self.direction
        if self.y <= 220 or self.y >= HEIGHT - 80:
            self.direction = -self.direction

    def draw(self, screen):
        body_color = YELLOW
        head_color = LIGHT_YELLOW
        pygame.draw.ellipse(screen, body_color, (int(self.x - 10), int(self.y - 5), 20, 15))
        head_x = int(self.x + 8 * math.cos(self.direction))
        head_y = int(self.y + 8 * math.sin(self.direction))
        pygame.draw.circle(screen, head_color, (head_x, head_y), 6)
        beak_x = head_x + int(6 * math.cos(self.direction))
        beak_y = head_y + int(6 * math.sin(self.direction))
        pygame.draw.polygon(screen, RED, [
            (beak_x, beak_y),
            (beak_x - 3 * math.sin(self.direction), beak_y + 3 * math.cos(self.direction)),
            (beak_x + 3 * math.sin(self.direction), beak_y - 3 * math.cos(self.direction)),
        ])

# --- Drawing Helpers ---
def draw_trend_graph(screen, values, x, y, width, height, color, max_val):
    if not values:
        return
    pygame.draw.rect(screen, (30, 30, 30), (x, y, width, height))
    pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height), 1)
    points = []
    for i, val in enumerate(values):
        px = x + (i / max(1, len(values) - 1)) * width
        py = y + height - (val / max_val) * height
        points.append((px, py))
    if len(points) > 1:
        pygame.draw.lines(screen, color, False, points, 2)

def draw_device(screen, pos, label, is_on, on_color, off_color, radius=25):
    x, y = pos
    color = on_color if is_on else off_color
    pygame.draw.circle(screen, color, (x, y), radius)
    pygame.draw.circle(screen, WHITE, (x, y), radius, 2)
    font = pygame.font.Font(None, 22)
    text = font.render(label, True, WHITE)
    screen.blit(text, (x - text.get_width() // 2, y + radius + 5))
    status = "ON" if is_on else "OFF"
    status_col = GREEN if is_on else GRAY
    text = font.render(status, True, status_col)
    screen.blit(text, (x - text.get_width() // 2, y - radius - 20))

# --- Main Simulation Loop ---
def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🐔 Smart Chicken Farm Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)

    state = FarmState()
    chickens = [Chicken() for _ in range(CHICKEN_COUNT)]

    floor_tiles = [(x, y) for x in range(0, WIDTH, 50) for y in range(200, HEIGHT, 50)]
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        # --- Update Environment + Automation ---
        state.update()
        state.automation_agent()

        # --- Scan for chicken hotspots using radar ---
        hotspots = state.radar_system.scan_hotspots(chickens)

        # --- Send live updates to Flask ---
        if state.time % 15 == 0:
            try:
                data = {
                    "temperature": round(state.temperature, 2),
                    "humidity": round(random.uniform(45, 75), 2),
                    "tankLevel": round(state.water_level, 1),
                    "feed": round(state.feed_level, 1),
                    "light": round(state.light, 2),
                }
                requests.post(SERVER_URL, json=data, timeout=1)
            except Exception:
                pass

        # --- Send hotspot data to Flask ---
        if state.time % 30 == 0:  # Send hotspot data every 30 frames (1 second)
            try:
                hotspot_data = {"hotspots": hotspots}
                requests.post("http://127.0.0.1:5000/hotspot-data", json=hotspot_data, timeout=1)
                print(f"Radar Hotspots Sent: {len(hotspots)} hotspots detected")
            except Exception as e:
                print(f"Failed to send hotspot data: {e}")

        # --- Draw Scene ---
        screen.fill((20, 20, 40))
        pygame.draw.rect(screen, BROWN, (0, 180, WIDTH, HEIGHT - 180))
        for tile in floor_tiles:
            pygame.draw.rect(screen, (130, 100, 60), (tile[0], tile[1], 50, 50))
            pygame.draw.rect(screen, (110, 80, 40), (tile[0], tile[1], 50, 50), 1)

        # Feed trough
        pygame.draw.rect(screen, GRAY, (50, 300, 150, 40), border_radius=5)
        feed_w = int((state.feed_level / 100) * 150)
        pygame.draw.rect(screen, LIGHT_GREEN, (50, 300, feed_w, 40), border_radius=5)
        pygame.draw.rect(screen, WHITE, (50, 300, 150, 40), 2, border_radius=5)
        screen.blit(small_font.render("Feed Trough", True, WHITE), (75, 350))

        # Devices
        draw_device(screen, (100, 120), "Light", state.light_on, YELLOW, (80, 80, 0))
        draw_device(screen, (700, 120), "Fan", state.fan, BLUE, (50, 50, 100), 30)

        # Fan animation
        if state.fan:
            for i in range(4):
                a = state.time * 0.25 + i * math.pi / 2
                x = 700 + int(20 * math.cos(a))
                y = 120 + int(20 * math.sin(a))
                pygame.draw.line(screen, LIGHT_BLUE, (700, 120), (x, y), 4)

        # Water Tank
        pygame.draw.rect(screen, (50, 50, 70), (350, 100, 60, 120), border_radius=10)
        water_h = int((state.water_level / 100) * 120)
        pygame.draw.rect(screen, BLUE, (350, 220 - water_h, 60, water_h), border_radius=10)
        pygame.draw.rect(screen, WHITE, (350, 100, 60, 120), 2, border_radius=10)
        screen.blit(small_font.render("Water Tank", True, WHITE), (335, 80))
        draw_device(screen, (440, 160), "Pump", state.pump, GREEN, (50, 100, 50), 15)

        # Chickens
        for ch in chickens:
            ch.move()
            ch.draw(screen)

        # Graphs
        draw_trend_graph(screen, state.history["temperature"], 500, 20, 160, 60, RED, 40)
        screen.blit(small_font.render(f"Temp: {state.temperature:.1f}°C", True, WHITE), (500, 85))
        draw_trend_graph(screen, state.history["light"], 500, 120, 160, 60, YELLOW, 600)
        screen.blit(small_font.render(f"Light: {state.light:.0f} lux", True, WHITE), (500, 185))

        # Control panel
        pygame.draw.rect(screen, (40, 40, 40), (20, 20, 200, 150), border_radius=10)
        pygame.draw.rect(screen, (80, 80, 80), (20, 20, 200, 150), 2, border_radius=10)
        screen.blit(font.render("CONTROL PANEL", True, WHITE), (35, 30))

        readings = [
            f"Temp: {state.temperature:.1f}°C",
            f"Light: {state.light:.0f} lux",
            f"Water: {state.water_level:.1f}%",
            f"Feed: {state.feed_level:.1f}%",
        ]
        for i, r in enumerate(readings):
            color = WHITE
            if i == 0 and state.temperature > 30: color = RED
            elif i == 2 and state.water_level < 30: color = RED
            elif i == 3 and state.feed_level < 30: color = RED
            screen.blit(font.render(r, True, color), (35, 60 + i * 25))

        # Status message
        if state.status_message:
            msg = font.render(state.status_message, True, YELLOW)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()
