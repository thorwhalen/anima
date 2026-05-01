# Animation interchange formats: a deep schema-level analysis for 2D cutout systems

**The most transferable design patterns for a Python-to-browser animation pipeline come not from any single format but from combining Spine's skeletal data model, Rive's state machine architecture, Lottie's animatable property pattern, USD's composition/layering system, and glTF's channel–sampler separation.** No existing format adequately covers the full requirements of a programmatically-authored 2D cutout animation system with AI orchestration — but roughly 80% of the needed schema can be assembled from proven patterns across these formats. The remaining 20% (progressive refinement layers, DSL-friendly composition primitives, and runtime-switchable blend trees) requires genuine invention. This report provides the format-level evidence to make those design decisions.

The architecture under analysis is: Python generates scene descriptions → custom JSON format → JS/TS renders in browser via PixiJS v8 + GSAP. Report 1 identified the absence of an open skeletal animation interchange format as the ecosystem's largest gap. This report examines twelve formats to extract the structural patterns, data models, and architectural lessons that should inform the custom schema design.

---

## Lottie's property animation model is the pattern to adopt for keyframes

Lottie's core contribution to format design is its **animatable property pattern** — a compact, elegant encoding that every property in the scene graph uses consistently. The pattern distinguishes static from animated values at the property level:

```json
{
  "a": 0,
  "k": [256, 256]
}
```

When animated, the same structure switches to a keyframe array:

```json
{
  "a": 1,
  "k": [
    {
      "t": 0,
      "s": [100, 200],
      "o": {"x": [0.333], "y": [0]},
      "i": {"x": [0.667], "y": [1]}
    },
    {
      "t": 60,
      "s": [400, 200]
    }
  ]
}
```

The `o` (out) and `i` (in) handles define cubic Bézier easing between keyframes, with **x mapping to normalized time** and **y mapping to interpolation factor** — identical semantics to CSS `cubic-bezier()` and directly mappable to GSAP's `CustomEase`. Position keyframes add spatial tangents (`ti`/`to`) for curved motion paths. Multi-dimensional properties support **per-axis easing** — each dimension of a position can ease independently.

Lottie's document structure uses a flat layer list with integer-index parenting (`ind`/`parent` fields) to form implicit hierarchies. Null layers (type 3) serve as invisible pivots, functioning as bones in character rigs. Precompositions encapsulate sub-timelines referenced by ID from an assets registry, with optional time remapping. This architecture supports character rigging through After Effects tools like Duik, but **all IK and expressions must be baked to raw keyframes before export** — Lottie carries no live constraint data.

The format's limitations for cutout animation are fundamental. There is **no skeletal mesh deformation** — vertices can only be animated via shape keyframes, not driven by bones. There are **no state machines** — the format describes a single linear timeline with no branching, conditions, or runtime interaction model. Expressions exist as embedded JavaScript strings but are supported only by lottie-web; all other runtimes (lottie-android, lottie-ios, Skottie, rlottie) ignore them. The Lottie Animation Community spec, now governed by the Linux Foundation, is still a draft covering a subset of Bodymovin's de facto features — expressions and effects remain explicitly outside the formal specification.

**What to borrow**: The `{a, k}` animatable property pattern. Cubic Bézier easing with per-dimension control. The centralized asset registry pattern. Precomp-style sub-composition references. **What to avoid**: Single-letter property keys (`a`, `k`, `s`, `o`, `i`) that sacrifice readability for compactness — use descriptive names since gzip handles the compression. Integer-based layer indexing — use string IDs. The linear-timeline-only limitation.

---

## Spine's skeletal data model sets the structural gold standard

Spine's JSON format is the most mature open documentation of a 2D skeletal animation data model. Its architecture separates static structure (the **setup pose**) from dynamic change (the **animation deltas**), a pattern that maps directly to the "rig definition vs. animation clip" separation needed in the custom format.

The top-level structure is clean and purposeful:

