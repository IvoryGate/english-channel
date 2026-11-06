"""Bounded-memory, audio-driven radial spectrum; no random animation."""
from __future__ import annotations

import math
from pathlib import Path
from dataclasses import asdict, dataclass, replace
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import soundfile as sf

from media.bar_waveform import _frame_bar_peaks
from media.media_layout import FPS
from media import resumable_frames


@dataclass(frozen=True)
class LightParticle:
    angle: float
    radius: float
    velocity: float
    energy: float
    age: float = 0
    lifetime: float = .6


def advance_particles(particles: list[LightParticle], peaks: np.ndarray,
                      previous: np.ndarray, last_emission: np.ndarray,
                      time: float, dt: float, size: int) -> list[LightParticle]:
    active = [replace(p, radius=p.radius+p.velocity*dt, age=p.age+dt)
              for p in particles if p.age+dt < p.lifetime
              and p.radius+p.velocity*dt < size*.48]
    rising = (peaks > .32) & ((peaks-previous)/dt > 1.2)
    local = (peaks >= np.roll(peaks, 1)) & (peaks >= np.roll(peaks, -1))
    eligible = np.flatnonzero(rising & local & (time-last_emission > .18))
    # Only the strongest local accents emit, not every frequency at once.
    for index in sorted(eligible, key=lambda i: float(peaks[i]), reverse=True)[:4]:
        value = float(peaks[index])
        radius = size*(.31+.052*value)+5
        active.append(LightParticle(-math.pi/2+index*2*math.pi/len(peaks),
                                   radius, size*(.16+.10*value), value))
        last_emission[index] = time
    return active


@lru_cache(maxsize=2)
def _spectrum_palette_base(size: int) -> Image.Image:
    """Reference-inspired green/cyan/blue/violet vertical light gradient."""
    stops = np.array([0, .42, .74, 1])
    colors = np.array([(95, 255, 156), (65, 235, 225),
                       (90, 166, 255), (220, 132, 255)])
    y = np.linspace(0, 1, size)
    rows = np.stack([np.interp(y, stops, colors[:, c]) for c in range(3)], axis=1)
    rgb = np.broadcast_to(rows[:, None, :], (size, size, 3)).astype(np.uint8)
    return Image.fromarray(rgb).convert('RGBA')


def spectrum_palette(size: int) -> Image.Image:
    # Callers change alpha; never expose the cached mutable image itself.
    return _spectrum_palette_base(size).copy()


def inner_ring_radii(peaks: np.ndarray, size: int) -> np.ndarray:
    """Inner thread moves independently; bar roots always stay on the outer circle."""
    return size * (.31 - .0375*np.clip(peaks, 0, 1))


def particle_opacity(particle: LightParticle) -> float:
    progress = min(1., max(0., particle.age/.065))
    fade_in = progress*progress*(3-2*progress)
    return fade_in * max(0., 1-particle.age/particle.lifetime)**1.4


@lru_cache(maxsize=2)
def _static_core(size: int) -> Image.Image:
    """Immutable artwork, antialiased once instead of once per audio frame."""
    image = Image.new('RGBA', (size*2, size*2))
    c, radius = size, size*.245*2
    ImageDraw.Draw(image).ellipse((c-radius, c-radius, c+radius, c+radius),
                                 fill=(17, 40, 35, 210))
    return image.resize((size, size), Image.Resampling.LANCZOS)


@lru_cache(maxsize=8)
def _band_directions(count: int) -> tuple[tuple[float, float], ...]:
    return tuple((math.cos(-math.pi/2+i*2*math.pi/count),
                  math.sin(-math.pi/2+i*2*math.pi/count)) for i in range(count))


