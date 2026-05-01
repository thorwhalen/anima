# Text-to-Structured-Animation: Deep Research Report

## A Roadmap for Building Agentic Educational Video Production Tools

**Author:** Thor Whalen
**Date:** March 2026

---

## Executive Summary

This report investigates the emerging space of **text-to-structured-animation** — the pipeline that transforms natural language descriptions into precise, editable, code-driven animations suitable for educational video production. Unlike generative text-to-video models (Runway, Pika, Kling) which produce opaque pixel-level output, structured animation preserves semantic objects, timelines, and editability — critical properties for educational content where accuracy matters more than photorealism.

The field is young and fragmented. Several academic projects (TheoremExplainAgent, Manimator, MoVer) have demonstrated that LLM-driven pipelines can produce structured Manim animations from natural language, but no production-grade, general-purpose, agent-controllable tool exists today. This represents a significant gap — and opportunity.

---

## 1. Landscape of Programmatic Animation Engines

### 1.1 Composability Audit

The core question for agentic control is: *how programmable is the interface?* A tool might be powerful, but if it can't be driven by an AI agent (via CLI, Python API, or MCP), it's useless for our purposes.

| Engine | Language | API Surface | CLI | Agent Skill Available | License | Cloud Rendering | Composability Score |
|--------|----------|-------------|-----|----------------------|---------|----------------|-------------------|
| **Manim CE** | Python | Full Python API, Scene classes | `manim render` | Yes (skills.sh) [1] | MIT | No (local only) | ★★★★★ |
| **ManimGL (3b1b)** | Python | Full Python API, OpenGL | `manimgl` | Yes (skills.sh) [2] | MIT | No | ★★★★☆ |
| **Motion Canvas** | TypeScript | Generator functions, signals | `npm start` + editor | Yes (skills.sh) [3] | MIT | No (local + editor) | ★★★★☆ |
| **Remotion** | React/TS | React components, props | `npx remotion render` | No dedicated skill | BSL 1.1 (free for small biz) | Yes (Lambda, Cloud Run) [4] | ★★★★★ |
| **Lottie** | JSON spec | JSON manipulation | Via renderers | No | CC BY 4.0 (spec) | Via web players | ★★★☆☆ |
| **After Effects** | ExtendScript | CEP/UXP panels | `aerender` CLI | No | Proprietary ($$$) | No | ★★☆☆☆ |

**Key observations:**

- **Manim Community Edition** is the clear front-runner for AI-driven animation. It has the richest Python API, the most active ecosystem of AI tooling built around it, MIT license, and Python is the language LLMs generate most reliably [5].
- **Remotion** stands out for cloud rendering (Lambda distributes rendering across many functions, rendering a 2-hour video in ~12 minutes [4]) and its React-based declarative model. Its license (BSL 1.1) is free for individuals and small businesses but requires a company license at scale.
- **Motion Canvas** is architecturally elegant (TypeScript generators, reactive signals, audio sync built-in [6]) but the TypeScript ecosystem is less mature for LLM code generation than Python.
- **Lottie** is not an animation *engine* but an animation *format* — important as a potential intermediate representation (see Section 3).

### 1.2 The Manim Ecosystem Dominance

Manim has emerged as the de facto backend for AI-to-animation research. Every major academic system in this space (TheoremExplainAgent, Manimator, PhysicsSolutionAgent, Generative Manim) uses Manim as its renderer [7][8][9][10]. This is not accidental:

- Python is LLMs' strongest code-generation language
- Manim's API is semantic (you write `Circle()`, `Transform()`, `Write()` — not pixel coordinates)
- The 3Blue1Brown videos provide a massive training signal — LLMs have seen thousands of Manim code examples
- MIT license allows unrestricted commercial use

However, Manim has limitations:

- **No built-in cloud rendering** — you must manage your own infrastructure
- **Heavy dependencies** — LaTeX, FFmpeg, Cairo/OpenGL
- **No audio sync primitives** — unlike Motion Canvas which has timeline markers and `waitUntil()` for voiceover sync [6]
- **No scene graph serialization** — you can't easily save/load/diff a scene as data; it's always code

---

## 2. Existing AI-to-Animation Pipelines

### 2.1 Academic Systems

**TheoremExplainAgent (TEA)** [7] — University of Waterloo / TIGER-AI-Lab (Feb 2025)

