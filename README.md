# termwall 🌟

> Terminal idle animation / screensaver in pure Bash

[![ShellCheck](https://github.com/Spifuth/TermWall/workflows/ShellCheck/badge.svg)](https://github.com/Spifuth/TermWall/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**termwall** is a screensaver for your terminal. After a period of inactivity, it takes over the screen with a beautiful full-screen animation. Press any key to instantly return to your terminal, exactly as you left it.


## ✨ Features

- **🎬 Multiple animations** - Stars, bouncing text, Matrix rain
- **⏱️ Idle detection** - Auto-launch after configurable idle time
- **🎨 Color themes** - Green, cyan, magenta, monochrome
- **⚡ Instant exit** - Any keypress stops the animation immediately
- **🔧 Configurable** - Simple config file with sensible defaults
- **🛡️ Safe** - Always restores your terminal, even on crash
- **📦 Zero dependencies** - Pure Bash + standard POSIX tools

## 📋 Requirements

- Bash 4.0+
- Standard POSIX utilities: `tput`, `stty`, `sleep`, `awk`
- A terminal emulator supporting ANSI escape sequences
- Linux or WSL

## 🚀 Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/Spifuth/TermWall.git
cd termwall

# Make executable and install
chmod +x termwall
sudo cp termwall /usr/local/bin/

# Copy example config
mkdir -p ~/.config/termwall
cp config.example ~/.config/termwall/config
```

### Manual Install

1. Download the `termwall` script
2. Make it executable: `chmod +x termwall`
3. Place it somewhere in your `$PATH`
4. (Optional) Copy `config.example` to `~/.config/termwall/config`

## 📖 Usage

### Run animation immediately

```bash
# Use default settings
termwall run

# Specify animation mode
termwall run --mode matrix

# Run for specific duration
termwall run --mode bounce --duration 30
```

### Watch for idle time

```bash
# Start idle watcher (uses config file settings)
termwall watch

# Custom idle threshold (60 seconds)
termwall watch --idle 60
```

### Other commands

```bash
# List available animation modes
termwall list-modes

# Validate your configuration
termwall validate-config

# Show help
termwall help

# Show version
termwall version
```

## ⚙️ Configuration

Configuration file location: `~/.config/termwall/config`

```bash
# Animation mode: stars, bounce, matrix
mode = stars

# Frames per second (1-60)
fps = 15

# Color theme: green, cyan, magenta, mono
color_theme = green

# Custom message to display
message = "Hello, World!"

# Seconds of inactivity before screensaver activates
idle_seconds = 300

# Duration of animation in seconds (0 = infinite)
duration_seconds = 0
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `mode` | `stars` | Animation mode (`stars`, `bounce`, `matrix`) |
| `fps` | `15` | Frames per second (1-60) |
| `color_theme` | `green` | Color palette (`green`, `cyan`, `magenta`, `mono`) |
| `message` | *(empty)* | Optional text to display |
| `idle_seconds` | `300` | Idle time before auto-start (watch mode) |
| `duration_seconds` | `0` | Animation duration (0 = infinite) |

## 🎨 Animation Modes

### Stars ⭐

A peaceful starfield that scrolls across the screen with twinkling effects.

```bash
termwall run --mode stars
```

### Bounce 📺

Classic DVD screensaver style - text bounces around the screen, changing colors on each bounce.

```bash
termwall run --mode bounce
```

### Matrix 💻

The iconic falling characters from The Matrix.

```bash
termwall run --mode matrix
```

## 🔧 CLI Reference

```
termwall — Terminal idle animation / screensaver

Usage: termwall <command> [options]

Commands:
  run              Launch animation immediately
  watch            Watch for idle time and auto-launch
  list-modes       List available animation modes
  validate-config  Validate configuration file
  version          Show version
  help             Show this help message

Run Options:
  -m, --mode MODE      Animation mode (stars, bounce, matrix)
  -c, --config PATH    Config file path
  -d, --duration SECS  Duration in seconds (0 = infinite)

Watch Options:
  -i, --idle SECS      Idle threshold in seconds
  -c, --config PATH    Config file path
```

## 🤔 How It Works

termwall uses the **alternate screen buffer** - a feature supported by most modern terminal emulators. This is the same mechanism used by programs like `vim`, `less`, and `htop`.

When termwall starts:
1. Saves your current terminal state
2. Switches to the alternate screen buffer
3. Hides the cursor
4. Runs the animation

When you press any key (or the duration expires):
1. Restores the cursor
2. Switches back to the main screen buffer
3. Restores terminal settings

Your original terminal content is preserved exactly as it was.

## 🐛 Troubleshooting

### Terminal not restored properly

If your terminal gets stuck (e.g., after a crash), run:
```bash
reset
# or
stty sane
```

### Animation is choppy

Try reducing the FPS in your config:
```bash
fps = 10
```

### Idle detection not working

The idle watcher works best with:
- `xprintidle` (for X11 sessions)
- Terminal-based idle detection as fallback

Install xprintidle for better idle detection:
```bash
# Debian/Ubuntu
sudo apt install xprintidle

# Arch
sudo pacman -S xprintidle
```

## 🧪 Running Tests

```bash
# Validate configuration
./termwall validate-config

# Smoke test (runs for 2 seconds)
./termwall run --duration 2
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Ensure ShellCheck passes (`shellcheck termwall`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by classic screensavers and the nostalgia of simpler times
- Thanks to the Bash community for excellent documentation
- Terminal escape sequence reference: [XTerm Control Sequences](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)

---

Made with ❤️ and Bash