# crt-scope

A Matplotlib theme and rendering shim that makes line plots look like vintage CRT oscilloscope traces.

## Features

- Dark gray oscilloscope-style screen and graticule
- Three built-in phosphor channels:
  - CH1: aqua P31-style green
  - CH2: amber CRT phosphor
  - CH3: P11-style blue phosphor
- Glow, bloom, and hot-core trace rendering
- Works with normal `plt.plot(...)` and `ax.plot(...)` after installation
- Consistent default trace width across channels

## Install locally

```bash
pip install matplotlib
```

Then place `crt_scope.py` and `crt_scope.mplstyle` somewhere on your Python path.

## Basic usage

```python
import numpy as np
import matplotlib.pyplot as plt
import crt_scope

crt_scope.install()

x = np.linspace(0, 10, 2000)
plt.plot(x, np.sin(x), label="CH1")
plt.plot(x, np.cos(x), label="CH2")
plt.plot(x, np.sin(2*x), label="CH3")
plt.legend()
plt.show()
```

## Force a specific phosphor

```python
plt.plot(x, y, channel=1)
plt.plot(x, y, channel=2)
plt.plot(x, y, channel=3)

plt.plot(x, y, color="ch1")
plt.plot(x, y, color="ch2")
plt.plot(x, y, color="ch3")
```

## Auto-install on import

By default, importing the module does **not** auto-install unless the environment variable is set.

```bash
export CRT_SCOPE_AUTO_INSTALL=1
```

Then:

```python
import crt_scope
```

That will apply the style and patch `Axes.plot` immediately on import.

## Production recommendation

For libraries and shared production code, prefer explicit installation:

```python
import crt_scope
crt_scope.install()
```

This avoids surprising global side effects during import.

Use auto-install only for notebooks, demos, internal tooling, or applications where you control the full plotting environment.

## Package for GitHub / PyPI

Recommended layout:

```text
crt-scope/
  pyproject.toml
  README.md
  src/
    crt_scope.py
    crt_scope.mplstyle
```

Then publish from the repository root with standard Python packaging tools.
