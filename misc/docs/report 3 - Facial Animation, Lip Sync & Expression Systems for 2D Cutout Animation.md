# Facial Animation, Lip Sync & Expression Systems for 2D Cutout Animation

**The automated lip sync pipeline for 2D cutout animation is technically mature enough to implement today, with Rhubarb Lip Sync and Montreal Forced Aligner forming the backbone of phoneme-to-viseme conversion, while Azure Speech SDK provides the strongest integrated TTS-to-viseme path.** The critical finding across this research is that **12–15 visemes represent the perceptual sweet spot** for stylized 2D characters — enough for convincing speech without diminishing returns. The largest gap in the ecosystem is not phoneme detection but co-articulation modeling and emotional modulation: every open-source tool outputs discrete viseme snapshots, but none blends between them with anticipatory motion or adjusts mouth shapes based on vocal intensity. This document provides the complete technical foundation — standards, tools, expression models, integration patterns, and architectural recommendations — to build a production-quality automated lip sync pipeline in Python (authoring) and JS/TS (rendering).

---

## Part 1: Viseme standards and the phoneme-to-viseme mapping problem

### The four dominant viseme sets

Four viseme standards dominate animation and speech technology, each optimized for different contexts:

**Preston Blair (10 shapes)** remains the industry standard for 2D cartoon animation since the 1940s. The set groups all English phonemes into 10 mouth positions: A/I (open), E (wide/spread), O (rounded open), U (puckered), C/D/G/K/N/R/S/Th/Y/Z (slightly parted teeth), F/V (labiodental), L (tongue visible), M/B/P (lips closed), W/Q (pursed), and Rest (neutral). Rhubarb Lip Sync uses an extended version with **9 active shapes** (A–H) plus X (silence), adding dedicated shapes for F/V and L sounds. This set prioritizes readability at small sizes and fast frame rates over phonetic accuracy.

**Microsoft SAPI / Azure visemes (22 IDs)** provide the most granular standard set. IDs 0–21 cover silence, 12 vowel/diphthong positions, and 10 consonant groups. Azure Speech SDK outputs these IDs with timestamps during TTS synthesis and optionally generates **SVG mouth animations** or **55-parameter 3D blend shapes** (ARKit-compatible) at 60 FPS. The 22-viseme set distinguishes diphthongs (AY, AW, OY) as separate visemes and separates the alveolar fricatives (S/Z) from postalveolar fricatives (SH/CH/JH/ZH) — distinctions invisible in simpler sets.

**Oculus/Meta OVR visemes (15 IDs)** derive directly from the MPEG-4 FAP standard (ISO/IEC 14496-2). With 14 visemes plus silence, this set is the default for VR avatars in VRChat, Ready Player Me, and Meta's social VR platforms. It maps closely to the MPEG-4 specification and supports interpolation between visemes via blending factors.

**MPEG-4 (14 + silence)** defines the ISO standard viseme set within its 68 Facial Animation Parameters. The Oculus set is a near-direct implementation. MPEG-4 visemes are designed for low-bitrate facial animation transmission and form the baseline for most real-time systems.

### How many visemes actually matter

Research converges on a clear hierarchy. **6–9 visemes** suffice for sketch-quality cartoon lip sync — the Preston Blair / Rhubarb range. Japanese anime typically uses only 5–6 shapes (A/I/U/E/O vowels plus closed). **12–15 visemes** hit the practical sweet spot: Bear & Harvey's comprehensive 2017 study [1] found that linguistically-motivated viseme sets in this range significantly outperformed both smaller and larger sets on visual speech recognition benchmarks. **20–22 visemes** add diphthong distinctions valuable for narration and high-fidelity TTS (the Microsoft/Azure level). Beyond 22, Mattheyses & Verhelst found that phoneme-level mapping (no grouping) gives the best synthesis results [2], but this contradicts Massaro's established position that "many phonemes are virtually indistinguishable by sight" [3]. Bernstein et al. (2015) partially resolved this debate by showing perceivers **can** discriminate phonemes within traditional viseme groups under controlled conditions [4], but **co-articulation quality matters more than viseme count** — smooth blending between 12 shapes looks better than snapping between 22.

### Complete English phoneme-to-viseme mapping

The table below maps all 39 General American English phonemes to a unified 16-group viseme set suitable for implementation. ARPAbet notation is used because Rhubarb, MFA, and CMU tools all use it internally.

#### Consonants