def radial_frame(peaks: np.ndarray, *, size: int = 800,
                 bar_rgb: tuple[int, int, int] = (255, 255, 255),
                 avatar: Image.Image | None = None,
                 particles: list[LightParticle] | None = None,
                 inner_peaks: np.ndarray | None = None) -> Image.Image:
    scale = 2
    canvas = _static_core(size).copy()
    c = size * scale / 2
    inner = size * .31 * scale
    # All moving lights have one shared color palette; supersample only alpha.
    beams = Image.new('L', (size*scale, size*scale), 0)
    light = ImageDraw.Draw(beams)
    values = np.clip(peaks, 0, 1)
    ring_radii = inner_ring_radii(values if inner_peaks is None else inner_peaks, size)
    if len(ring_radii) != len(values):
        raise ValueError('Inner thread and spectrum must have matching band counts')
    ring_points = []
    for index, (value, (cosine, sine)) in enumerate(zip(values, _band_directions(len(values)))):
        # Keep the silhouette a ring: local short pulses, never long sun rays.
        radius = inner
        length = (3 + float(value) * size * .052) * scale
        start = (c + radius*cosine, c + radius*sine)
        end = (c + (radius+length)*cosine, c + (radius+length)*sine)
        bead_radius = float(ring_radii[index]) * scale
        bead_position = (c + bead_radius*cosine, c + bead_radius*sine)
        ring_points.append(bead_position)
        line_width = max(3, round(size * .0075)) * scale
        light.line((start, end), fill=255, width=line_width)
        cap = line_width / 2
        for x, y in (start, end):
            light.ellipse((x-cap, y-cap, x+cap, y+cap), fill=255)
        # Beads belong to the deforming inner thread, not a rigid circle.
        bead = size * .004 * scale
        x, y = bead_position
        light.ellipse((x-bead, y-bead, x+bead, y+bead), fill=255)
    if ring_points:
        light.line(ring_points + ring_points[:1], fill=210, width=2*scale, joint='curve')
    for particle in particles or []:
        fade = max(0, 1-particle.age/particle.lifetime)
        radius = (2+1.5*particle.energy) * scale * (.6+.4*fade)
        x = c + particle.radius * scale * math.cos(particle.angle)
        y = c + particle.radius * scale * math.sin(particle.angle)
        light.ellipse((x-radius, y-radius, x+radius, y+radius),
                      fill=round(235*particle_opacity(particle)))
    beams = beams.resize((size, size), Image.Resampling.LANCZOS)
    colored = spectrum_palette(size)
    colored.putalpha(beams)
    # Light blooms outward: never outline the beams with a dark stroke.
    for radius, strength in ((size * .008, .45), (size * .0025, .65)):
        glow = spectrum_palette(size)
        glow.putalpha(beams.filter(ImageFilter.GaussianBlur(radius)).point(lambda a: round(a * strength)))
        canvas = Image.alpha_composite(canvas, glow)
    canvas = Image.alpha_composite(canvas, colored)
    if avatar is not None:
        diameter = round(size * .45)
        if avatar.info.get('elr_circle') and avatar.size == (diameter, diameter):
            logo = avatar
        else:
            logo = avatar.convert('RGBA').resize((diameter, diameter), Image.Resampling.LANCZOS)
            mask = Image.new('L', (diameter, diameter))
            ImageDraw.Draw(mask).ellipse((0, 0, diameter-1, diameter-1), fill=255)
            logo.putalpha(mask)
        canvas.alpha_composite(logo, (round((size-diameter)/2), round((size-diameter)/2)))
    return canvas


def spectrum_targets(target: np.ndarray) -> np.ndarray:
    """Blend neighboring bands without amplifying all bars or changing bounds."""
    boosted = np.clip((target - .12) / .88, 0, 1) ** 1.7
    padded = np.pad(boosted, 1, mode='edge')
    return .15*padded[:-2] + .7*padded[1:-1] + .15*padded[2:]


def smooth_motion(position: np.ndarray, velocity: np.ndarray, target: np.ndarray,
                  dt: float, omega: float = 28.) -> tuple[np.ndarray, np.ndarray]:
    """Exact critically damped motion: carry velocity, no frame-dependent jumps."""
    offset = position-target
    impulse = velocity+omega*offset
    decay = math.exp(-omega*dt)
    result = target+(offset+impulse*dt)*decay
    speed = (velocity-omega*impulse*dt)*decay
    return np.clip(result, 0, 1), speed


