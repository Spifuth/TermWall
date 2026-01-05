#!/usr/bin/env python3
"""
termwall — Terminal idle animation / screensaver
A Python screensaver that displays animations after idle time

Usage: termwall <command> [options]
Commands: run, watch, list-modes, validate-config
"""

import argparse
import curses
import math
import os
import random
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

VERSION = "2.0.0"
PROGRAM_NAME = "termwall"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "termwall" / "config"

# Default configuration
DEFAULTS = {
    "mode": "stars",
    "fps": 30,
    "idle_seconds": 300,
    "duration_seconds": 0,
    "color_theme": "green",
    "message": "",
}

AVAILABLE_MODES = ["stars", "pulse", "matrix", "rain"]

COLOR_THEMES = {
    "green": curses.COLOR_GREEN,
    "cyan": curses.COLOR_CYAN,
    "magenta": curses.COLOR_MAGENTA,
    "mono": curses.COLOR_WHITE,
    "red": curses.COLOR_RED,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
}


@dataclass
class Config:
    mode: str = DEFAULTS["mode"]
    fps: int = DEFAULTS["fps"]
    idle_seconds: int = DEFAULTS["idle_seconds"]
    duration_seconds: int = DEFAULTS["duration_seconds"]
    color_theme: str = DEFAULTS["color_theme"]
    message: str = DEFAULTS["message"]