| ARPAbet | IPA | Example | Viseme | Mouth shape |
|---------|-----|---------|--------|-------------|
| P | p | **p**at | **PP** | Lips pressed together, released with burst |
| B | b | **b**at | **PP** | Lips pressed together (voiced) |
| M | m | **m**at | **PP** | Lips pressed, air through nose |
| F | f | **f**at | **FF** | Lower lip tucked under upper front teeth |
| V | v | **v**at | **FF** | Lower lip under upper teeth (voiced) |
| TH | θ | **th**in | **TH** | Tongue tip visible between teeth |
| DH | ð | **th**is | **TH** | Tongue between teeth (voiced) |
| T | t | **t**ip | **DD** | Tongue at alveolar ridge, lips parted |
| D | d | **d**ip | **DD** | Same as /t/ (voiced) |
| N | n | **n**ot | **nn** | Tongue tip at ridge, mouth open |
| S | s | **s**it | **SS** | Teeth close together, narrow slit |
| Z | z | **z**oo | **SS** | Same as /s/ (voiced) |
| SH | ʃ | **sh**e | **CH** | Lips funneled/protruded forward |
| ZH | ʒ | mea**s**ure | **CH** | Same funneled shape (voiced) |
| CH | tʃ | **ch**in | **CH** | Lips funneled, then released |
| JH | dʒ | **j**oy | **CH** | Same as /tʃ/ (voiced) |
| K | k | **c**at | **kk** | Back tongue raised; lips shaped by adjacent vowel |
| G | g | **g**o | **kk** | Same as /k/ (voiced) |
| NG | ŋ | si**ng** | **kk** | Back tongue up, lips neutral |
| L | l | **l**ip | **nn** | Tongue raised to ridge, mouth open |
| R | ɹ | **r**ed | **RR** | Lips slightly rounded, tongue retracted |
| W | w | **w**et | **W** | Lips tightly rounded/puckered |
| Y | j | **y**es | **I** | Lips spread, tongue raised |
| HH | h | **h**at | **H** | Mirrors the following vowel shape |

#### Vowels

| ARPAbet | IPA | Example | Viseme | Mouth shape |
|---------|-----|---------|--------|-------------|
| IY | iː | s**ee** | **I** | Lips spread wide, narrow opening |
| IH | ɪ | s**i**t | **I** | Slightly more open than /iː/ |
| EY | eɪ | s**ay** | **E** | Lips spread, mid-open |
| EH | ɛ | b**e**d | **E** | Moderately spread, more open |
| AE | æ | c**a**t | **aa** | Wide open, lips spread, jaw dropped |
| AA | ɑ | f**a**ther | **aa** | Wide open, jaw dropped, lips neutral |
| AH | ʌ | c**u**p | **aa** | Moderately open, lips relaxed |
| AX | ə | **a**bout | **aa** | Barely open, very relaxed (schwa) |
| AO | ɔ | c**au**ght | **O** | Lips slightly rounded, jaw open |
| OW | oʊ | g**o** | **O** | Lips rounded, medium opening |
| UH | ʊ | b**oo**k | **U** | Loosely rounded, small opening |
| UW | uː | f**oo**d | **U** | Tightly rounded/puckered |
| ER | ɝ | b**ir**d | **ER** | Slightly rounded with r-coloring |

#### Diphthongs

| ARPAbet | IPA | Example | Viseme | Mouth shape |
|---------|-----|---------|--------|-------------|
| AY | aɪ | b**uy** | **aa→I** | Open, glides to spread |
| AW | aʊ | c**ow** | **aa→U** | Open, glides to rounded |
| OY | ɔɪ | b**oy** | **O→I** | Rounded, glides to spread |

### Language extensibility

The English 15-viseme MPEG-4 base covers the most critical cross-language distinctions. Adding **3–5 additional visemes** handles most world languages: rounded front vowels (/y/, /ø/, /œ/) for French, German, and Turkish; alveolar trills (/r/) for Spanish, Italian, and Russian; and pharyngeal fricatives (/ħ/, /ʕ/) for Arabic. A **20-viseme universal set** covers the vast majority of languages. Microsoft Azure already maps its 22 viseme IDs across multiple locales (en-US, fr-FR, de-DE, ja-JP, zh-CN, and others), maintaining the same ID framework with language-specific phoneme mappings. Japanese requires only 6–9 visemes due to its 5-vowel system and limited consonant contrasts.

---

## Part 2: Audio-to-viseme pipeline tools evaluated

### Rhubarb Lip Sync — the 2D animation workhorse

Rhubarb Lip Sync [5] is a C++ command-line tool (MIT license) purpose-built for 2D animation lip sync. It analyzes audio files and outputs timed mouth shape sequences in JSON, TSV, XML, or DAT formats. Internally it runs **PocketSphinx** for English speech recognition or a language-independent phonetic energy analyzer. Version 1.13.0 is the current stable release; a v2 rewrite incorporating MFA for multilingual support is in proof-of-concept but unreleased.

**Output format** (JSON): Each entry contains `start` (seconds), `end` (seconds), and `value` (letter A–H or X for silence). The `--extendedShapes` flag controls which of the 3 extended shapes (G for F/V, H for L, X for idle) to use. The `--dialogFile` option provides the transcript and significantly improves accuracy. Python integration works via subprocess: `rhubarb -f json -o output.json input.wav`. A **WebAssembly port** (rhubarb-lip-sync-wasm, published June 2025 on npm) enables browser-native operation with a TypeScript API.

**Quality assessment**: Rhubarb produces good results for English dialogue with transcript provided. It implements artistic timing principles — anticipating vowels, suppressing jittery rapid movements, and prioritizing perceptually important sounds. Known limitations include English-only word-based recognition, degraded performance with background noise or music, and no true co-articulation modeling. The viseme set is hardcoded (not customizable in v1). Maintenance is low — the repo has open issues from 2024–2025 without maintainer response, though the codebase is stable.

### Montreal Forced Aligner — gold standard for phoneme boundaries