def render_radial_waveform_video(audio_path: Path, output_path: Path, *,
                                width: int = 800, height: int = 800, fps: int = FPS,
                                bar_rgb: tuple[int, int, int], avatar_path: Path | None = None) -> Path:
    if width != height:
        raise ValueError('Radial spectrum requires square geometry')
    avatar = None
    if avatar_path and avatar_path.is_file():
        diameter = round(width * .45)
        with Image.open(avatar_path) as original:
            avatar = original.convert('RGBA').resize((diameter, diameter), Image.Resampling.LANCZOS)
        mask = Image.new('L', (diameter, diameter))
        ImageDraw.Draw(mask).ellipse((0, 0, diameter-1, diameter-1), fill=255)
        avatar.putalpha(mask)
        avatar.info['elr_circle'] = True
    identity = {
        'audio': resumable_frames.file_hash(audio_path), 'width': width, 'height': height,
        'fps': fps, 'barRgb': list(bar_rgb),
        'avatar': resumable_frames.file_hash(avatar_path) if avatar_path and avatar_path.is_file() else None,
        'renderer': resumable_frames.file_hash(Path(__file__)),
        'checkpointEngine': resumable_frames.file_hash(Path(resumable_frames.__file__)),
    }
    with sf.SoundFile(audio_path) as source:
        rate = source.samplerate
        window = round(.07 * rate)
        smoothed = np.zeros(48, dtype=np.float32)
        bar_velocity = np.zeros(48, dtype=np.float32)
        previous = np.zeros(96, dtype=np.float32)
        inner_motion = np.zeros(96, dtype=np.float32)
        inner_velocity = np.zeros(96, dtype=np.float32)
        last_emission = np.full(96, -1.0)
        particles: list[LightParticle] = []

        def save_state():
            arrays = dict(smoothed=smoothed, bar_velocity=bar_velocity, previous=previous,
                inner_motion=inner_motion, inner_velocity=inner_velocity, last_emission=last_emission)
            return {'arrays': {name: {'values': value.tolist(), 'dtype': value.dtype.str}
                for name, value in arrays.items()}, 'particles': [asdict(p) for p in particles]}

        def restore_state(data):
            nonlocal smoothed, bar_velocity, previous, inner_motion, inner_velocity, last_emission, particles
            arrays = []
            for name, count in (('smoothed', 48), ('bar_velocity', 48), ('previous', 96),
                    ('inner_motion', 96), ('inner_velocity', 96), ('last_emission', 96)):
                saved = data['arrays'][name]
                dtype = np.dtype(saved['dtype'])
                if dtype.kind != 'f' or dtype.itemsize not in (4, 8):
                    raise ValueError('Invalid radial checkpoint precision')
                value = np.asarray(saved['values'], dtype=dtype)
                if value.shape != (count,) or not np.all(np.isfinite(value)):
                    raise ValueError('Invalid radial motion checkpoint')
                arrays.append(value)
            restored_particles = [LightParticle(**p) for p in data['particles']]
            if len(restored_particles) > 1000 or any(
                    not all(math.isfinite(v) for v in asdict(p).values())
                    or p.lifetime <= 0 for p in restored_particles):
                raise ValueError('Invalid particle checkpoint')
            smoothed, bar_velocity, previous, inner_motion, inner_velocity, last_emission = arrays
            particles = restored_particles

        def draw_frame(frame):
            nonlocal smoothed, bar_velocity, previous, inner_motion, inner_velocity, particles
            end = min(len(source), round(frame / fps * rate))
            start = max(0, end-window)
            source.seek(start)
            chunk = source.read(end-start, dtype='float32', always_2d=True).mean(axis=1)
            rms = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) else 0
            target = _frame_bar_peaks(chunk, 48, rate) * min(1.0, rms / .035)
            smoothed, bar_velocity = smooth_motion(smoothed, bar_velocity, spectrum_targets(target), 1/fps)
            values = np.concatenate((smoothed, smoothed[::-1]))
            inner_motion, inner_velocity = smooth_motion(inner_motion,
                inner_velocity, np.sqrt(values), 1/fps, omega=22.)
            particles = advance_particles(particles, values, previous,
                last_emission, frame/fps, 1/fps, width)
            image = radial_frame(values, size=width, bar_rgb=bar_rgb,
                avatar=avatar, particles=particles, inner_peaks=inner_motion)
            previous = values.copy()
            return image

        return resumable_frames.render_resumable_frames(output=output_path,
            total_frames=max(1, math.ceil(len(source) / rate * fps)), width=width,
            height=height, fps=fps, identity=identity, draw_frame=draw_frame,
            save_state=save_state, restore_state=restore_state)