```json
{
  "skeleton": { "spine": "4.2.40", "width": 470, "height": 731 },
  "bones": [
    { "name": "root" },
    { "name": "torso", "parent": "root", "length": 85.82, "rotation": 94.95, "x": -6.42, "y": 1.97 }
  ],
  "slots": [
    { "name": "left-arm", "bone": "left arm", "attachment": "left-arm" }
  ],
  "skins": [
    { "name": "default", "attachments": {
        "left-arm": { "left-arm": { "x": 0, "y": 0, "width": 63, "height": 47 } }
    }}
  ],
  "animations": {
    "walk": {
      "bones": { "torso": { "rotate": [
        { "time": 0, "angle": -26.55 },
        { "time": 0.133, "angle": -8.78, "curve": [0.25, 0, 0.75, 1] }
      ]}}
    }
  }
}
```

**Bones** form an ordered array where parents always precede children, enabling single-pass hierarchy construction. Transform values are relative to parent and define the setup pose; animation values are **deltas from setup**. This delta model is critical — it means the same walk animation produces correct results regardless of the character's base proportions, enabling animation reuse across differently-proportioned rigs.

**Slots** serve a dual purpose: they define both draw order (array position) and attachment containers. Each slot is bound to exactly one bone and displays one attachment at a time. This indirection layer between bones and visual content is Spine's most distinctive pattern — it allows the skeleton topology to remain stable while visual appearances change through skin swapping.

**Skins** use a compound key — `slot name + attachment key` — to map visual content to the skeleton. The `default` skin serves as fallback; named skins can override specific attachments. Crucially, skins in Spine 4.x can also activate skin-specific bones and constraints, enabling mechanical differences (not just cosmetic) between character variants.

**Weighted meshes** encode per-vertex bone influences compactly: `[boneCount, boneIdx, x, y, weight, ...]` packed sequentially in the vertices array. Detection of weighted vs. unweighted meshes is implicit — if `vertices.length > uvs.length`, the mesh is weighted. This encoding is space-efficient but relies on careful parsing.