MFA [6] (MIT license, Python/Kaldi, v3.3.9 as of February 2026) is the academic-grade forced alignment system. It produces **phone-level time alignments at 10ms resolution** — the highest boundary precision available in open-source tools. MFA uses Kaldi's GMM-HMM framework: words are mapped to phonemes via pronunciation dictionaries, triphone acoustic models are built, and Viterbi decoding finds optimal state sequences. Output is Praat TextGrid files with separate word and phone tiers.

Research by Rousso et al. (2024) shows MFA outperforms WhisperX and MMS on word-level forced alignment, with approximately **47% of boundaries within 10ms of ground truth** and mean boundary error of ~19ms. Pretrained acoustic models and G2P (grapheme-to-phoneme) models are available for **100+ languages** via `mfa model download`. Installation requires conda (`conda install -c conda-forge montreal-forced-aligner`), and both CLI and Python API are available. MFA is actively maintained with monthly/quarterly releases and is being presented at Interspeech 2025.

### WhisperX — transcription plus alignment in one pass

WhisperX [7] (BSD-2-Clause) adds accurate word-level timestamps to OpenAI's Whisper via wav2vec2 forced alignment plus VAD preprocessing. The pipeline runs: pyannote VAD segments audio → Whisper transcribes with batch inference (12× speedup over base Whisper) → wav2vec2 CTC models align at character level → optional speaker diarization. Output includes word-level timestamps with confidence scores. WhisperX operates at character rather than phoneme level for timing; deriving phoneme boundaries requires combining with `phonemizer` and proportional distribution.

### Cloud APIs with direct viseme output

**Azure Speech SDK** is the strongest integrated solution. During TTS synthesis, it fires viseme events containing: **22 viseme IDs with timestamps** (100-nanosecond resolution), optional **SVG mouth animation** XML (en-US only), or **55-parameter 3D blend shapes** (ARKit-compatible, 60 FPS). The SDK is event-based — a `viseme_received` callback fires per viseme during `speak_ssml_async()`. Pricing is **~$15–16 per million characters** (neural TTS); viseme events add no extra cost. Python SDK is pip-installable (`azure-cognitiveservices-speech`). The key limitation is that viseme output works only via the SDK, not the REST API.

**Amazon Polly** offers the second-best direct viseme path via Speech Marks. It outputs X-SAMPA-based viseme labels with millisecond timestamps as line-delimited JSON. However, speech marks require a **separate API call** from audio synthesis — two calls for one utterance. Standard engine pricing is **$4 per million characters** (the cheapest option with visemes). The generative engine does not support speech marks.

**ElevenLabs** provides **character-level timestamps** via its `/with-timestamps` endpoint — more granular than word-level but not phoneme-level. No native viseme or phoneme output; characters must be mapped to phonemes via a G2P dictionary. Voice quality is among the best available. Pricing ranges from $5/month (30K credits) to $330/month (2M credits).

**Google Cloud TTS/STT** offers only word-level timing. Google TTS supports SSML `<mark>` tags for timepoints (still in v1beta1, not GA). Google STT provides word-level time offsets. Neither outputs phonemes or visemes.

### Essential supporting tools

**phonemizer** [8] (GPL-3, Python, v3.3.0) converts text to IPA phoneme sequences via espeak-ng or Festival backends. It supports **100+ languages** through espeak-ng. Critical limitation: text-to-phonemes only — no timing information. It serves as the glue component between word timestamps and viseme mapping.

**PocketSphinx** (BSD, C/Python, v5.0.4, January 2025) provides lightweight phoneme alignment via `phone_align` mode. Its maintainer states "active development has largely ceased and it has become very, very far from the state of the art," but it remains useful for embedded deployment and is the engine inside Rhubarb.

**NVIDIA NeMo Forced Aligner** (Apache 2.0) uses CTC ASR models (FastConformer) for forced alignment across 14+ languages. Claims best word alignment accuracy and speed versus competitors. Actively maintained as part of the NeMo ecosystem.

**Gentle** (MIT) was once the easiest forced aligner but is **effectively dead** — unmaintained since ~2020, web demo offline, no updates. Use MFA instead.

**Papagayo-NG** (GPL) is a GUI lip sync editor — not suitable for automated pipelines. Scriptability is minimal. Maintenance is sporadic.

### Pipeline approach comparison

| Approach | Simplicity | Accuracy | Cost | Best for |
|----------|-----------|----------|------|----------|
| **Rhubarb on any audio** | Highest | Good (English) | Free | Rapid prototyping, 2D animation |
| **Azure TTS + viseme events** | High | Very good | $15/1M chars | Production with synthetic speech |
| **Any TTS + MFA alignment** | Medium | Best | Free (local TTS) | Maximum precision, multilingual |
| **Polly TTS + speech marks** | High | Good | $4–16/1M chars | Cost-sensitive production |
| **Recorded audio + MFA** | Medium | Best | Free | Voice actor recordings |

---

## Part 3: Expression and emotion systems for 2D faces

### Which FACS Action Units matter for cartoons

The full FACS system defines 44 Action Units, but 2D cartoon faces need only **10–12 key AUs** to cover the full emotional range. The essential subset:

