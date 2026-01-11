---
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-resume-2026-01-09.md
  - _bmad-output/planning-artifacts/prd.md
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Rust vs Python for Resume as Code CLI'
research_goals: 'Evaluate Rust as alternative to Python for CLI implementation, focusing on: (1) single binary distribution, (2) learning opportunity, (3) performance for BM25 ranking and embedding operations'
user_name: 'Joshua Magady'
date: '2026-01-09'
web_research_enabled: true
source_verification: true
---

# Technical Research Report: Rust vs Python for Resume as Code CLI

**Date:** 2026-01-09
**Author:** Joshua Magady
**Research Type:** Technical

---

## Research Overview

This research evaluates whether Rust is a viable and beneficial alternative to Python for implementing the Resume as Code CLI tool, with specific focus on:

1. **Single Binary Distribution** - Packaging and deployment simplicity
2. **Learning Opportunity** - Rust as a skill development investment
3. **Performance** - BM25 ranking and future embedding operations

**Context:** Resume as Code is a CLI tool for managing career accomplishments as structured Work Units and generating tailored resumes. The PRD specifies Python with Click, WeasyPrint, and python-docx.

---

## Technical Research Scope Confirmation

**Research Topic:** Rust vs Python for Resume as Code CLI
**Research Goals:** Evaluate Rust as alternative to Python for CLI implementation, focusing on: (1) single binary distribution, (2) learning opportunity, (3) performance for BM25 ranking and embedding operations

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-01-09

---

## Technology Stack Analysis

### Executive Summary: Rust vs Python for Resume as Code

Based on comprehensive research of the 2025-2026 ecosystem, here is the verdict for your specific use case:

| Priority | Winner | Confidence | Notes |
|----------|--------|------------|-------|
| **Single Binary Distribution** | **Rust** | High | 5-15MB binary, instant startup vs 25-50MB + 2-3s startup (PyInstaller) |
| **Learning Opportunity** | **Rust** | High | Worthwhile investment, 3-6 month learning curve |
| **BM25 Performance** | **Tie** | High | BM25S (Python) achieves near-Tantivy (Rust) performance |
| **Embedding Performance** | **Rust** | Medium | 3-5x faster with ONNX Runtime, but Python ecosystem is richer |
| **PDF Generation** | **Python** | High | WeasyPrint + Jinja is mature; genpdf is capable but less flexible |
| **DOCX Generation** | **Python** | High | python-docx vastly superior for templates; docx-rs is construction-only |
| **CLI Framework** | **Tie** | High | Clap and Click are both excellent |
| **Development Velocity** | **Python** | High | 4-8 weeks MVP vs 12-16 weeks in Rust |

**Bottom Line:** For Resume as Code specifically, the **hybrid approach** or **Python with selective Rust** makes the most sense given your goals.

---

### Single Binary Distribution

#### Rust Native Compilation
- Compiles directly to native machine code via LLVM
- **Binary size:** 5-15MB typical for CLI tools (can reach 50MB with heavy deps)
- **Startup time:** Milliseconds — instant execution
- **Cross-compilation:** Excellent. Build Windows, macOS, Linux from single machine:
  ```bash
  rustup target add x86_64-apple-darwin
  rustup target add x86_64-pc-windows-gnu
  cargo build --target x86_64-pc-windows-gnu --release
  ```
- **No runtime dependencies** — users download and run immediately
- The `cross` tool automates cross-compilation with Docker