The constraint system includes **IK** (1-bone or 2-bone chains with mix/bend direction), **transform constraints** (per-axis copying of another bone's SRT), **path constraints** (distributing bones along path attachments), and **physics constraints** (Spine 4.2+, providing procedural secondary motion for hair, cloth, and tails that respond dynamically to movement rather than being baked). Keyframe easing uses `[cx1, cy1, cx2, cy2]` cubic Bézier notation, identical to CSS semantics.

The runtime contract follows a data/instance separation: `SkeletonData` (shared, stateless) spawns `Skeleton` instances (stateful). The per-frame pipeline is `state.update(delta) → state.apply(skeleton) → skeleton.updateWorldTransform()`. Animation mixing uses tracks — track 0 is the base, higher tracks override with configurable alpha — plus automatic crossfading with per-animation-pair mix durations stored in `AnimationStateData`.

**Licensing is permissive for format inspiration.** Writing a custom runtime that reads Spine JSON requires no Spine license. The format documentation is public and explicitly states that data can be processed and re-imported. However, generating Spine-compatible JSON for use with official Spine runtimes requires users of those runtimes to hold Spine Editor licenses. For the custom format under design, there are **zero licensing concerns** — the goal is to learn from Spine's architecture, not to produce Spine-compatible files.

---

## Rive's state machine is the model to replicate

Rive's state machine architecture is the most sophisticated interactive animation control system in the 2D ecosystem. While its `.riv` binary format is impractical to adopt directly (proprietary, editor-dependent, no write libraries), the **conceptual model** should be replicated almost wholesale in the custom JSON format.

The state machine is a directed graph evaluated per-frame. States are animation playback units; transitions are conditional edges. Each artboard can host multiple state machines, and each state machine supports **multiple concurrent layers** — only one state is active per layer, but layers mix additively. This enables simultaneous body movement, facial expression, and hand gesture tracks running independently.

**Inputs** form the contract between the animation system and application code. Three types: `boolean` (binary toggles), `number` (continuous values for blend control), and `trigger` (fire-and-forget events). These map cleanly to a Python DSL surface:

```json
{
  "stateMachine": {
    "inputs": [
      { "name": "speed", "type": "number", "default": 0 },
      { "name": "isGrounded", "type": "boolean", "default": true },
      { "name": "jump", "type": "trigger" }
    ],
    "layers": [{
      "states": [
        { "name": "idle", "animation": "idle_loop" },
        { "name": "locomotion", "type": "blend1D", "input": "speed",
          "animations": [
            { "name": "walk", "position": 0 },
            { "name": "run", "position": 100 }
          ]
        },
        { "name": "jump", "animation": "jump_oneshot" }
      ],
      "transitions": [
        { "from": "idle", "to": "locomotion",
          "conditions": [{ "input": "speed", "op": ">", "value": 0.1 }],
          "duration": 0.2 },
        { "from": "locomotion", "to": "idle",
          "conditions": [{ "input": "speed", "op": "<=", "value": 0.1 }],
          "duration": 0.3 },
        { "from": "anyState", "to": "jump",
          "conditions": [{ "input": "jump", "type": "trigger" }],
          "duration": 0.1 }
      ]
    }]
  }
}
```

**Blend states** are Rive's mechanism for parametric animation. A 1D blend state mixes multiple timelines along a single numeric input axis — setting `speed` to 30 blends walk and run proportionally. Additive blend states combine via multiple independent inputs, each controlling a different animation's mix weight. **Listeners** bridge pointer events to input changes declaratively, mapping shapes to hit areas without code.

Rive's runtime architecture processes state machines in a tight loop: process pointer events → evaluate input conditions → fire transitions → advance current state animation → apply animation values → resolve constraints → render. The C++ core compiles to WebAssembly for browser deployment. The key limitation is that `.riv` is binary-only with no JSON representation, generated exclusively by the Rive editor. The predecessor format (Flare) supported JSON export, and the community has noted its removal as a significant loss for tooling. No official write library exists — runtimes are read-only.

**What to borrow**: The full state machine graph model (states, transitions, conditions, duration, exit time). Multi-layer concurrent state machines. 1D and additive blend states. Typed inputs as the API contract. Listeners as declarative event-to-input bridges. **What to avoid**: Binary-only serialization. Context-dependent serialization where object ordering implies ownership. Integer index-based parent references (use string IDs).

---

## USD's composition arcs solve the progressive refinement problem

USD's composition system, while designed for 3D film production, contains the most directly applicable concepts for the sketch-then-polish workflow described in the architecture. The **LIVRPS strength ordering** (Local, Inherits, Variants, References, Payloads, Specializes) defines how multiple layers of scene description compose into a final result, with the **strongest opinion winning** for any given property.

The layering model maps precisely to an AI-assisted animation pipeline:

```
Layer stack (strongest → weakest):
  director_notes.json      ← Final creative overrides
  artist_refinement.json   ← Polished timing, improved poses  
  ai_generated.json        ← Rough animation from AI
```

Each layer provides "opinions" about properties. The artist can fix the AI's timing without modifying the AI-generated layer — the artist's opinion simply overrides for those specific properties. The director can override specific shots without touching the artist's work. **All edits are preserved and auditable** — removing a stronger layer reveals the weaker opinions beneath. This non-destructive stacking is fundamentally different from Lottie or Spine's single-file, flattened representations.

**VariantSets** offer named alternatives that can be switched at runtime. A character node could define costume variants (`casual`, `formal`, `armor`), expression sets, or alternate animation styles — selectable without file replacement. **References** enable file-level composition: a scene JSON references a character JSON, which references a rig JSON. **Payloads** mark heavy data (sprite sheets, dense keyframe tracks) for deferred loading.

USD's time sampling stores animation as discrete time-value pairs per attribute, with linear interpolation by default. Recent versions (26.x) add spline support with knots and tangents. The **default value + time samples** duality maps well to the setup-pose + animation concept from Spine — every attribute has a rest value outside time and optional keyframed overrides.

The UsdSkel schema demonstrates clean skeletal data modeling: `UsdSkelSkeleton` encodes joint hierarchies as compact path token arrays, with `bindTransforms` and `restTransforms` stored separately. `UsdSkelAnimation` stores joint transforms as vectorized arrays of translation, rotation (quaternion), and scale — decoupled from the skeleton definition so different animations can be applied to the same rig. `UsdSkelBlendShape` defines point offsets with support for in-betweens and sparse subsets.

**Full USD is impractical for browser rendering** — the C++ runtime is ~30MB+ compiled, and WASM ports remain experimental with large binary sizes. The recommendation is to extract concepts, not the runtime. A lightweight JSON implementation of LIVRPS-style layering, variant selection, and reference composition would provide USD's most valuable capabilities at a fraction of the complexity.

---

## glTF's channel–sampler model provides the cleanest animation data separation

glTF's animation model achieves remarkable clarity by fully separating **what to animate** (channels) from **how to animate** (samplers):

```json
{
  "animations": [{
    "channels": [
      { "sampler": 0, "target": { "node": 5, "path": "rotation" } },
      { "sampler": 1, "target": { "node": 5, "path": "translation" } }
    ],
    "samplers": [
      { "input": 2, "output": 3, "interpolation": "CUBICSPLINE" },
      { "input": 2, "output": 4, "interpolation": "LINEAR" }
    ]
  }]
}
```

A **channel** points a sampler at a target (node ID + property path). A **sampler** binds input timestamps to output values with an interpolation mode. This indirection allows samplers to be shared across channels and makes the data model self-documenting.

The `CUBICSPLINE` interpolation encodes Hermite tangents inline: for each keyframe, the output contains `[inTangent, value, outTangent]`, with tangents scaled by `deltaTime` between adjacent keyframes. The cubic Hermite formula `p(t) = (2t³ - 3t² + 1)p₀ + (t³ - 2t² + t)m₀ + (-2t³ + 3t²)p₁ + (t³ - t²)m₁` provides smooth interpolation without requiring Bézier conversion.

The `KHR_animation_pointer` extension is particularly relevant — it enables animating **any property** via JSON pointer notation: `"/materials/0/pbrMetallicRoughness/baseColorFactor"`. Adapted for 2D, this becomes a general mechanism for animating opacity, tint color, texture frame index, or any custom property: `"/nodes/character/leftArm/opacity"`. This pattern directly supports the flexibility needed for a DSL where `scene.add(charlie.set_expression("surprised"))` must resolve to a concrete property path in the scene graph.

glTF is fundamentally 3D and lacks 2D-specific concepts: no sprite atlas support, no 2D transform model (it uses quaternions and VEC3), no draw order mechanism, no named easing functions beyond LINEAR/STEP/CUBICSPLINE. But its channel–sampler architecture and KHR_animation_pointer generality are worth adopting directly.

---

## Lessons from SVG, SWF, Godot, Theatre.js, and Motion Canvas

**SVG's scene graph** provides an excellent conceptual vocabulary for the JSON format. The `<g>` (group with inherited transforms), `<defs>` (definitions not rendered directly), `<symbol>` (reusable component with its own coordinate system), and `<use>` (instance reference) elements map directly to scene graph node types. SVG's transform composition — each nested group establishing a new local coordinate space with matrix multiplication down the tree — is exactly the model PixiJS implements internally. However, SVG rendering hits a **performance ceiling around 3,000–5,000 animated elements** due to DOM overhead, and Chrome does not hardware-accelerate SVG transforms. For character animation, **PixiJS Canvas rendering is the correct target**, with SVG serving as the conceptual model and asset source format.

GSAP's SVG handling reveals important implementation details. GSAP applies transforms via the `transform` attribute (matrix notation) rather than CSS, normalizes `transformOrigin` to work element-relative (fixing SVG's viewport-relative default), and supports independent component animation (rotation doesn't affect scale). These normalization behaviors should inform how the JSON format encodes transform origins and component independence.

**SWF's define-once, instantiate-many model** is architecturally significant. Characters were defined as symbols in a dictionary and instantiated with different transforms, properties, and independent timeline playback. This is precisely the instancing model needed for cutout animation — a hand symbol defined once and instantiated on left and right arms. SWF's nested independent timelines (each MovieClip with its own playhead) enabled complex compositions from simple building blocks. Frame labels as named anchors (`gotoAndPlay("walk_start")`) proved more maintainable than frame numbers.

**Godot's NodePath addressing** (`"Parent/Child:property"`) is the most practical pattern for animation targeting. Any property on any node can be animated via path strings. Godot's AnimationPlayer + AnimationTree separation cleanly divides animation data (keyframe tracks) from animation control logic (state machines, blend trees) — a separation the custom format should maintain. The `.tscn` text format demonstrates that human-readable, VCS-friendly scene files can be generated programmatically — users report writing Python scripts to generate Godot scenes from databases.

**Theatre.js demonstrates pure data separation**: animation data knows nothing about the renderer. The Project → Sheet → Object → Prop hierarchy with typed properties and constraints (`types.number(1, { range: [0, 1] })`) provides both runtime validation and UI hints. The pattern of "code declares structure, editor refines values" aligns with the Python DSL → JSON → visual editor workflow.

**Motion Canvas proves code-first animation viability** with TypeScript generator functions. Its flow combinators — `all()` for parallel, `sequence()` for staggered, `delay()`, `loop()` — are the primitives a Python DSL needs. The Python equivalent using `yield from` (or async/await) would serialize to JSON composition nodes describing how animation clips combine. DragonBones and COLLADA provide cautionary tales: DragonBones died from single-company dependency and editor coupling; COLLADA failed from under-specified structure, missing conformance tests, and trying to be everything.

---

## Comparative matrix across all formats

| Capability | Lottie | Rive | Spine | SVG+SMIL | USD | glTF | DragonBones | SWF | Godot |
|---|---|---|---|---|---|---|---|---|---|
| Hierarchical scene graph | Medium | High | High | High | High | High | High | High | High |
| Skeletal rigging | Low | High | High | None | High | High | High | Low | Medium |
| Mesh deformation | None | High | High | None | High | High | High | None | Low |
| Keyframe animation | High | High | High | High | High | High | High | High | High |
| Procedural animation | Low | Low | Medium | None | Low | None | None | Low | Low |
| State machines | None | High | None | None | None | None | None | Low | High |
| Blend trees | None | High | Medium | None | None | None | None | None | High |
| Lip sync / morph targets | Low | Medium | Medium | None | High | High | Low | None | Low |
| Progressive refinement | None | None | None | None | High | None | None | None | Low |
| Programmatic generation | High | Low | High | High | Medium | High | Medium | Low | High |
| Human readability | Medium | None | High | High | High | Medium | High | None | High |
| Browser runtime available | High | High | High | High | Low | High | Medium | None | None |

---

## Structural patterns that recur across multiple formats

Five architectural patterns appear across three or more formats and should be considered canonical for the custom schema:

**Pattern 1 — Channels reference targets by path.** glTF's `target: { node, path }`, Godot's `NodePath("Node:property")`, USD's attribute paths, and KHR_animation_pointer's JSON pointers all converge on string-based property addressing. The custom format should use: `"target": "character/leftArm:rotation"`.

**Pattern 2 — Keyframes use cubic Bézier easing.** Lottie, Spine, Rive, SMIL (`keySplines`), and CSS animations all encode easing as `[cx1, cy1, cx2, cy2]` cubic Béziers with x=time, y=value on a [0,1] normalized range. This maps directly to GSAP's `CustomEase.create("id", "M0,0 C cx1,cy1 cx2,cy2 1,1")` and CSS `cubic-bezier()`.

**Pattern 3 — Setup pose plus animation deltas.** Spine (setup pose vs. animation timelines), USD (default values vs. time samples), Rive (artboard base state vs. animation overrides), and glTF (node TRS vs. animation channels) all separate rest-state from motion. Every node property has a default value; animations express differences from that default.

**Pattern 4 — Skins/variants decouple skeleton from appearance.** Spine skins, USD VariantSets, DragonBones skins, and Rive's Solo node all enable swapping visual content without changing the underlying skeleton topology. The custom format should support this through a skin/variant system where `slot → attachment` mappings can be switched at runtime.

**Pattern 5 — Define once, reference many.** Lottie precomps, SWF symbols, SVG `<defs>`/`<use>`, USD references, and Godot scene instancing all provide asset definition and reuse. A centralized definitions registry with ID-based referencing is essential.

---

## Concrete schema design recommendations

Based on the cross-format analysis, the custom JSON schema should adopt the following structure. Here is an annotated skeleton showing how patterns from each source format combine:

```json
{
  "format": "cutout-anim",
  "version": "1.0.0",
  "compatibleVersion": "1.0.0",

  "meta": {
    "name": "Charlie Walk Cycle",
    "framerate": 30,
    "width": 1920,
    "height": 1080,
    "generator": "cutout-dsl-python/0.1.0"
  },

  "assets": {
    "images": {
      "charlie_torso": { "src": "sprites/charlie/torso.png", "width": 120, "height": 180 },
      "charlie_arm_upper": { "src": "sprites/charlie/arm_upper.png", "width": 40, "height": 80 }
    },
    "atlases": {
      "charlie_faces": { "src": "sprites/charlie/faces.json", "image": "sprites/charlie/faces.png" }
    }
  },

  "skeleton": {
    "bones": [
      { "id": "root", "x": 960, "y": 540 },
      { "id": "hip", "parent": "root", "length": 40, "rotation": 0 },
      { "id": "torso", "parent": "hip", "length": 120, "rotation": -90, "x": 0, "y": -40 },
      { "id": "upperArmL", "parent": "torso", "length": 60, "rotation": 170, "x": -30, "y": -110 },
      { "id": "forearmL", "parent": "upperArmL", "length": 55, "rotation": -20 }
    ],
    "constraints": [
      { "type": "ik", "id": "armIK_L", "bones": ["upperArmL", "forearmL"],
        "target": "handTarget_L", "mix": 1.0, "bendPositive": true }
    ]
  },

  "slots": [
    { "id": "torsoSlot", "bone": "torso", "attachment": "charlie_torso",
      "anchor": [0.5, 0.85] },
    { "id": "upperArmSlotL", "bone": "upperArmL", "attachment": "charlie_arm_upper",
      "anchor": [0.5, 0.1] }
  ],

  "skins": {
    "default": {},
    "winter": {
      "torsoSlot": { "attachment": "charlie_torso_coat" },
      "upperArmSlotL": { "attachment": "charlie_arm_coat" }
    }
  },

  "animations": {
    "walk": {
      "duration": 1.0,
      "loop": true,
      "tracks": {
        "torso:rotation": {
          "keyframes": [
            { "time": 0, "value": -2, "easing": [0.25, 0, 0.75, 1] },
            { "time": 0.5, "value": 2, "easing": [0.25, 0, 0.75, 1] },
            { "time": 1.0, "value": -2 }
          ]
        },
        "upperArmL:rotation": {
          "keyframes": [
            { "time": 0, "value": 30 },
            { "time": 0.5, "value": -30 },
            { "time": 1.0, "value": 30 }
          ]
        },
        "torsoSlot:opacity": {
          "keyframes": [
            { "time": 0, "value": 1.0 }
          ]
        }
      },
      "events": [
        { "time": 0.25, "name": "footstep", "data": { "foot": "left" } },
        { "time": 0.75, "name": "footstep", "data": { "foot": "right" } }
      ]
    }
  },

  "stateMachine": {
    "inputs": [
      { "name": "speed", "type": "number", "default": 0 },
      { "name": "grounded", "type": "boolean", "default": true },
      { "name": "emote", "type": "trigger" }
    ],
    "layers": [
      {
        "name": "locomotion",
        "states": [
          { "name": "idle", "animation": "idle" },
          { "name": "move", "type": "blend1D", "input": "speed",
            "points": [
              { "animation": "walk", "position": 50 },
              { "animation": "run", "position": 100 }
            ]
          }
        ],
        "transitions": [
          { "from": "idle", "to": "move", "duration": 0.2,
            "conditions": [{ "input": "speed", "op": ">", "value": 5 }] },
          { "from": "move", "to": "idle", "duration": 0.3,
            "conditions": [{ "input": "speed", "op": "<=", "value": 5 }] }
        ]
      },
      {
        "name": "expression",
        "states": [
          { "name": "neutral", "animation": "face_neutral" },
          { "name": "emoting", "animation": "face_emote" }
        ],
        "transitions": [
          { "from": "anyState", "to": "emoting", "duration": 0.15,
            "conditions": [{ "input": "emote", "type": "trigger" }] }
        ]
      }
    ]
  },

  "composition": {
    "type": "sequence",
    "children": [
      { "type": "setInput", "input": "speed", "value": 0, "duration": 2.0 },
      { "type": "parallel", "children": [
        { "type": "tween", "input": "speed", "to": 80, "duration": 1.5,
          "easing": "power2.inOut" },
        { "type": "event", "name": "startWalking" }
      ]},
      { "type": "setInput", "input": "speed", "value": 80, "duration": 4.0 }
    ]
  },

  "layers": [
    { "name": "ai_draft", "src": "layers/ai_generated.json" },
    { "name": "artist_polish", "src": "layers/artist_refinement.json" },
    { "name": "director_override", "src": "layers/director_notes.json" }
  ]
}
```

This schema synthesizes **Spine's skeletal model** (bones, slots, skins, setup pose), **Rive's state machine** (inputs, layers, blend states, transitions), **Lottie's keyframe encoding** (per-property tracks with Bézier easing), **glTF's channel–sampler separation** (tracks keyed by `"nodeId:property"` paths), **USD's layering** (ordered override layers with external references), and **Motion Canvas's composition primitives** (sequence, parallel, tween nodes for DSL serialization).

---

## The adopt-versus-extend-versus-invent decision

Three strategic paths exist, with sharply different tradeoffs:

**Adopt Lottie (extend with custom keys)** — Lottie's spec permits unknown properties, and renderers silently ignore them. A custom schema could embed skeletal data, state machines, and constraints in Lottie-compatible JSON that degrades gracefully in standard Lottie players (showing baked fallback animation). The `dotLottie` container format already adds state machines at the packaging level. However, Lottie's linear-timeline DNA makes this approach feel like building a house on foundations designed for a shed. The impedance mismatch between Lottie's motion-graphics model and interactive character animation would create persistent friction.

**Adopt Spine's format (generate compatible JSON)** — Spine's JSON is the closest existing format to what's needed for skeletal 2D cutout animation. A Python DSL could generate Spine-compatible JSON consumed by `pixi-spine`. This works well for the skeletal core but lacks state machines, composition primitives, progressive refinement layers, and DSL metadata. Extending Spine JSON with custom sections risks breaking `pixi-spine` compatibility on updates and creates an awkward hybrid. Additionally, Spine runtimes expect Spine-version-matched data — the tight coupling between export version and runtime version means format changes require synchronized updates across the pipeline.

**Design a custom format with optional export adapters** — This is the recommended path. Design a schema optimized for the specific requirements (Python generation, PixiJS rendering, AI orchestration, progressive refinement), then build **export adapters** that can flatten the custom format into Lottie JSON (for sharing/preview), Spine JSON (for game engine integration), or other targets as needed. This avoids inheriting any single format's limitations while preserving interoperability.

The export adapter approach means the custom format can include features no existing format supports — progressive refinement layers, composition trees, DSL metadata, AI provenance tracking — without worrying about backward compatibility. The custom runtime in JS/TS interprets the full format; export adapters produce lossy-but-useful conversions for external tools.

---

## What the format needs for an ergonomic Python DSL

For a DSL surface like `scene.add(charlie.walk_to(200, duration=3))` to generate clean JSON, the format must support several DSL-specific patterns:

**Composition primitives** that serialize generator-style animation code. Motion Canvas proves this works: `all()`, `sequence()`, `delay()`, and `loop()` combinators translate to JSON composition nodes. The Python DSL compiles `charlie.walk_to(200).then(charlie.wave())` into a `{ "type": "sequence", "children": [...] }` tree. These nodes describe temporal relationships between animation clips and state machine inputs, bridging the gap between imperative Python code and declarative JSON data.

**Named easing presets** beyond raw Bézier curves. While the format should support `[cx1, cy1, cx2, cy2]` notation for precision, it should also accept GSAP-compatible named easings like `"power2.inOut"`, `"elastic.out"`, `"back.in(1.7)"`. The JS runtime resolves these to GSAP easing functions directly. This makes the DSL more readable: `charlie.walk_to(200, easing="power2.inOut")` vs. `charlie.walk_to(200, easing=[0.455, 0.03, 0.515, 0.955])`.

**Relative and absolute addressing**. The DSL should support both `charlie.left_arm.rotation = 30` (object-oriented access that resolves to `"charlie/leftArm:rotation"` path) and `scene.set("charlie/leftArm:rotation", 30)` (direct path access). The JSON format uses path strings; the Python DSL provides syntactic sugar.

**Implicit setup-pose capture**. When the DSL constructs a character (`charlie = Character("charlie", rig="humanoid")`), the current property values become the setup pose. Animations authored via the DSL express deltas. The format encodes both explicitly — the skeleton section holds setup values, animation tracks hold deltas — but the DSL handles the math transparently.

**Layer-aware authoring**. The DSL should track which "layer" (ai_draft, artist_polish, director_override) an edit targets. This metadata flows into the JSON layers system. `with scene.layer("artist_polish"): charlie.walk.timing_adjust(0.1)` writes the timing override to the artist layer, preserving the AI draft beneath.

---

## Conclusion: build a format, not a compromise

The analysis of twelve formats reveals a clear architectural consensus on scene graph representation (hierarchical nodes with inherited transforms), keyframe encoding (cubic Bézier easing in normalized [0,1] space), and skeletal data modeling (bones → slots → skins → animations as separable concerns). These are solved problems — adopt them directly.

The genuine innovations needed are in three areas. First, **progressive refinement through layered opinions** — only USD addresses this, and its full runtime is impractical for the browser. Implementing a lightweight LIVRPS-inspired layer system in JSON, where property opinions from multiple sources compose with explicit strength ordering, would be genuinely novel in the 2D animation space. Second, **state machines as first-class JSON citizens** — Rive proves the model works but locks it in a proprietary binary; extracting this into an open, human-readable JSON structure with typed inputs, multi-layer graphs, and blend states fills the ecosystem gap Report 1 identified. Third, **composition primitives that serialize DSL intent** — no existing format captures the temporal composition semantics (`sequence`, `parallel`, `stagger`) that a Python DSL needs to express choreography.

The critical risk is scope creep. COLLADA's failure demonstrates that a format trying to be everything becomes reliable at nothing. The custom format should be **opinionated about 2D cutout animation**: it handles bones, sprites, state machines, blend trees, and multi-layer composition. It does not handle 3D, particles, physics simulation, or audio mixing. For everything outside its scope, it provides export adapters and extensibility via a `userData` field on every node. Conformance tests and a reference runtime implementation — not just a specification document — are essential from day one.