- **AU1 (inner brow raiser)** and **AU2 (outer brow raiser)**: Together they create surprise; AU1 alone signals sadness or worry
- **AU4 (brow lowerer)**: Anger, concentration, and sadness — the single most expressive brow action
- **AU5 (upper lid raiser)**: Wide eyes for surprise, fear, and intensity
- **AU6 (cheek raiser)**: Distinguishes genuine (Duchenne) smiles from posed smiles — pushes cheeks up, narrows eyes from below
- **AU12 (lip corner puller)**: The smile — pulls mouth corners up and back
- **AU15 (lip corner depressor)**: The frown — pulls mouth corners down
- **AU20 (lip stretcher)**: Horizontal lip stretch for fear
- **AU25 (lips part)** and **AU26 (jaw drop)**: Mouth opening for speech and surprise
- **AU9 (nose wrinkler)**: Disgust — the only nose-specific AU that matters for 2D

Apple's ARKit 52 blend shapes map cleanly to these AUs: `browInnerUp` ≈ AU1, `browDownLeft/Right` ≈ AU4, `browOuterUpLeft/Right` ≈ AU2, `eyeWideLeft/Right` ≈ AU5, `mouthSmileLeft/Right` ≈ AU12, `mouthFrownLeft/Right` ≈ AU15, `jawOpen` ≈ AU26, and `noseSneerLeft/Right` ≈ AU9. For 2D cutout characters, a practical parameter set of **~15 values** captures the full expression space.

### Live2D, VTuber, and Rive expression models

**Live2D Cubism** uses a parametric deformation model with standardized parameter IDs. The key facial parameters include `ParamEyeLOpen/ROpen` (0–1, eye open/close), `ParamEyeLSmile/RSmile` (0–1, smiley eye deformation), `ParamBrowLY/RY` (-1 to 1, brow height), `ParamBrowLAngle/RAngle` (-1 to 1, angry to raised), `ParamMouthForm` (-1 to 1, frown to smile), `ParamMouthOpenY` (0–1, open/close), and `ParamCheek` (0–1, blush). Expressions are applied as **additive, multiplicative, or overwrite** operations on base motion.

**VTube Studio** maps face tracking inputs to Live2D parameters. Core inputs include `MouthSmile`, `MouthOpen`, `Brows`, `EyeOpenLeft/Right`, and gaze parameters. On iOS with ARKit ("Perfect Sync"), all 52 blend shapes are available as individual inputs. Voice-based lip sync maps to 5 vowel shapes: `VoiceA`, `VoiceI`, `VoiceU`, `VoiceE`, `VoiceO`.

**Rive** handles expressions through its state machine — designers create timeline animations for expression states, connected by transitions with configurable blend durations. Number and Boolean inputs drive state changes programmatically. Duolingo's production implementation uses Rive state machines for lip sync, idle behaviors, and reaction states simultaneously across multiple layers.

### Emotion-to-expression mapping table

The following mapping is derived from EMFACS prototypes and provides directly implementable parameter values (0.0–1.0 scale):

| Parameter | Neutral | Happy | Sad | Angry | Surprised | Disgusted | Fearful |
|-----------|---------|-------|-----|-------|-----------|-----------|---------|
| BrowHeight | 0.5 | 0.5 | 0.6 | 0.2 | 0.9 | 0.3 | 0.7 |
| BrowFurrow | 0.0 | 0.0 | 0.5 | 0.9 | 0.0 | 0.4 | 0.6 |
| EyeOpenness | 0.7 | 0.6 | 0.5 | 0.8 | 1.0 | 0.5 | 1.0 |
| EyeSquint | 0.0 | 0.5 | 0.0 | 0.4 | 0.0 | 0.3 | 0.0 |
| MouthSmile | 0.0 | 0.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| MouthFrown | 0.0 | 0.0 | 0.7 | 0.3 | 0.0 | 0.3 | 0.0 |
| MouthOpen | 0.0 | 0.3 | 0.1 | 0.1 | 0.8 | 0.2 | 0.4 |
| LipStretch | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.7 |
| NoseWrinkle | 0.0 | 0.0 | 0.0 | 0.1 | 0.0 | 0.8 | 0.0 |

For compound emotions (happily surprised, sadly angry), parameter values interpolate between constituent emotions using Russell's circumplex model — mapping valence (negative → positive) and arousal (calm → excited) to blended expression parameter values.

### Text-to-emotion detection tools

The best available model for driving animation from dialogue text is **SamLowe/roberta-base-go_emotions** on HuggingFace — a RoBERTa model trained on Google's GoEmotions dataset (58K Reddit comments, 28 emotion categories including neutral). It outputs multi-label probabilities suitable as intensity multipliers for expression parameters. For the animation pipeline, the 28 GoEmotions categories map to 7 expression states: joy/amusement/love → Happy; sadness/grief/disappointment → Sad; anger/annoyance → Angry; surprise/realization → Surprised; disgust → Disgusted; fear/nervousness → Fearful; neutral → Neutral. For lightweight deployment, **mkpvishnu/miniLM-go_Emotions** at ~90MB provides 9-class detection suitable for constrained environments.

### Prosody drives expression from speech

Speech audio features map predictably to facial expression parameters. **Pitch (F0)** extracted via `librosa.pyin()` correlates with brow height — higher pitch drives eyebrows up (surprise/excitement), lower pitch down (sadness/calm). **Energy (RMS)** drives mouth openness and eye intensity — louder speech means wider eyes and more emphatic mouth shapes. **Pitch variability** (standard deviation of F0) acts as an expression intensity multiplier — high variability amplifies all expression parameters. **Spectral centroid** correlates with smile — brighter voice timbre maps to positive valence.

