# Changelog

AI-maintained record of substantive changes to the anima codebase. One entry per
day per chunk of work; keep entries terse.

## 2026-05-01

- Phase 1 substrate landed: Scene IR (Pydantic + composition combinators + flatten + validate + migrate + sync), dol-backed project mall (characters, environments, voices, styles, scenes, artifacts, decisions), Renderer / TTSProvider / LipSyncProvider / Verifier protocols, project init/load/save, argh-based CLI (`anima init / validate / sync / check`), `check_requirements` diagnostics, three project skills (`anima`, `anima-spec`, `anima-dev`), example `park_bench_cartoon/` skeleton, tests with doctests + pytest.
- Phase 2A — Python-side cutout subsystem: `anima/adapters/cutout/` ships transform math (`Matrix3x3`, `TransformParams`, decompose/compose), easing (named presets + cubic-Bézier dispatcher), scene graph (`Node` tree as `MutableMapping[str, Node]`, lazy world-transform with dirty propagation, slot machinery), animation channels (`Keyframe`, `Channel`, binary-search evaluation), poses (`Pose: dict[(target, prop), value]`, `apply_pose`, `merge_poses` with override semantics), clips (`Clip` with `LoopMode.ONCE/LOOP/PING_PONG`), timeline (`Track`, `PlacedClip`, `Timeline`, `evaluate_timeline` with track-order override), JSON contract for the JS runtime (`CutoutSceneJSON` + nested Pydantic models, `to_dict`/`from_dict` round-trip), `compile_shot(Shot, mall)` bridge from authoring `anima.ir` types into runtime JSON, and `CutoutRenderer` skeleton self-registering on import. 175/175 tests pass.
