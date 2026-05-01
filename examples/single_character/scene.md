# Single Character Smoke

The simplest renderable scene: one character (placeholder rect parts), one shot,
two seconds. Used as the Phase 2D end-to-end test.

```yaml meta
title: Single Character Smoke
duration: 2
fps: 24
resolution:
  width: 320
  height: 240
default_style: cutout
```

## Shot s1 (cutout)

```yaml shot
duration: 2
```

```yaml entities
- kind: character
  id: charlie
  store: characters
  ref: charlie-v1
```