The recommended extraction stack is **openSMILE** (eGeMAPS feature set, 88 features at ~10ms windows) for comprehensive prosodic analysis, or **librosa** for simpler pitch/energy extraction. Pre-trained speech emotion recognition models — fine-tuned Wav2Vec 2.0 or HuBERT on RAVDESS/IEMOCAP datasets — achieve **86–96% accuracy** on acted emotional speech. SpeechBrain provides open-source SER recipes.

---

## Part 4: Integration architecture and the timing problem

### The complete pipeline from text to animated mouth

```
TEXT SCRIPT
    │
    ├─── [Text-to-Emotion] ──→ emotion labels + intensity
    │         (GoEmotions model)
    │
    ▼
TTS ENGINE (Azure / ElevenLabs / Piper / Coqui)
    │
    ├─── Audio file (.wav)
    │         │
    │         ├─── [Rhubarb CLI] ──→ Mouth cues JSON (shape + time)
    │         │         OR
    │         ├─── [MFA] ──→ TextGrid (phoneme boundaries at 10ms)
    │         │         │
    │         │         └─── [Phoneme→Viseme Map] ──→ Viseme sequence
    │         │
    │         └─── [Prosody Extraction] ──→ pitch/energy curves
    │                   (openSMILE / librosa)
    │
    └─── Viseme events (Azure SDK direct)
              │
              ▼
    ANIMATION DATA GENERATOR (Python)
    │
    ├─── Viseme keyframes with co-articulation blending
    ├─── Expression keyframes (emotion + prosody-driven)
    ├─── Audio sync metadata
    │
    ▼
    ANIMATION JSON (custom Spine-inspired format)
    │
    ▼
    JS/TS RENDERER (PixiJS v8 + GSAP)
    │
    ├─── Layer 0: Base pose
    ├─── Layer 1: Idle behaviors (blink, breathe)
    ├─── Layer 2: Lip sync (mouth slot attachment swap / sprite swap)
    ├─── Layer 3: Emotion (eyes, brows — additive override)
    │
    └─── Audio playback (Web Audio API, master clock)
```

### How existing tools connect audio to character rigs

**Spine 2D** pre-bakes lip sync into animations as slot attachment timeline keyframes. A `mouth` slot contains image attachments (`mouth_a` through `mouth_h`, `mouth_x`) mapped to Rhubarb shapes. Rhubarb generates timing, which is written directly into the `.json` animation file. At runtime, the Spine runtime simply plays the animation — no real-time audio analysis occurs.

```json
"animations": {
  "say_hello": {
    "slots": {
      "mouth": {
        "attachment": [
          { "time": 0.00, "name": "mouth_x" },
          { "time": 0.05, "name": "mouth_d" },
          { "time": 0.27, "name": "mouth_c" },
          { "time": 0.31, "name": "mouth_b" },
          { "time": 0.43, "name": "mouth_x" }
        ]
      }
    }
  }
}
```

**Live2D** takes a parametric approach: basic lip sync maps audio RMS volume (0–1) to `ParamMouthOpenY` via `addParameterValue()` with a 0.8 weight. The advanced MotionSync feature converts audio to A/I/U/E/O vowel visemes and blends corresponding parameter shapes. All animation sources (lip sync, blink, emotion) compose through the same additive parameter system.

**Adobe Character Animator** runs real-time ML-based viseme classification from microphone input via Adobe Sensei, detecting 11 audio-driven visemes. It also supports offline processing via "Compute Lip Sync Take from Scene Audio and Transcript" for improved accuracy.

**Rive** uses state machines with programmable inputs — each viseme is a timeline animation state, transitions are set to **~50ms mix duration** for rapid speech, and runtime code drives a `viseme` Number Input from external phoneme data. Duolingo's production system demonstrates this pattern at scale.

### Time-based sync and drift correction

The user's web-based renderer faces a fundamental sync challenge: `requestAnimationFrame` does not guarantee consistent frame timing, while audio playback via the Web Audio API runs on its own clock. The solution is **audio-as-master-clock** — always derive animation time from `audioElement.currentTime` or `AudioContext.currentTime` rather than accumulating `deltaTime`:

```javascript
function animate() {
  const audioTime = audioElement.currentTime;
  const viseme = findVisemeAtTime(visemeData, audioTime);
  updateMouthShape(viseme);
  requestAnimationFrame(animate);
}
```

Human perception is sensitive to audio-visual delays as small as **40ms**. Traditional animation practice calls for lip sync to be **2 frames ahead** of audio — mouth shapes should anticipate sound. Rhubarb's output already incorporates this anticipatory timing. For the user's pipeline, applying a global offset of **−80 to −90ms** to viseme timestamps compensates for rendering latency and produces the illusion of natural speech.

When phonemes are shorter than a frame (~33ms at 30 FPS, ~42ms at 24 FPS), Rhubarb filters them as noise — any prediction that doesn't persist across 3 consecutive internal samples is suppressed. Minimum viseme duration should be **~40ms** (one frame at 24 FPS).

### Co-articulation: where quality is made