The most rigorous academic work in this space. Architecture:
- **Two-agent system**: A *planner agent* creates story plans and narration, a *coding agent* generates Manim Python scripts
- **Agentic RAG**: Retrieval at three stages — storyboard generation, technical implementation, and error correction
- **Retry loop**: Up to N=5 attempts with error feedback
- Best model: o3-mini achieves 93.8% success rate on their TheoremExplainBench (240 theorems)
- Key finding: agentless approaches fail to produce videos longer than 20 seconds; the planner agent is essential for coherent long-form content
- License: MIT

**Manimator** [8] (July 2025)

More general than TEA, accepts PDF/arXiv papers as input:
- **Three-stage pipeline**: (1) LLM generates structured Markdown scene description, (2) code-focused LLM converts to Manim Python, (3) Manim renders
- Uses different LLMs for different stages (gemini-2.0-flash for PDF analysis, DeepSeek-V3 for code generation — best price/performance ratio)
- Outperforms TEA baselines on Element Layout (0.853 vs 0.57-0.61)
- Currently lacks iterative refinement based on visual feedback
- License: Open-source (to be released)

**PhysicsSolutionAgent** [9] (Jan 2026)

Extends the TEA pattern to physics problems:
- **Planner-Coder architecture** with GPT-5 mini
- **Screenshot-driven feedback**: renders intermediate frames and feeds them back to the LLM for visual verification
- RAG over Manim documentation for code correctness
- Identifies "Manim code hallucinations" and "LaTeX rendering errors" as primary failure modes

**MoVer (Motion Verification)** [11] (Feb 2025)

A fundamentally different approach — instead of just generating code, MoVer introduces a **verification DSL** based on first-order logic that can check spatio-temporal properties of animations:
- Predicates for direction, timing, relative positioning of objects
- LLM generates both the animation AND a MoVer verification program
- Verification failures are fed back for iterative correction
- Without iteration: 58.8% success → with up to 50 iterations: 93.6% success
- This is the closest thing to a formal specification layer for animations

### 2.2 Commercial/Open-Source Tools

**Generative Manim** [10] — Open-source (generative-manim.vercel.app)

- Web app + API for text-to-Manim generation
- Multiple model backends (GPT-4o, fine-tuned GPT-3.5, Claude Sonnet)
- "Animo" — a companion video editor for LLM+Manim workflows
- Simple prompt → code → render pipeline (no intermediate scene description)
- License: Open-source

**AnimG** [12] — Commercial (animg.app)

- Browser-based, no local install
- "Spec-driven agentic flow" — generates a spec first, lets user align, then generates
- Free tier with limits, Pro for downloads
- Closest to a product, but opaque architecture

**Manim Agent Skills** [1][2][3] — Skills ecosystem (skills.sh, agentskills.io)

- Multiple community-maintained skills for Manim CE, ManimGL, and Motion Canvas
- Install with `npx skills add` — gives AI agents (Claude Code, Copilot, Cursor) structured knowledge about animation APIs
- This is infrastructure, not a product — but it's a critical piece of the puzzle for agent-controllable workflows

### 2.3 Pattern Analysis

Every successful system follows a variant of the same architectural pattern:

```
Natural Language → [Planning Agent] → Structured Scene Description → [Coding Agent] → Animation Code → [Renderer] → Video
                                                                          ↑
                                                                   [Error Feedback Loop]
```

