from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_hex, to_rgb
from matplotlib.lines import Line2D

STYLE_PATH = Path(__file__).with_name('crt_scope.mplstyle')
DEFAULT_TRACE_WIDTH = 2.0
CHANNEL_SEQUENCE = (1, 2, 3)
AUTO_INSTALL_ENV_VAR = 'CRT_SCOPE_AUTO_INSTALL'


@dataclass(frozen=True)
class TraceStyle:
    glow_color: str
    core_color: str
    hot_color: str
    bloom_profile: tuple[tuple[float, float], ...] = (
        (16.0, 0.018),
        (10.0, 0.035),
        (6.0, 0.070),
        (3.6, 0.135),
        (1.8, 0.230),
    )
    core_alpha: float = 0.96
    hot_alpha: float = 0.88


DEFAULT_TRACE_STYLES: dict[int, TraceStyle] = {
    1: TraceStyle(
        glow_color='#39E0C3',
        core_color='#7CFFE9',
        hot_color='#F1FFF9',
    ),
    2: TraceStyle(
        glow_color='#FF9C38',
        core_color='#FFC15E',
        hot_color='#FFF1C8',
    ),
    3: TraceStyle(
        glow_color='#2E7BFF',
        core_color='#79ADFF',
        hot_color='#EAF5FF',
    ),
}

_PATCHED = False
_ORIGINAL_AXES_PLOT = Axes.plot

_COLOR_ALIASES = {
    'ch1': 1,
    'crt1': 1,
    'p31': 1,
    'scope1': 1,
    'ch2': 2,
    'crt2': 2,
    'amber_crt': 2,
    'scope2': 2,
    'ch3': 3,
    'crt3': 3,
    'p11': 3,
    'scope3': 3,
}