Co-articulation — the blending of adjacent phonemes — separates good lip sync from great. **Anticipatory co-articulation** causes the mouth to begin forming the next sound **40–120ms before acoustic onset**. When saying "cool" versus "key," the same /k/ produces visibly different mouth shapes because the lips pre-shape for the upcoming vowel.

The classic **Cohen & Massaro dominance model** [9] uses overlapping exponential decay functions: each viseme has an inherent dominance strength (θ) and the blended viseme at time t is the weighted sum normalized by total dominance. Bilabials (/m/, /b/, /p/) have the highest dominance — lips must close regardless of neighbors. Rounded vowels (/o/, /u/) have high dominance — lip rounding persists into adjacent consonants. Tongue-only phonemes (/l/, /n/, /t/, /d/) have low visual dominance and are heavily influenced by neighbors.

The JALI model [10] (Edwards et al., SIGGRAPH 2016) maps each phoneme to a 2D "viseme field" with independent jaw (JA) and lip (LI) axes. Audio volume drives articulation intensity — louder speech produces stronger parameter values. Default onset/offset is **120ms** (150ms for lip protrusion phonemes), and bilabial closure constraints are enforced as hard rules. Viseme apex timing occurs at approximately **75% through the phoneme duration** based on articulatory muscle studies (Charalambous et al. 2019).

Practical transition parameters for implementation:

- **Normal speech transitions**: 80–120ms, cubic ease-in-out
- **Fast speech**: 30–60ms, linear or slight ease
- **Plosive release** (/p/, /b/): 20–40ms onset, near-instantaneous
- **Sustained vowels**: 150–250ms hold, slow ease-out
- **Noise filter threshold**: discard any viseme shorter than 40ms

### Layered expression: composing mouth and face

The standard architecture separates animation into layers with region masks:

```
Layer 3: Emotion (eyes + brows)    → Mask: upper face    → Override/Additive
Layer 2: Lip Sync (mouth + jaw)    → Mask: lower face    → Override
Layer 1: Idle (blink, breathe)     → Mask: full body     → Additive, weight 0.3
Layer 0: Base Pose                 → Mask: full body     → Base
```

**Override blending** replaces lower-layer values for masked properties — lip sync overrides the mouth portion of any base or idle animation. **Additive blending** stores animation as deltas from a reference pose, added on top of already-evaluated layers — used for breathing overlays and micro-expressions. The formula: `finalValue = basePose + (additivePose - referencePose) × weight`.

Live2D handles this elegantly: every animation source calls `addParameterValue(paramId, value, weight)` on the model — eye blink with weight 1.0, lip sync with weight 0.8, and emotion with weight 0.6 all compose additively. The weight parameter controls how much each source influences the final value. Conflicts (e.g., "sad" expression pulling mouth corners down while a viseme wants mouth open) resolve through the weight hierarchy — lip sync on the mouth region should have higher weight than emotion on the mouth, but emotion should dominate eyes and brows.

### Recommended animation data format

```json
{
  "version": "1.0",
  "audio": "dialog_001.wav",
  "duration": 2.5,
  "visemes": [
    {
      "time": 0.00, "duration": 0.05, "shape": "X",
      "intensity": 0.0,
      "blend": { "easeIn": 0.02, "easeOut": 0.02 }
    },
    {
      "time": 0.05, "duration": 0.22, "shape": "D",
      "intensity": 0.9,
      "blend": {
        "easeIn": 0.04, "easeOut": 0.06,
        "curve": [0.25, 0.1, 0.25, 1.0]
      }
    }
  ],
  "emotions": [
    { "time": 0.0, "type": "neutral", "intensity": 1.0 },
    { "time": 1.2, "type": "happy", "intensity": 0.6, "transition": 0.3 }
  ],
  "prosody": [
    { "time": 0.0, "pitch": 0.5, "energy": 0.3 },
    { "time": 0.1, "pitch": 0.7, "energy": 0.6 }
  ]
}
```

This format separates viseme, emotion, and prosody tracks — the renderer composites them through the layer system. Spine's convention of time-in-seconds and Bézier curve parameters (`[cx1, cy1, cx2, cy2]`) provides proven interpolation.

---

## Part 5: What's hard, what's new, and where the opportunity lies

### The unsolved problems in automated 2D lip sync

**Co-articulation remains the critical quality gap.** Every open-source tool outputs discrete viseme snapshots without modeling how the mouth transitions between them. Rhubarb has basic anticipatory timing but no true co-articulation model. The JALI system (2016) formalized co-articulation for 3D animation but has never been implemented in an open-source 2D tool. AI-generated lip sync typically exhibits a consistent **60–100ms delay on labial consonants** — the hallmark of non-anticipatory mapping.

**Emotional modulation of mouth shapes** is entirely absent from open-source tools. The same phoneme looks visually different when shouting versus whispering — jaw drops more, lip tension changes, mouth opening width varies. VisemeNet [11] (Zhou et al., 2018) addressed this by extracting speech style from facial landmarks, but this approach has never been productized.

**Non-speech vocalizations** — laughs, sighs, grunts, breathing — are poorly handled. Rhubarb detects non-speech segments and assigns neutral mouth positions, but no system generates expressive mouth shapes for these automatically. Professional animators hand-key laugh cycles and sighs.

**Style consistency across art styles** is a recognized gap. Aneja & Li (2019) [12] found that different animators prefer different visemes and articulation levels for identical audio — "A2's relatively low overall transition count suggests the animator prefers a smoother, less articulated style." No system adapts lip sync output to match an art style.