def parse_config(config_path: Path) -> Config:
    """Parse configuration file."""
    config = Config()
    
    if not config_path.exists():
        return config
    
    with open(config_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Remove inline comments
            if "#" in line:
                line = line[:line.index("#")].strip()
            
            if "=" not in line:
                print(f"Warning: Invalid syntax at line {line_num}", file=sys.stderr)
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            
            if key == "mode":
                config.mode = value
            elif key == "fps":
                config.fps = int(value) if value.isdigit() else DEFAULTS["fps"]
            elif key == "idle_seconds":
                config.idle_seconds = int(value) if value.isdigit() else DEFAULTS["idle_seconds"]
            elif key == "duration_seconds":
                config.duration_seconds = int(value) if value.isdigit() else DEFAULTS["duration_seconds"]
            elif key == "color_theme":
                config.color_theme = value
            elif key == "message":
                config.message = value
    
    return config


def validate_config(config: Config) -> List[str]:
    """Validate configuration and return list of errors."""
    errors = []
    
    if config.mode not in AVAILABLE_MODES:
        errors.append(f"Invalid mode '{config.mode}'. Available: {', '.join(AVAILABLE_MODES)}")
    
    if not 1 <= config.fps <= 120:
        errors.append(f"Invalid fps '{config.fps}'. Must be 1-120")
    
    if config.idle_seconds < 0:
        errors.append(f"Invalid idle_seconds '{config.idle_seconds}'. Must be non-negative")
    
    if config.duration_seconds < 0:
        errors.append(f"Invalid duration_seconds '{config.duration_seconds}'. Must be non-negative")
    
    if config.color_theme not in COLOR_THEMES:
        errors.append(f"Invalid color_theme '{config.color_theme}'. Available: {', '.join(COLOR_THEMES.keys())}")
    
    return errors


# =============================================================================
# Animation: Stars
# =============================================================================

@dataclass
class Star:
    x: float
    y: int
    char: str
    speed: float
    brightness: int = 0


class StarsAnimation:
    STAR_CHARS = [".", "·", "+", "*", "✦", "✧", "★", "⋆"]
    
    def __init__(self, stdscr, config: Config):
        self.stdscr = stdscr
        self.config = config
        self.height, self.width = stdscr.getmaxyx()
        self.stars: List[Star] = []
        self._init_stars()
    
    def _init_stars(self):
        num_stars = (self.width * self.height) // 25
        num_stars = max(50, min(500, num_stars))
        
        self.stars = []
        for _ in range(num_stars):
            self.stars.append(Star(
                x=random.uniform(0, self.width - 1),
                y=random.randint(0, self.height - 1),
                char=random.choice(self.STAR_CHARS),
                speed=random.uniform(0.05, 0.4),
                brightness=random.randint(1, 3),
            ))
    
    def update(self):
        self.height, self.width = self.stdscr.getmaxyx()
        
        for star in self.stars:
            star.x -= star.speed
            
            if star.x < 0:
                star.x = self.width - 1
                star.y = random.randint(0, self.height - 1)
                star.brightness = random.randint(1, 3)
            
            # Random twinkle
            if random.random() < 0.02:
                star.brightness = random.randint(1, 3)
    
    def render(self):
        self.stdscr.erase()
        
        for star in self.stars:
            x, y = int(star.x), star.y
            if 0 <= x < self.width and 0 <= y < self.height - 1:
                try:
                    attr = curses.A_DIM if star.brightness == 1 else (
                        curses.A_NORMAL if star.brightness == 2 else curses.A_BOLD
                    )
                    self.stdscr.addch(y, x, star.char, curses.color_pair(1) | attr)
                except curses.error:
                    pass
        
        # Draw message
        if self.config.message:
            self._draw_message()
        
        self.stdscr.refresh()
    
    def _draw_message(self):
        msg = self.config.message
        y = self.height // 2
        x = (self.width - len(msg)) // 2
        if x > 0 and y < self.height - 1:
            try:
                self.stdscr.addstr(y, x, msg, curses.A_BOLD | curses.color_pair(2))
            except curses.error:
                pass


# =============================================================================
# Animation: Pulse
# =============================================================================

class PulseAnimation:
    """Text that pulses with color waves and breathing effect."""
    
    def __init__(self, stdscr, config: Config):
        self.stdscr = stdscr
        self.config = config
        self.height, self.width = stdscr.getmaxyx()
        
        self.text = config.message or "TERMWALL"
        self.frame = 0
        self.phase = 0.0
        
        # Decorative particles around text
        self.particles = []
        self._init_particles()
    
    def _init_particles(self):
        """Create floating particles around the text area."""
        self.particles = []
        center_y = self.height // 2
        center_x = self.width // 2
        
        for i in range(40):
            angle = random.uniform(0, 6.28)
            distance = random.uniform(3, min(self.width, self.height) // 3)
            self.particles.append({
                'base_x': center_x + distance * math.cos(angle),
                'base_y': center_y + distance * math.sin(angle) * 0.5,
                'phase': random.uniform(0, 6.28),
                'speed': random.uniform(0.02, 0.05),
                'amplitude': random.uniform(1, 3),
                'char': random.choice(['·', '•', '○', '◦', '∘', '⋅', '*', '+']),
            })
    
    def update(self):
        self.height, self.width = self.stdscr.getmaxyx()
        self.frame += 1
        self.phase += 0.05
        
        # Update particles
        for p in self.particles:
            p['phase'] += p['speed']
    
    def render(self):
        self.stdscr.erase()
        
        center_y = self.height // 2
        center_x = (self.width - len(self.text)) // 2
        
        # Draw floating particles
        for p in self.particles:
            x = int(p['base_x'] + math.sin(p['phase']) * p['amplitude'])
            y = int(p['base_y'] + math.cos(p['phase'] * 0.7) * p['amplitude'] * 0.5)
            
            if 0 <= x < self.width and 0 <= y < self.height - 1:
                try:
                    # Particles fade based on distance from center
                    dist = abs(x - self.width // 2) + abs(y - center_y)
                    if dist < 10:
                        attr = curses.A_BOLD
                    elif dist < 20:
                        attr = curses.A_NORMAL
                    else:
                        attr = curses.A_DIM
                    self.stdscr.addch(y, x, p['char'], curses.color_pair(1) | attr)
                except curses.error:
                    pass
        
        # Calculate breathing effect (smooth sine wave)
        breath = math.sin(self.phase) * 0.5 + 0.5  # 0 to 1
        
        # Draw main text with color wave effect
        if center_x > 0 and center_y < self.height - 1:
            for i, char in enumerate(self.text):
                # Each character has slightly offset phase for wave effect
                char_phase = self.phase + i * 0.3
                char_brightness = math.sin(char_phase) * 0.5 + 0.5
                
                # Choose color based on wave position
                colors = [1, 7, 6, 1, 5, 4]  # theme, cyan, magenta, theme, blue, yellow
                color_idx = int((char_phase / 0.5) % len(colors))
                
                try:
                    x = center_x + i
                    if 0 <= x < self.width:
                        if char_brightness > 0.7:
                            attr = curses.A_BOLD
                        elif char_brightness > 0.3:
                            attr = curses.A_NORMAL
                        else:
                            attr = curses.A_DIM
                        
                        self.stdscr.addch(center_y, x, char, 
                            curses.color_pair(colors[color_idx]) | attr)
                except curses.error:
                    pass
        
        # Draw decorative lines above and below
        line_char = '─'
        line_width = len(self.text) + 4
        line_x = center_x - 2
        
        if line_x > 0:
            # Animated line above
            for i in range(line_width):
                x = line_x + i
                if 0 <= x < self.width and center_y - 2 >= 0:
                    try:
                        wave = math.sin(self.phase * 2 + i * 0.5)
                        attr = curses.A_BOLD if wave > 0 else curses.A_DIM
                        self.stdscr.addch(center_y - 2, x, line_char,
                            curses.color_pair(1) | attr)
                    except curses.error:
                        pass
            
            # Animated line below
            for i in range(line_width):
                x = line_x + i
                if 0 <= x < self.width and center_y + 2 < self.height - 1:
                    try:
                        wave = math.sin(self.phase * 2 + i * 0.5 + 3.14)
                        attr = curses.A_BOLD if wave > 0 else curses.A_DIM
                        self.stdscr.addch(center_y + 2, x, line_char,
                            curses.color_pair(1) | attr)
                    except curses.error:
                        pass
        
        self.stdscr.refresh()


# =============================================================================
# Animation: Matrix
# =============================================================================

@dataclass
class MatrixDrop:
    x: int
    y: float
    speed: float
    length: int
    chars: List[str] = field(default_factory=list)


class MatrixAnimation:
    CHARS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    def __init__(self, stdscr, config: Config):
        self.stdscr = stdscr
        self.config = config
        self.height, self.width = stdscr.getmaxyx()
        self.drops: List[MatrixDrop] = []
        self._init_drops()
    
    def _init_drops(self):
        num_drops = self.width // 2
        num_drops = max(20, min(200, num_drops))
        
        self.drops = []
        for i in range(num_drops):
            x = i * 2
            if x < self.width:
                self.drops.append(self._new_drop(x, random_start=True))
    
    def _new_drop(self, x: int, random_start: bool = False) -> MatrixDrop:
        length = random.randint(8, 25)
        start_y = random.randint(-self.height, 0) if random_start else random.randint(-20, -1)
        
        return MatrixDrop(
            x=x,
            y=float(start_y),
            speed=random.uniform(0.15, 0.5),
            length=length,
            chars=[random.choice(self.CHARS) for _ in range(length)],
        )
    
    def update(self):
        self.height, self.width = self.stdscr.getmaxyx()
        
        for drop in self.drops:
            drop.y += drop.speed
            
            # Randomly change characters
            if random.random() < 0.1:
                idx = random.randint(0, len(drop.chars) - 1)
                drop.chars[idx] = random.choice(self.CHARS)
            
            # Reset if off screen
            if drop.y - drop.length > self.height:
                new_drop = self._new_drop(drop.x)
                drop.y = new_drop.y
                drop.speed = new_drop.speed
                drop.length = new_drop.length
                drop.chars = new_drop.chars
    
    def render(self):
        self.stdscr.erase()
        
        for drop in self.drops:
            head_y = int(drop.y)
            
            for i, char in enumerate(drop.chars):
                y = head_y - i
                
                if 0 <= y < self.height - 1 and 0 <= drop.x < self.width:
                    try:
                        if i == 0:
                            # Head - bright white
                            self.stdscr.addch(y, drop.x, char, 
                                curses.A_BOLD | curses.color_pair(2))
                        elif i < 3:
                            # Near head - bright green
                            self.stdscr.addch(y, drop.x, char,
                                curses.A_BOLD | curses.color_pair(1))
                        elif i < 8:
                            # Middle - normal green
                            self.stdscr.addch(y, drop.x, char,
                                curses.color_pair(1))
                        else:
                            # Tail - dim green
                            self.stdscr.addch(y, drop.x, char,
                                curses.A_DIM | curses.color_pair(1))
                    except curses.error:
                        pass
        
        # Draw message
        if self.config.message:
            msg = f" {self.config.message} "
            y = self.height // 2
            x = (self.width - len(msg)) // 2
            if x > 0 and y < self.height - 1:
                try:
                    self.stdscr.addstr(y, x, msg, curses.A_BOLD | curses.A_REVERSE)
                except curses.error:
                    pass
        
        self.stdscr.refresh()


# =============================================================================
# Animation: Rain
# =============================================================================

@dataclass 
class RainDrop:
    x: int
    y: float
    speed: float
    char: str


class RainAnimation:
    def __init__(self, stdscr, config: Config):
        self.stdscr = stdscr
        self.config = config
        self.height, self.width = stdscr.getmaxyx()
        self.drops: List[RainDrop] = []
        self._init_drops()
    
    def _init_drops(self):
        num_drops = self.width * self.height // 30
        num_drops = max(50, min(500, num_drops))
        
        self.drops = []
        for _ in range(num_drops):
            self.drops.append(RainDrop(
                x=random.randint(0, self.width - 1),
                y=random.uniform(-self.height, self.height),
                speed=random.uniform(0.15, 0.6),
                char=random.choice(["|", "│", "┃", "╿", "╽"]),
            ))
    
    def update(self):
        self.height, self.width = self.stdscr.getmaxyx()
        
        for drop in self.drops:
            drop.y += drop.speed
            
            if drop.y > self.height:
                drop.y = random.uniform(-5, 0)
                drop.x = random.randint(0, self.width - 1)
                drop.speed = random.uniform(0.15, 0.6)
    
    def render(self):
        self.stdscr.erase()
        
        for drop in self.drops:
            x, y = drop.x, int(drop.y)
            if 0 <= x < self.width and 0 <= y < self.height - 1:
                try:
                    attr = curses.A_BOLD if drop.speed > 1.5 else (
                        curses.A_DIM if drop.speed < 0.8 else curses.A_NORMAL
                    )
                    self.stdscr.addch(y, x, drop.char, curses.color_pair(1) | attr)
                except curses.error:
                    pass
        
        # Draw message
        if self.config.message:
            msg = self.config.message
            y = self.height // 2
            x = (self.width - len(msg)) // 2
            if x > 0 and y < self.height - 1:
                try:
                    self.stdscr.addstr(y, x, msg, curses.A_BOLD | curses.color_pair(2))
                except curses.error:
                    pass
        
        self.stdscr.refresh()


# =============================================================================
# Animation Controller
# =============================================================================

def init_colors(config: Config):
    """Initialize color pairs."""
    curses.start_color()
    curses.use_default_colors()
    
    theme_color = COLOR_THEMES.get(config.color_theme, curses.COLOR_GREEN)
    
    # Color pair 1: Theme color
    curses.init_pair(1, theme_color, -1)
    # Color pair 2: White (for highlights)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    # Color pairs 3-7: Various colors for bounce
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_BLUE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_CYAN, -1)


def get_animation(stdscr, config: Config):
    """Get animation instance based on mode."""
    animations = {
        "stars": StarsAnimation,
        "pulse": PulseAnimation,
        "matrix": MatrixAnimation,
        "rain": RainAnimation,
    }
    return animations[config.mode](stdscr, config)


def run_animation(stdscr, config: Config):
    """Main animation loop."""
    # Setup curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(0)
    init_colors(config)
    
    animation = get_animation(stdscr, config)
    
    frame_time = 1.0 / config.fps
    start_time = time.time()
    running = True
    
    while running:
        frame_start = time.time()
        
        # Check for keypress
        try:
            key = stdscr.getch()
            if key != -1:  # Any key pressed
                running = False
                continue
        except curses.error:
            pass
        
        # Check duration
        if config.duration_seconds > 0:
            elapsed = time.time() - start_time
            if elapsed >= config.duration_seconds:
                running = False
                continue
        
        # Update and render
        animation.update()
        animation.render()
        
        # Frame rate limiting
        frame_elapsed = time.time() - frame_start
        sleep_time = frame_time - frame_elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


def curses_main(stdscr, config: Config):
    """Curses wrapper main function."""
    try:
        run_animation(stdscr, config)
    except KeyboardInterrupt:
        pass


# =============================================================================
# CLI Commands
# =============================================================================

def cmd_run(args):
    """Run animation command."""
    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    config = parse_config(config_path)
    
    # Override with CLI args
    if args.mode:
        config.mode = args.mode
    if args.duration is not None:
        config.duration_seconds = args.duration
    if args.fps:
        config.fps = args.fps
    
    # Validate
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    
    # Check terminal
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Error: termwall requires an interactive terminal", file=sys.stderr)
        return 1
    
    # Run animation
    curses.wrapper(curses_main, config)
    return 0


def cmd_watch(args):
    """Watch for idle and launch animation."""
    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    config = parse_config(config_path)
    
    if args.idle:
        config.idle_seconds = args.idle
    
    print(f"Watching for idle time (threshold: {config.idle_seconds}s)")
    print("Press Ctrl+C to stop watching")
    
    # Simple idle detection using /dev/input or similar would go here
    # For now, just a placeholder
    try:
        while True:
            time.sleep(1)
            # TODO: Implement proper idle detection
    except KeyboardInterrupt:
        print("\nStopped watching")
    
    return 0


def cmd_list_modes(args):
    """List available animation modes."""
    print("Available animation modes:\n")
    descriptions = {
        "stars": "Scrolling starfield with twinkling effect",
        "pulse": "Breathing text with color waves and particles",
        "matrix": "Matrix-style falling characters",
        "rain": "Gentle rain animation",
    }
    for mode in AVAILABLE_MODES:
        desc = descriptions.get(mode, "")
        print(f"  {mode:10} - {desc}")


def cmd_validate_config(args):
    """Validate configuration file."""
    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    
    if not config_path.exists():
        print(f"Warning: Config file not found: {config_path}")
        print("Using default configuration")
        config = Config()
    else:
        print(f"Validating config: {config_path}")
        config = parse_config(config_path)
    
    errors = validate_config(config)
    
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    
    print("\nConfiguration is valid!\n")
    print("Current configuration:")
    print(f"  mode            = {config.mode}")
    print(f"  fps             = {config.fps}")
    print(f"  idle_seconds    = {config.idle_seconds}")
    print(f"  duration_seconds = {config.duration_seconds}")
    print(f"  color_theme     = {config.color_theme}")
    print(f"  message         = {config.message}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Terminal idle animation / screensaver"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM_NAME} {VERSION}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Launch animation immediately")
    run_parser.add_argument("-m", "--mode", choices=AVAILABLE_MODES, help="Animation mode")
    run_parser.add_argument("-c", "--config", help="Config file path")
    run_parser.add_argument("-d", "--duration", type=int, help="Duration in seconds (0 = infinite)")
    run_parser.add_argument("--fps", type=int, help="Frames per second")
    
    # watch command
    watch_parser = subparsers.add_parser("watch", help="Watch for idle time")
    watch_parser.add_argument("-i", "--idle", type=int, help="Idle threshold in seconds")
    watch_parser.add_argument("-c", "--config", help="Config file path")
    
    # list-modes command
    subparsers.add_parser("list-modes", help="List available animation modes")
    
    # validate-config command
    validate_parser = subparsers.add_parser("validate-config", help="Validate configuration file")
    validate_parser.add_argument("-c", "--config", help="Config file path")
    
    args = parser.parse_args()
    
    if args.command == "run":
        return cmd_run(args)
    elif args.command == "watch":
        return cmd_watch(args)
    elif args.command == "list-modes":
        return cmd_list_modes(args)
    elif args.command == "validate-config":
        return cmd_validate_config(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