def _mix(color_a: str, color_b: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    a = to_rgb(color_a)
    b = to_rgb(color_b)
    mixed = tuple((1.0 - amount) * x + amount * y for x, y in zip(a, b))
    return to_hex(mixed)



def _style_from_color(color: str) -> TraceStyle:
    return TraceStyle(
        glow_color=to_hex(to_rgb(color)),
        core_color=_mix(color, '#FFFFFF', 0.22),
        hot_color=_mix(color, '#FFFFFF', 0.82),
    )



def channel_style(channel: int) -> TraceStyle:
    if channel not in DEFAULT_TRACE_STYLES:
        raise KeyError(f'Unknown CRT channel {channel}.')
    return DEFAULT_TRACE_STYLES[channel]



def channel_color(channel: int) -> str:
    return channel_style(channel).core_color



def register_channel_style(
    channel: int,
    *,
    glow_color: str,
    core_color: str | None = None,
    hot_color: str | None = None,
    bloom_profile: tuple[tuple[float, float], ...] | None = None,
    core_alpha: float | None = None,
    hot_alpha: float | None = None,
) -> None:
    style = _style_from_color(glow_color)
    if core_color is not None:
        style = replace(style, core_color=core_color)
    if hot_color is not None:
        style = replace(style, hot_color=hot_color)
    if bloom_profile is not None:
        style = replace(style, bloom_profile=bloom_profile)
    if core_alpha is not None:
        style = replace(style, core_alpha=core_alpha)
    if hot_alpha is not None:
        style = replace(style, hot_alpha=hot_alpha)
    DEFAULT_TRACE_STYLES[channel] = style



def _resolve_requested_channel(kwargs: dict[str, Any]) -> int | None:
    requested = kwargs.pop('channel', None)
    if requested is None:
        requested = kwargs.pop('crt_channel', None)

    color = kwargs.get('color')
    if isinstance(color, str):
        alias = _COLOR_ALIASES.get(color.lower())
        if alias is not None:
            kwargs.pop('color', None)
            requested = alias if requested is None else requested

    if requested is None:
        return None
    try:
        return int(requested)
    except (TypeError, ValueError) as exc:
        raise ValueError('channel must be an integer such as 1, 2, or 3.') from exc



def _next_auto_channel(ax: Axes) -> int:
    next_index = getattr(ax, '_crt_scope_next_channel', 0)
    channel = CHANNEL_SEQUENCE[next_index % len(CHANNEL_SEQUENCE)]
    ax._crt_scope_next_channel = next_index + 1
    return channel



def _clone_line_data(source: Line2D, ax: Axes, *, color: str, linewidth: float, alpha: float,
                     zorder: float, marker: str = 'None') -> Line2D:
    line = Line2D(
        source.get_xdata(orig=False),
        source.get_ydata(orig=False),
        linestyle=source.get_linestyle(),
        drawstyle=source.get_drawstyle(),
        dash_capstyle=source.get_dash_capstyle(),
        dash_joinstyle=source.get_dash_joinstyle(),
        solid_capstyle='round',
        solid_joinstyle='round',
        antialiased=True,
        marker=marker,
        markersize=0.0 if marker == 'None' else source.get_markersize(),
        color=color,
        linewidth=linewidth,
        alpha=alpha,
        zorder=zorder,
        label='_nolegend_',
    )
    line.set_transform(source.get_transform())
    line.set_clip_path(source.get_clip_path())
    line.set_clip_box(source.get_clip_box())
    ax.add_line(line)
    return line



def _apply_crt_rendering(ax: Axes, line: Line2D, *, style: TraceStyle, linewidth: float,
                         glow_strength: float = 1.18, hot_core: bool = True) -> None:
    xdata = line.get_xdata(orig=False)
    ydata = line.get_ydata(orig=False)
    if len(xdata) == 0:
        return

    original_marker = line.get_marker()
    if original_marker is None:
        original_marker = 'None'

    line.set_color(style.core_color)
    line.set_linewidth(linewidth)
    line.set_alpha(style.core_alpha)
    line.set_solid_capstyle('round')
    line.set_solid_joinstyle('round')
    line.set_antialiased(True)
    line.set_zorder(max(line.get_zorder(), 3.0))

    if glow_strength > 0:
        for extra_lw, alpha in style.bloom_profile:
            _clone_line_data(
                line,
                ax,
                color=style.glow_color,
                linewidth=linewidth + (extra_lw * glow_strength),
                alpha=alpha,
                zorder=max(1.0, line.get_zorder() - 1.0),
                marker='None',
            )

    if hot_core:
        _clone_line_data(
            line,
            ax,
            color=style.hot_color,
            linewidth=max(0.8, linewidth * 0.34),
            alpha=style.hot_alpha,
            zorder=line.get_zorder() + 1.0,
            marker='None',
        )

    if original_marker not in ('None', None, '', ' '):
        line.set_marker(original_marker)



def install(*, patch_plot: bool = True) -> None:
    """Apply the CRT theme globally. After install(), normal plt.plot/ax.plot work."""
    plt.style.use(str(STYLE_PATH))
    if patch_plot:
        patch_plot_calls()



def patch_plot_calls() -> None:
    global _PATCHED
    if _PATCHED:
        return

    def crt_plot(self: Axes, *args: Any, **kwargs: Any):
        requested_channel = _resolve_requested_channel(kwargs)
        glow_strength = float(kwargs.pop('glow_strength', 1.18))
        hot_core = bool(kwargs.pop('hot_core', True))

        explicit_lw = kwargs.get('linewidth', kwargs.get('lw', None))
        if explicit_lw is None:
            kwargs['linewidth'] = DEFAULT_TRACE_WIDTH
            base_linewidth = DEFAULT_TRACE_WIDTH
        else:
            base_linewidth = float(explicit_lw)

        lines = _ORIGINAL_AXES_PLOT(self, *args, **kwargs)

        for line in lines:
            requested_color = line.get_color()
            if requested_channel is None:
                channel = _next_auto_channel(self)
                style = channel_style(channel)
            else:
                channel = requested_channel
                if channel in DEFAULT_TRACE_STYLES:
                    style = channel_style(channel)
                else:
                    style = _style_from_color(requested_color)
            _apply_crt_rendering(
                self,
                line,
                style=style,
                linewidth=base_linewidth,
                glow_strength=glow_strength,
                hot_core=hot_core,
            )
        return lines

    Axes.plot = crt_plot
    _PATCHED = True



def uninstall_patch() -> None:
    global _PATCHED
    if not _PATCHED:
        return
    Axes.plot = _ORIGINAL_AXES_PLOT
    _PATCHED = False



def enable_auto_install() -> None:
    os.environ[AUTO_INSTALL_ENV_VAR] = '1'



def disable_auto_install() -> None:
    os.environ[AUTO_INSTALL_ENV_VAR] = '0'



def maybe_auto_install() -> bool:
    value = os.environ.get(AUTO_INSTALL_ENV_VAR, '').strip().lower()
    enabled = value in {'1', 'true', 'yes', 'on'}
    if enabled:
        install()
    return enabled



def scope_axes(ax: Axes, *, xdivs: int = 10, ydivs: int = 8) -> Axes:
    ax.minorticks_on()
    ax.grid(True, which='major', linewidth=0.85, alpha=0.42)
    ax.grid(True, which='minor', linewidth=0.32, alpha=0.11)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ax.set_xticks([x0 + i * (x1 - x0) / xdivs for i in range(xdivs + 1)])
    ax.set_yticks([y0 + i * (y1 - y0) / ydivs for i in range(ydivs + 1)])
    ax.set_xlabel('TIME')
    ax.set_ylabel('AMPLITUDE')
    return ax


maybe_auto_install()
