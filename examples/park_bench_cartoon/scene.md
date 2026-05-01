# Park Bench Cartoon

```yaml meta
title: Park Bench Cartoon
author: Thor Whalen
duration: 45
fps: 30
resolution:
  width: 1920
  height: 1080
default_style: cutout
```

A short two-character cartoon: Charlie and Maya on a park bench. Phase-1 skeleton
(IR only — rendering arrives in Phase 2).

## Shot s1 (cutout)

Wide establishing shot. The two of them sit, light wind, pigeons in the foreground.

```yaml shot
duration: 8
camera:
  move: hold
```

## Shot s2 (cutout)

Charlie turns toward Maya and asks his question.

```yaml shot
duration: 12
camera:
  move: hold
```

```dialogue
charlie: Did you ever wonder why we always meet here?
```

## Shot s3 (cutout)

Maya laughs, then answers. Slow camera push-in on her at the end.

```yaml shot
duration: 25
camera:
  move: push_in
```

```dialogue
maya: Because the pigeons trust us.
```