The key differentiators between systems are:
1. **Whether there's a planning stage** (TEA/Manimator yes, Generative Manim no — big quality difference)
2. **Whether there's visual verification** (PhysicsSolutionAgent yes, others no)
3. **What the intermediate scene description looks like** (Markdown in Manimator, story plans in TEA, none in Generative Manim)
4. **How sophisticated the error feedback loop is** (MoVer's formal verification vs. simple retry)

---

## 3. Intermediate Representations and Formats

This is the hardest and most important design problem. The IR sits between natural language and renderer-specific code, and its design determines editability, portability, and agent-controllability.

### 3.1 Existing Animation Formats

**Lottie JSON** [13]

- JSON-based vector animation format, standardized by the Linux Foundation's Lottie Animation Community
- Structure mirrors After Effects internals: layers → shapes → transforms → keyframes
- Rich ecosystem: web/iOS/Android/React Native players, editors, converters
- JSON Schema available for validation and code generation
- Strengths: cross-platform, well-specified, JSON (agent-friendly)
- Weaknesses: designed for UI micro-interactions, not pedagogical animations; no concept of "explanation flow" or "mathematical objects"; After Effects-centric vocabulary

**SVG + SMIL / CSS Animations**

- W3C standards, browser-native
- SVG provides scene graph; SMIL/CSS provides animation
- MoVer [11] operates on SVG-based motion graphics specifically
- Strengths: web-native, inspectable, agent-editable
- Weaknesses: limited animation expressiveness, no audio sync, poor tooling for complex sequences

**Motion Canvas Scene Model** [6]

- TypeScript generator functions that yield animation steps
- Reactive signals for computed values
- Scene graph with layout primitives (like React's Flexbox)
- Timeline markers for audio sync
- Strengths: compositional, declarative-ish, audio-aware
- Weaknesses: TypeScript-specific, no serialization format

**Manim Scene Model** [5]

- Python classes with `construct()` methods
- Mobjects (mathematical objects) as the scene graph
- Animations as high-level transformations
- Strengths: most expressive for math, huge LLM training corpus
- Weaknesses: imperative (not declarizable), no standard serialization

### 3.2 The Missing Layer: A Pedagogical Scene Description Format

None of the existing formats capture what matters for educational animations:

- **Pedagogical structure**: What concept is being explained? In what order? Why?
- **Semantic objects**: Not just "circle at (3,4)" but "the unit circle representing sin(θ)"
- **Temporal narrative**: Not just keyframes but "first show X, then reveal Y to demonstrate Z"
- **Audio sync points**: Where does narration align with visual events?

The Manimator approach (structured Markdown) [8] is the closest — it generates:
- Topic identification
- Key concepts and mathematical formulas
- Scene-by-scene breakdown with visual element descriptions
- Pedagogical flow

A more formal version of this — a **Pedagogical Animation Description Language (PADL)** — could look like:

```json
{
  "topic": "Fourier Transform",
  "scenes": [
    {
      "id": "scene_01",
      "purpose": "Introduce the concept of frequency decomposition",
      "narration": "Any signal can be decomposed into...",
      "narration_sync_point": "start",
      "visual_elements": [
        {"id": "wave_composite", "type": "function_plot", "expression": "sin(x) + 0.5*sin(3x)"},
        {"id": "wave_components", "type": "function_group", "expressions": ["sin(x)", "0.5*sin(3x)"]}
      ],
      "animations": [
        {"action": "create", "target": "wave_composite", "style": "draw"},
        {"action": "wait", "duration": 1.5, "sync": "after_narration:frequency_decomposition"},
        {"action": "transform", "from": "wave_composite", "to": "wave_components", "style": "morph"}
      ]
    }
  ]
}
```

This is **the** architectural innovation opportunity. A well-designed IR here would:
- Be agent-readable and agent-writable (JSON/YAML)
- Be renderer-agnostic (compile to Manim, Motion Canvas, Remotion, or Lottie)
- Support diff/merge for collaborative editing
- Enable visual preview without full rendering
- Carry pedagogical metadata (for evaluation and search)

### 3.3 Design Recommendation

Build a three-layer representation:

1. **Narrative Layer** (high-level, human-editable) — Scene descriptions in structured Markdown or YAML, with pedagogical annotations. This is what the user and the LLM planner produce and iterate on.

2. **Scene Graph Layer** (mid-level, agent-editable) — A JSON schema defining objects, their properties, animation sequences, and sync points. Renderer-agnostic. Diffable. This is the SSOT.

3. **Render Code Layer** (low-level, generated) — Manim Python, Motion Canvas TypeScript, or Remotion React. Generated from the Scene Graph Layer by a code-generation agent. Disposable and regeneratable.

The MoVer verification DSL [11] could serve as a fourth layer — a **constraint specification** that sits alongside the Scene Graph and enables formal verification of the output.

---

## 4. Rendering Infrastructure and Cloud APIs

### 4.1 Self-Hosted Rendering

For Manim:
- Requires Python + FFmpeg + LaTeX + Cairo
- Docker containers are the standard approach (several projects provide Dockerfiles [14])
- No GPU required (Manim CE uses Cairo; ManimGL uses OpenGL but can render offscreen)
- Rendering is CPU-bound and parallelizable per-scene

For Motion Canvas:
- Node.js + FFmpeg
- Frame-by-frame export to image sequence, then FFmpeg stitching

### 4.2 Cloud Video Rendering APIs

These are relevant for the **final composition** stage (stitching animated segments with narration, transitions, titles):

| Service | Model | Pricing (approx) | Key Strength |
|---------|-------|-------------------|--------------|
| **Remotion Lambda** [4] | AWS Lambda distributed rendering | ~pennies per render | React-based, distributed, self-hosted on your AWS |
| **Shotstack** [15] | JSON → video API | $49/mo for 200 min (720p) | Timeline-based JSON editing, AI asset pipeline |
| **Creatomate** [16] | JSON → video API | Credit-based, similar range | Better template editor, auto-scaling durations |
| **Plainly** [17] | After Effects templates via API | Higher-end pricing | AE template rendering at scale |

**Recommendation**: For the structured animation segments, render locally or in Docker (Manim is fast enough). For final composition (adding narration audio, transitions between segments, titles), either use Remotion Lambda (if you want full control) or Shotstack's JSON API (if you want managed infrastructure). Shotstack's JSON edit-decision-list model is particularly agent-friendly [15].

---

## 5. Architecture Patterns for Agentic Animation Pipelines

### 5.1 The Canonical Pipeline

Based on analysis of all existing systems, the production architecture should be:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                │
│  Natural language input ←→ Visual preview ←→ Edit commands           │
└───────────────┬─────────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (MCP Server)                        │
│  Routes between planning, code gen, rendering, verification          │
└───────┬───────────┬───────────────┬────────────────┬────────────────┘
        │           │               │                │
┌───────▼───┐ ┌─────▼─────┐ ┌──────▼──────┐ ┌───────▼───────┐
│  PLANNER  │ │  CODER    │ │  RENDERER   │ │  VERIFIER     │
│  Agent    │ │  Agent    │ │  (Manim,    │ │  (MoVer-like  │
│  (LLM)   │ │  (LLM)    │ │  Remotion)  │ │  DSL checks)  │
│           │ │           │ │             │ │               │
│ NL → PADL│ │ PADL →    │ │ Code →      │ │ Video →       │
│ scene     │ │ Manim/TS  │ │ Video/Frames│ │ Pass/Fail +   │
│ description│ │ code      │ │             │ │ Error Report  │
└───────────┘ └───────────┘ └─────────────┘ └───────────────┘
```

### 5.2 The Edit/Feedback Loop

The most critical difference between a demo and a product is the **edit loop**. Current academic systems are one-shot: prompt → video. A real tool needs:

1. **Structural editing**: "Move the explanation of eigenvalues before the matrix multiplication scene"  
   → Operates on the Narrative Layer

2. **Visual editing**: "Make the circle bigger and change it to blue"  
   → Operates on the Scene Graph Layer

3. **Code-level editing**: "Use `FadeIn` instead of `Write` for the equation"  
   → Operates on the Render Code Layer

4. **Verification-driven editing**: "The arrow should point left, not right"  
   → Detected by MoVer-like verification, auto-corrected

Each edit level should be expressible in natural language AND in the appropriate structured format. The agent should route edits to the correct layer.

### 5.3 MCP Server Design

For agentic control, each major capability should be an MCP tool:

```
animation-pipeline/
├── tools/
│   ├── plan_scenes      # NL → structured scene description
│   ├── generate_code    # Scene description → renderer code
│   ├── render_scene     # Code → video/frames
│   ├── verify_animation # Video → verification report
│   ├── edit_scene       # Edit command → updated scene description
│   ├── preview_frame    # Scene + timestamp → static frame
│   ├── compose_video    # Scenes + narration → final video
│   └── list_templates   # Available animation patterns
├── resources/
│   ├── scene_schema     # JSON Schema for scene descriptions
│   ├── style_presets    # Visual style configurations
│   └── animation_library # Reusable animation patterns
```

This maps naturally to your `py2mcp` pattern — each tool is a Python function, exposed via FastMCP.

---

## 6. Known Hard Problems

### 6.1 Element Layout and Overlap

Every system reports this as a top failure mode [7][8][9]. LLMs struggle with spatial reasoning — they'll generate code where text overlaps, objects go off-screen, or layouts are cluttered. PhysicsSolutionAgent's screenshot-driven feedback [9] helps, but it's expensive (requires rendering intermediate frames and feeding them to a vision model).

**Mitigation**: Build a lightweight layout validator that checks bounding boxes before full rendering. The Scene Graph Layer should carry spatial constraints.

### 6.2 Manim Code Hallucinations

LLMs generate Manim API calls that don't exist, use deprecated syntax, or misunderstand parameter semantics [14]. This is especially problematic because Manim evolves rapidly and Manim CE vs ManimGL APIs diverge significantly.

**Mitigation**: RAG over current Manim documentation (as TEA does [7]), and use the Agent Skills [1] approach to inject correct API knowledge into the agent context. The `skill` package you're building could manage this directly.

### 6.3 Temporal Coherence

Animations need to flow — objects introduced in scene 1 should be consistent in scene 5. Current systems handle each scene somewhat independently, leading to visual discontinuities.

**Mitigation**: The Scene Graph Layer should maintain a persistent object registry across scenes. Objects have lifecycle states (created, visible, hidden, destroyed).

### 6.4 Audio-Visual Sync

Narration timing drives animation timing (or vice versa). This is architecturally hard because the audio track length isn't known until TTS generates it, but animation durations are coded ahead of time.

**Mitigation**: Motion Canvas solves this with timeline markers and `waitUntil()` [6]. For Manim, you'd need a post-sync step that adjusts `self.wait()` durations based on audio length. Alternatively, generate narration first, extract timestamps, then generate animations to fit.

---

## 7. Diagram-to-Animation as a Feeder Pipeline

Diagramming tools (Mermaid, PlantUML, D3, TikZ/PGF) produce structured visual assets that are excellent candidates for "still image animation" — applying Ken Burns, parallax, progressive reveal, and build-up effects to static diagrams.

This is a lighter-weight pipeline than full programmatic animation, but it covers a large percentage of educational content use cases (flowcharts, architecture diagrams, sequence diagrams, state machines). The key insight: these tools already produce **structured output** (SVG with semantic groups, or AST-like intermediate forms), which makes them much more agent-controllable than pixel-based tools.

For the roadmap: treat diagram-to-animation as a **plugin** in the architecture. The Scene Graph Layer should accept static diagram assets alongside programmatic animation scenes, and the Composer should handle transitions between them.

---

## 8. Market Gaps and Monetization Signals

### 8.1 Who's Building What

- **AnimG** [12] is the closest commercial product — browser-based, spec-driven, freemium. But it's Manim-only and early-stage.
- **Generative Manim** [10] is open-source infrastructure, not a product.
- **Shotstack** [15] and **Creatomate** [16] are general video automation platforms — they don't understand educational content or mathematical objects.
- **Synthesia**, **HeyGen**, **D-ID** are AI avatar platforms — talking heads, not structured animations.

### 8.2 The Gap

Nobody is building a **full-stack agentic educational video production tool** that:
- Accepts natural language or documents as input
- Produces 3Blue1Brown-quality structured animations (not pixel-generated video)
- Supports iterative editing via natural language
- Composes animation segments with narration and transitions
- Has cloud rendering for production use
- Exposes an MCP/API interface for agent integration

This is the gap. The academic pieces exist (TEA, Manimator, MoVer), the rendering infrastructure exists (Manim, Remotion Lambda), the agent plumbing exists (MCP, skills.sh, your `py2mcp`). What's missing is the **integration layer** — the IR, the orchestrator, the edit loop, and the product.

### 8.3 Monetization Angles

- **API/Platform**: Charge per render-minute (like Shotstack). Target: EdTech companies, online course platforms, YouTube educators.
- **Self-hosted + Pro**: Open-source the core engine, charge for cloud rendering and premium features (like Remotion's model).
- **Vertical SaaS**: "Video production for STEM educators" — bundle with narration (ElevenLabs/Kokoro), template libraries, and a no-code editor.

---

## 9. Recommended Roadmap

### Phase 1: Core IR and MCP Server (4-6 weeks)
- Design the Pedagogical Animation Description Language (PADL) JSON schema
- Build `py2mcp` tools for: `plan_scenes`, `generate_code`, `render_scene`
- Use Manim CE as the sole backend
- Simple prompt → plan → code → render pipeline (no edit loop yet)

### Phase 2: Verification and Edit Loop (4-6 weeks)
- Add MoVer-inspired verification (bounding box checks, timing validation)
- Implement the edit routing system (NL edit → correct layer)
- Add screenshot-driven feedback for visual QA
- Build `preview_frame` tool for quick visual checks without full rendering

### Phase 3: Composition and Audio (3-4 weeks)
- Integrate TTS (ElevenLabs API or open-source Kokoro/F5-TTS)
- Build `compose_video` tool (Remotion or FFmpeg-based stitching)
- Audio-visual sync via timeline markers
- Add diagram-to-animation plugin (Mermaid → animated SVG)

### Phase 4: Cloud and Product (4-6 weeks)
- Docker-based rendering service
- API endpoint (Shotstack-style JSON → video)
- Web UI for non-technical users
- Template library for common educational patterns

---

## REFERENCES

[1] [manim_skill (ManimCE + ManimGL Agent Skills)](https://github.com/adithya-s-k/manim_skill) — Agent skills for AI coding assistants, installable via skills.sh.

[2] [3b1b/manim (ManimGL)](https://github.com/3b1b/manim) — Original Manim by Grant Sanderson, OpenGL-based. MIT License. 85k+ stars.

[3] [Motion Canvas Skills](https://skills.sh/apoorvlathey/motion-canvas-skills/motion-canvas) — Agent skill for Motion Canvas TypeScript animation library.

[4] [Remotion Lambda](https://www.remotion.dev/lambda) — Distributed video rendering on AWS Lambda. BSL 1.1 license.

[5] [Manim Community Edition](https://www.manim.community/) — Community-maintained fork. MIT License. Comprehensive documentation.

[6] [Motion Canvas](https://motioncanvas.io/) — TypeScript library for programmatic animations with generator functions and audio sync. MIT License.

[7] Ku, M., Chong, T., Leung, J., Shah, K., Yu, A., & Chen, W. (2025). [TheoremExplainAgent: Towards Multimodal Explanations for LLM Theorem Understanding](https://arxiv.org/abs/2502.19400). arXiv:2502.19400. MIT License.

[8] [Manimator: Transforming Research Papers and Mathematical Concepts into Visual Explanations](https://arxiv.org/html/2507.14306v1) (July 2025). Uses DeepSeek-V3 for code generation, three-stage pipeline with structured Markdown IR.

[9] [PhysicsSolutionAgent](https://www.arxiv.org/pdf/2601.13453) (Jan 2026). Planner-Coder architecture with screenshot-driven feedback for physics education videos.

[10] [Generative Manim](https://github.com/marcelo-earth/generative-manim) — Open-source text-to-Manim-video tool. Multiple LLM backends.

[11] [MoVer: Motion Verification for Motion Graphics Animations](https://arxiv.org/html/2502.13372v1) (Feb 2025). First-order logic DSL for verifying spatio-temporal properties of animations. 93.6% success with iterative correction.

[12] [AnimG](https://animg.app/) — Commercial browser-based AI Manim animation generator with spec-driven agentic flow.

[13] [Lottie Animation Format Specification](https://lottie.github.io/lottie-spec/1.0.1/) — JSON-based vector animation format, standardized by the Lottie Animation Community / Linux Foundation.

[14] [manim-video-generator](https://github.com/rohitg00/manim-video-generator) — Event-driven Manim generation pipeline using Motia framework. Includes NLU classifier and scene composer.

[15] [Shotstack Video Editing API](https://shotstack.io/) — Cloud JSON-to-video rendering platform. Timeline-based editing, AI asset pipeline integration.

[16] [Creatomate](https://creatomate.com/) — Cloud video generation API with template editor and auto-scaling durations.

[17] [Plainly Videos - Best Video Editing APIs](https://www.plainlyvideos.com/blog/best-video-editing-api) — Comparative review of cloud video rendering APIs (March 2026).

[18] Ni, H. (2025). [Multi-Layered Visual Language: Bridging Human Thought, LLM Reasoning, and Animated Explanation](https://watchsound.medium.com/multi-layered-visual-language-bridging-human-thought-llm-reasoning-and-animated-explanation-27862d6a0d2d). Medium. Proposes semantic storyboarding and multi-layer architecture for LLM-driven animation.
