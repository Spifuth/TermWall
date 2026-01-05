# Documentation

This folder contains demos and documentation assets.

## Creating a Demo GIF

### Using asciinema + agg

```bash
# Install asciinema
pip install asciinema

# Install agg (asciinema gif generator)
# https://github.com/asciinema/agg

# Record a session
asciinema rec demo.cast

# In the recording, run:
# ./termwall run --mode stars --duration 10
# Press 'q' to stop recording

# Convert to GIF
agg demo.cast demo.gif --font-size 14 --cols 80 --rows 24
```

### Using termtosvg

```bash
# Install
pip install termtosvg

# Record and convert
termtosvg -g 80x24 demo.svg

# In the recording, run termwall, then exit
```

### Using ttygif

```bash
# Install ttyrec and ttygif
sudo apt install ttyrec
# Get ttygif from https://github.com/icholy/ttygif

# Record
ttyrec demo.rec

# Convert
ttygif demo.rec
```

## Demo Files

- `demo.gif` - Main demo for README (stars animation)
- `demo-matrix.gif` - Matrix mode demo
- `demo-bounce.gif` - Bounce mode demo