*Source: [LogRocket Cross-Compilation Guide](https://blog.logrocket.com/guide-cross-compilation-rust/), [Better Programming](https://betterprogramming.pub/cross-compiling-rust-from-mac-to-linux-7fad5a454ab1)*

#### Python Packaging Options

| Tool | Binary Size | Startup Time | Pros | Cons |
|------|-------------|--------------|------|------|
| **PyInstaller** | ~28MB | ~2.1s | Mature, handles binary deps well | Extracts to temp dir, slow startup |
| **PyOxidizer** | Smaller | Faster | Loads from memory, no temp extraction | Must build C deps from source |
| **Nuitka** | Variable | 2-10x faster | Compiles to C then native | Some CPython-specific code may break |

*Source: [PyOxidizer Comparisons](https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_comparisons.html), [AhmedSyntax](https://ahmedsyntax.com/pyinstaller-onefile/)*

**Verdict:** Rust wins decisively on binary distribution. Smaller binaries, instant startup, trivial cross-compilation.

---

### CLI Frameworks

#### Clap (Rust)
- **De facto standard** for Rust CLI development (used by ripgrep, Cargo itself)
- Derive macro API for declarative command definition
- Automatic help generation, shell completions (bash/zsh/fish/powershell)
- **Compile-time validation** — typos and type mismatches caught before runtime
- Adds ~700KB-1MB to binary size
- Excellent documentation

```rust
#[derive(Parser)]
struct Cli {
    #[arg(long)]
    jd: PathBuf,
    #[arg(long, default_value = "dist")]
    output_dir: PathBuf,
}
```

*Source: [Awesome CLI Frameworks](https://github.com/shadawck/awesome-cli-frameworks), [HN Discussion](https://news.ycombinator.com/item?id=44429695)*

#### Click (Python)
- Dominant Python CLI framework (powers Flask CLI)
- Decorator-based API
- Excellent documentation with real-world examples
- **Typer** (by FastAPI author) modernizes Click with type hints

```python
@click.command()
@click.option('--jd', type=click.Path(exists=True))
def plan(jd):
    ...
```

*Source: [Click Advanced](https://click.palletsprojects.com/en/stable/advanced/), [Typer Alternatives](https://typer.tiangolo.com/alternatives/)*

**Verdict:** Both excellent. Clap has compile-time safety; Click/Typer has faster iteration. For Resume as Code, either works well.

---

### PDF Generation

#### Rust Options

| Library | Type | Strengths | Weaknesses |
|---------|------|-----------|------------|
| **genpdf** | High-level | Pure Rust, handles layout/wrapping, multi-page | Limited image support |
| **Typst** | Template engine | Modern LaTeX alternative, JSON/CSV input, fast | Newer ecosystem |
| **printpdf** | Low-level | Fine-grained control | Requires manual coordinate management |

genpdf example:
```rust
let mut doc = genpdf::Document::new(font_family);
doc.push(genpdf::elements::Paragraph::new("Resume"));
doc.render_to_file("output.pdf")?;
```

*Source: [docs.rs/genpdf](https://docs.rs/genpdf), [Typst Blog](https://typst.app/blog/2025/automated-generation/)*

#### Python Options

| Library | Approach | Speed | Best For |
|---------|----------|-------|----------|
| **WeasyPrint** | HTML/CSS → PDF | 0.35s/doc | Template-driven, designer collaboration |
| **ReportLab** | Programmatic | 0.75s/doc | Complex layouts, charts, conditional logic |
| **FPDF2** | Lightweight | Fast | Simple documents, minimal deps |
| **Borb** | Modern | 0.12s/doc | Forms, signatures, multimedia |

WeasyPrint + Jinja workflow:
```python
template = Template(html_template)
html = template.render(name=name, experience=experience)
pdf = HTML(string=html).write_pdf()
```

*Source: [Nutrient Top 10 PDF Libraries](https://www.nutrient.io/blog/top-10-ways-to-generate-pdfs-in-python/), [Templated.io](https://templated.io/blog/generate-pdfs-in-python-with-libraries/)*

**Verdict:** Python (WeasyPrint) wins for resume generation. HTML/CSS templates enable designer collaboration. Rust (genpdf) is capable but less mature for complex layouts.

---

### DOCX Generation

#### Rust: docx-rs
- Clean API similar to python-docx
- Good for **construction** (building new documents)
- **Critical limitation:** Reading/modifying existing DOCX files loses formatting
- WebAssembly support for browser-based generation
- Silently ignores unrecognized XML tags during round-trip

*Source: [Tritium Legal Blog](https://tritium.legal/blog/word)*

#### Python: python-docx
- **Battle-tested**, comprehensive manipulation
- Excellent round-trip preservation (read → modify → write)
- **Template-based generation:** Load designed template, replace placeholders, save
- Mature ecosystem with extensive documentation

**Verdict:** Python (python-docx) wins decisively. Template support is critical for professional resumes. docx-rs is construction-only.

---

### BM25 Text Ranking

#### Rust: Tantivy
- Reimplements Apache Lucene core with modern optimizations
- **2x throughput** of Java Lucene, less memory
- BM25 scoring by default
- Boolean queries, phrase matching, fuzzy search
- Powers production systems (ParadeDB, Quickwit)
- Starts in <10ms, handles millions of documents

*Source: [ParadeDB Tantivy Intro](https://www.paradedb.com/learn/tantivy/introduction)*

#### Python: BM25S
- **500x faster** than rank-bm25 using scipy sparse matrices
- Near-commercial-grade performance on single machine
- Pure Python, simple API
- Pre-computes word-level relevance scores

```python
import bm25s
retriever = bm25s.BM25(corpus=corpus)
results, scores = retriever.retrieve(bm25s.tokenize("Rust Docker"), k=10)
```

*Source: [Hugging Face BM25S Blog](https://huggingface.co/blog/xhluca/bm25s)*

**Verdict:** Tie. BM25S achieves near-Tantivy performance with Python simplicity. For Resume as Code's scale (hundreds to thousands of Work Units), BM25S is sufficient. Tantivy only necessary for millions of documents.

---

### Embeddings and Vector Search

#### Rust Options
- **Candle:** Minimalist ML framework from Hugging Face, lightweight inference
- **ONNX Runtime (ort crate):** Production-grade, 3-5x Python speed, 60-80% less memory
- **Pragmatic approach:** Generate embeddings in Python, inference in Rust via PyO3

```rust
let session = Session::builder()?
    .commit_from_file("model.onnx")?;
let embeddings = session.run(ort::inputs!["input_ids" => input])?;
```

*Source: [dev.to Sentence Transformers in Rust](https://dev.to/mayu2008/building-sentence-transformers-in-rust-a-practical-guide-with-burn-onnx-runtime-and-candle-281k)*

#### Python Options
- **sentence-transformers:** Dominant, pre-trained models, dead simple
- **FAISS:** Industry-standard vector similarity at scale (billions of embeddings)
- **LanceDB:** Modern vector DB with SQL queries on embeddings

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(resumes)
```

*Source: [SBERT Semantic Search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html), [FAISS Guide](https://www.stephendiehl.com/posts/faiss/)*

**Verdict:** Python for development (richer ecosystem), Rust for production inference (3-5x faster). For Resume as Code MVP, Python suffices. Semantic embeddings are post-MVP anyway.

---

### Developer Experience

#### Rust Learning Curve
- **3-6 months** for Python developers to reach productivity
- Ownership/borrowing system initially frustrating
- "Fighting the borrow checker" phase yields profound insights
- Compiler acts as automated code reviewer
- Longer compilation times (seconds to minutes)
- Error messages can overwhelm beginners

*Source: [JetBrains Rust Blog](https://blog.jetbrains.com/rust/2025/11/10/rust-vs-python-finding-the-right-balance-between-speed-and-simplicity/), [dev.to Learning Rust](https://dev.to/mukhtar_onif/getting-started-with-rust-in-2025-why-now-is-a-great-time-to-learn-rust-1d89)*

#### Python Development Speed
- Immediate feedback, minimal friction
- Dynamic typing enables rapid prototyping
- Vast ecosystem — almost any capability has mature libraries
- Requires comprehensive testing to catch type-related bugs
- No compile-time validation

**Verdict:** Python for speed to MVP (4-8 weeks). Rust for long-term reliability (12-16 weeks to production). Learning Rust is valuable but extends timeline.

---

### Serialization (YAML/JSON)

#### Serde (Rust)
- De facto standard, derive macros for zero-cost serialization
- serde_json is ~20x faster than serde_yaml
- Strong type safety at parse time
- Compile-time overhead from macro expansion

#### Python (standard library)
- `json` built-in, `PyYAML` for YAML
- Adequate performance for config loading
- Minimal learning curve

**Verdict:** Both adequate. Serde faster but only matters at massive scale.

---

## Recommendations for Resume as Code

### Option 1: Python MVP, Selective Rust Later (Recommended)

**Timeline:** 4-8 weeks to MVP

**Stack:**
- CLI: Click or Typer
- PDF: WeasyPrint + Jinja templates
- DOCX: python-docx with template support
- BM25: BM25S (500x faster than rank-bm25)
- Distribution: PyInstaller (accept 2-3s startup)

**When to add Rust:**
- If startup time becomes unacceptable → rewrite CLI in Rust
- If BM25 on large corpora becomes bottleneck → Tantivy via PyO3
- If embeddings needed at scale → ONNX Runtime via PyO3

**Pros:** Fast to market, mature ecosystem, template-driven generation
**Cons:** Slower startup, larger binary

---

### Option 2: Rust from Day One (Learning Path)

**Timeline:** 12-16 weeks to MVP

**Stack:**
- CLI: Clap
- PDF: genpdf (or Typst for template approach)
- DOCX: docx-rs (construction only — may need to defer template support)
- BM25: Tantivy
- Distribution: Native binary via `cargo build --release`

**Challenges:**
- DOCX template support is weak — significant gap vs python-docx
- PDF templates require more custom code than WeasyPrint
- Learning curve extends timeline by 2-3x

**Pros:** Single binary, instant startup, performance headroom, Rust skills
**Cons:** Longer timeline, weaker document template ecosystem

---

### Option 3: Hybrid Architecture (Best of Both)

**Timeline:** 8-12 weeks

**Architecture:**
- Core CLI and distribution: Rust (Clap, single binary)
- Document generation: Python (WeasyPrint, python-docx) called via subprocess or embedded Python
- BM25/embeddings: Either language based on scale

**Integration Patterns:**
1. **Subprocess:** Rust CLI calls Python scripts for generation
2. **PyO3:** Embed Python interpreter in Rust binary
3. **Microservice:** Rust CLI, Python document service

**Pros:** Best distribution story, best document ecosystem
**Cons:** Increased complexity, two languages to maintain

---

## Final Recommendation

Given your priorities:

1. **Single binary distribution** → Points to Rust
2. **Learning opportunity** → Points to Rust
3. **Performance for BM25/embeddings** → Tie (BM25S is fast enough; embeddings post-MVP)

**My recommendation: Option 2 (Rust from Day One) with acceptance of trade-offs.**

**Rationale:**
- Your primary goals (binary distribution + learning Rust) both favor Rust
- The DOCX template limitation is real but solvable (generate from scratch, or defer DOCX templates)
- The PDF limitation is minor (genpdf or Typst can handle resume layouts)
- BM25 with Tantivy is excellent
- Timeline extension is acceptable for a personal tool + learning project
- You'll end up with a superior distribution story

**Critical Success Factors:**
1. Accept that DOCX generation will be construction-only (no template loading) in v1
2. Use Typst or genpdf for PDFs — don't try to replicate WeasyPrint's HTML approach
3. Budget 3-6 months for Rust proficiency before expecting Python-like velocity
4. Start with the CLI framework (Clap) and Work Unit validation (serde_yaml) — low-risk, high-learning
5. Tackle PDF generation after you're comfortable with Rust patterns

**Fallback:** If Rust document generation proves too limiting, the hybrid approach (Rust CLI + Python document service) remains viable.

---

<!-- Content will be appended sequentially through research workflow steps -->