### AI talking heads: impressive but inapplicable to 2D cutout

The 2024–2026 explosion of neural talking head models — **LatentSync** (ByteDance, diffusion-based, December 2024), **EMO** (Alibaba, audio→video without intermediate representations), **Hallo** (Fudan University, three generations through December 2024), **MuseTalk** (Tencent, real-time 30+ FPS latent-space inpainting) — produces impressive results for photorealistic faces. But **almost none are applicable to stylized 2D cutout characters** because they all output pixel data (video frames), not discrete viseme or parameter data.

The systems that **do** output usable parameter data are:

- **NVIDIA Audio2Face-3D** (open-sourced 2025): Outputs **52 ARKit blendshapes at 30 FPS** via gRPC streaming. A 180M-parameter transformer + diffusion model. Could be mapped to 2D mouth shapes via a learned or rule-based mapping layer. This is the most promising bridge between AI quality and 2D puppet animation.
- **Azure Speech SDK**: 22 viseme IDs + SVGs + blend shapes, directly from TTS
- **Rhubarb + WASM**: Discrete viseme letters, now runnable in-browser
- **HeadTTS** (met4citizen, 2025): Free neural TTS with integrated viseme output, running in-browser via WebGPU/WASM

### The professional-to-open-source gap

Toon Boom Harmony's auto lip sync analyzes audio waveforms and maps detected phonemes to 8 standard mouth shapes (A–H) — functionally similar to Rhubarb but integrated into a $25–117/month professional animation suite. Adobe Character Animator provides real-time webcam-driven lip sync suitable for live broadcasts (used in The Late Show with Stephen Colbert). Neither offers co-articulation, emotional modulation, or style adaptation.

The gap between professional and open-source tools is narrower than expected in raw phoneme detection but wide in **integration and refinement**: professional tools wrap lip sync in polished editing workflows, while open-source tools require custom scripting at every step. Aneja & Li's landmark finding is encouraging: their LSTM model for real-time 2D lip sync "was significantly preferred over all commercial tools, including offline methods" in human judgment experiments, using only 12 visemes and ~13 minutes of training data.

### Key academic work on 2D cartoon lip sync

The most directly relevant papers for the user's system:

**Aneja & Li (2019) [12]** — "Real-Time Lip Sync for Live 2D Animation." An LSTM converting streaming audio to 12 discrete visemes for 2D characters at <200ms latency. Achieved **64–67% per-frame viseme accuracy** and outperformed Character Animator and Toon Boom in human preference tests. Used dynamic time warping for data augmentation, reducing training data requirements to ~13 minutes of hand-animated lip sync. The closest published work to the user's use case.

**Edwards et al. (2016) [10]** — "JALI: An Animator-Centric Viseme Model for Expressive Lip Synchronization" (SIGGRAPH). Defines the 2D viseme field (jaw × lip action), procedural co-articulation from transcript + audio features, and intensity-aware articulation. The theoretical foundation for quality lip sync.

**Zhou et al. (2018) [11]** — "VisemeNet: Audio-Driven Animator-Centric Speech Animation" (SIGGRAPH). A 3-stage LSTM outputting viseme curves + co-articulation parameters directly from audio, capturing speech style differences.

**Furukawa et al. (2018) [13]** — "Voice Animator: Automatic Lip-Synching in Limited Animation by Audio." Specifically targets limited animation style (anime/cartoon), following standard cartoon production workflow. Language-independent approach suitable for dubbing.

**Bao et al. (2023) [14]** — "Learning Audio-Driven Viseme Dynamics." Phoneme-guided viseme curve extraction producing artist-friendly blendshape weights. Multilingual via pretrained audio features.

### What would make this system notably better

The user's Python+JS/TS pipeline has a clear opportunity to fill the gap between Rhubarb (good but basic, English-only, no co-articulation or emotion) and professional tools ($25–117/month, closed-source, manual cleanup required). Five specific differentiators:

1. **Co-articulation layer**: Implement the Cohen-Massaro dominance model as post-processing on Rhubarb/MFA output — apply exponential blending between adjacent visemes with dominance weights per viseme type, enforce bilabial closure constraints, and shift viseme onsets by −80ms for anticipation. This alone would surpass every open-source alternative.

2. **Intensity modulation from prosody**: Extract pitch and energy from audio via librosa, normalize to 0–1, and use them as multipliers on viseme openness and expression parameters. Louder speech → wider mouth opening; higher pitch → raised brows.

3. **Configurable viseme sets**: Allow artists to define 6–20 mouth shapes per character and map them to the canonical viseme groups. The system should output shape IDs referencing the artist's custom set, not hardcoded Rhubarb letters.

4. **NVIDIA Audio2Face bridge**: Now that Audio2Face is open-source, its 52-blendshape output could be reduced to 2D mouth shapes via a mapping layer (e.g., `jawOpen` + `mouthFunnel` + `mouthPucker` → select from viseme set). This would bring state-of-art neural lip sync quality to 2D cutout animation.

5. **Progressive refinement**: The pipeline should output lip sync at three quality tiers — Tier 1 (Rhubarb: instant, rough), Tier 2 (MFA-aligned with co-articulation post-processing: higher quality), Tier 3 (MFA + emotion + prosody modulation: production quality). Each tier builds on the previous, enabling rough-cut review before investing in refinement.

