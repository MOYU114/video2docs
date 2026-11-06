# video2docs

Turn lecture recordings into **slide-aligned transcripts**: for every slide page you get the
time range in the video, the slide text, and what the lecturer actually said while it was on
screen. The output is plain Markdown, ready to read yourself or to hand to an LLM for
summaries, key points and likely exam questions.

Everything runs locally. Transcription uses
[mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) on Apple Silicon
(about 8x real time with `whisper-large-v3-turbo` on an M4), and alignment is a small
pure-Python TF-IDF + Viterbi matcher with no model download.

```
recordings/*.mp4 ──transcribe──▶ transcripts (JSON + timestamped TXT)
slides/*.pdf     ──slides──────▶ per-page text            ──align──▶ output/<course>/<recording>.md
```

## Example output

```markdown
## lecture02 p.41  [00:25:52–00:30:38]

**Slide**

> Designing Application-Level Multicast
> ...

**Lecture**

... link stress, the lower the better, stretch the lower the better, and tree cost ...
```

## Install

Requires macOS on Apple Silicon, [Homebrew](https://brew.sh) and Python 3.10–3.13.

```bash
brew install ffmpeg uv
git clone https://github.com/MOYU114/video2docs.git
cd video2docs
uv sync
```

## Usage

1. Copy the example config and point it at your files:

   ```bash
   cp config/courses.example.yaml config/courses.yaml
   ```

   Each course needs a folder of recordings and a folder of slide PDFs.

2. Run the pipeline (each step skips work that is already done):

   ```bash
   uv run video2docs transcribe CS5223 --only 2026-08-28   # try one recording first
   uv run video2docs slides CS5223
   uv run video2docs align CS5223
   uv run video2docs all CS5223                            # or everything at once
   ```

Results land in `output/<course>/`. Intermediate files (transcripts, parsed PDFs, alignment
JSON with similarity scores) are in `work/<course>/`.

## How alignment works

1. The transcript is cut into ~45 s windows.
2. Each window and each slide page become TF-IDF vectors; IDF is estimated over both.
3. Every window votes for its closest deck; decks with at least 15% of the votes are taken
   as the lecture's material, so a recording that spans two decks is handled.
4. A Viterbi pass over the chosen pages favours staying on a page or moving forward and
   penalises jumping back, which removes most one-off mismatches while still allowing the
   lecturer to revisit a slide.

If deck detection is wrong for a recording, set it by hand with `lecture_map` in the config.

## Limitations

- Transcription requires Apple Silicon (MLX). Other platforms would need a different Whisper
  backend, such as faster-whisper; contributions welcome.
- Alignment relies on shared vocabulary, so slides that are mostly figures or equations
  align less reliably.

## 中文说明

把课程录像转成“按讲义页对齐的文字稿”：每页讲义对应视频里的时间段、讲义原文和老师当时说的话，
输出为 Markdown，可以直接阅读，也可以交给 LLM 提炼重点和考点。全部在本地运行。
用法见上文：复制 `config/courses.example.yaml` 为 `config/courses.yaml` 并填好路径，然后运行
`uv run video2docs all <课程名>`。

## License

MIT