---

## Conclusion

The 2D cutout lip sync pipeline is implementable today with mature, well-documented tools. **Rhubarb Lip Sync provides the fastest path to working lip sync** — a single CLI call produces timed mouth shapes in JSON. **MFA delivers the most accurate phoneme boundaries** at 10ms resolution across 100+ languages. **Azure Speech SDK offers the tightest TTS-to-viseme integration**, eliminating the separate alignment step entirely. The phoneme-to-viseme mapping is a solved problem at 12–15 visemes; the complete ARPAbet mapping table in this document can be implemented directly as a lookup dictionary.

The real frontier is not detection but synthesis quality. Co-articulation, emotional modulation, and style adaptation remain the unsolved problems where manual intervention still outperforms automation. The JALI and VisemeNet papers provide proven approaches to co-articulation and intensity-aware visemes, but neither has been implemented in an open-source 2D tool — this is the largest gap and the clearest opportunity. NVIDIA's open-sourcing of Audio2Face in 2025 creates a new path: neural lip sync quality outputting animation parameters rather than pixels, bridgeable to 2D cutout characters through a blendshape-to-viseme mapping layer.

The progressive quality strategy — rough Rhubarb output first, MFA-refined alignment second, prosody and emotion modulation third — aligns perfectly with the user's LLM+toolchain architecture. Each refinement tier is independently valuable, and the entire pipeline can run without manual keyframing.

---

## References

[1] Bear, H. L. & Harvey, R. W. "Phoneme-to-viseme mappings: the good, the bad, and the ugly." [Speech Communication, 2017](https://www.sciencedirect.com/science/article/pii/S0167639317300869)

[2] Mattheyses, W. & Verhelst, W. "Audiovisual speech synthesis: An overview of the state-of-the-art." [Speech Communication, 2015](https://www.sciencedirect.com/science/article/pii/S0167639314000697)

[3] Massaro, D. W. et al. "Perception of asynchronous and conflicting visual and auditory speech." [JASA, 1996](https://asa.scitation.org/doi/10.1121/1.414955)

[4] Bernstein, L. E. et al. "Visual phonetic processing: A high-density ERP study." [Frontiers in Psychology, 2015](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4499841/)

[5] Wolf, D. S. "Rhubarb Lip Sync." [GitHub Repository](https://github.com/DanielSWolf/rhubarb-lip-sync)

[6] McAuliffe, M. et al. "Montreal Forced Aligner: Trainable Text-Speech Alignment Using Kaldi." [Interspeech, 2017](https://montreal-forced-aligner.readthedocs.io/)

[7] Bain, M. et al. "WhisperX: Time-Accurate Speech Transcription of Long-Form Audio." [Interspeech, 2023](https://github.com/m-bain/whisperX)

[8] Bernard, M. & Titeux, H. "Phonemizer: Text to Phones Transcription for Multiple Languages in Python." [JOSS, 2021](https://github.com/bootphon/phonemizer)

[9] Cohen, M. M. & Massaro, D. W. "Modeling coarticulation in synthetic visual speech." [Models and Techniques in Computer Animation, Springer, 1993](https://link.springer.com/chapter/10.1007/978-4-431-66911-1_13)

[10] Edwards, P. et al. "JALI: An Animator-Centric Viseme Model for Expressive Lip Synchronization." [ACM SIGGRAPH, 2016](https://dgp.toronto.edu/~elf/JALISIG16.pdf)

[11] Zhou, Y. et al. "VisemeNet: Audio-Driven Animator-Centric Speech Animation." [ACM SIGGRAPH / TOG, 2018](https://dl.acm.org/doi/10.1145/3197517.3201292)

[12] Aneja, D. & Li, W. "Real-Time Lip Sync for Live 2D Animation." [arXiv:1910.08685, 2019](https://arxiv.org/abs/1910.08685)

[13] Furukawa, S. et al. "Voice Animator: Automatic Lip-Synching in Limited Animation by Audio." [ACE 2017, Springer](https://link.springer.com/chapter/10.1007/978-3-319-76270-8_12)

[14] Bao, F. et al. "Learning Audio-Driven Viseme Dynamics for 3D Face Animation." [arXiv:2301.06059, 2023](https://arxiv.org/abs/2301.06059)

[15] Microsoft. "Get facial position with viseme." [Azure Speech Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-speech-synthesis-viseme)

[16] Amazon. "Generating Speech Marks — Amazon Polly." [AWS Documentation](https://docs.aws.amazon.com/polly/latest/dg/speechmarks.html)

[17] NVIDIA. "Audio2Face Open Source Release." [NVIDIA Developer Blog, 2025](https://developer.nvidia.com/blog/nvidia-open-sources-audio2face-animation-model/)

[18] Meta. "Oculus Lipsync Viseme Reference." [Meta Developers](https://developers.meta.com/)

[19] Cappelletta, L. & Harte, N. "Phoneme-to-viseme mapping for visual speech recognition." [ICPRAM, 2012](https://www.researchgate.net/publication/268290744)

[20] Live2D Inc. "Cubism SDK Documentation — Standard Parameter List." [Live2D Official Docs](https://docs.live2d.com/)