# Visionary AI: Asphalt Pathology Detection

AI-powered road inspection from a single photo or video. The system detects asphalt pathologies with a YOLO model, retrieves engineering knowledge for each defect, and generates a civil engineering inspection report with severity, priority, recommended repair and action timeframe.

Built for the **AI Innovation Challenge 2026** (AI Builders League) by **Team Visionary AI**.

## Live Demo

**[Try it on Hugging Face Spaces](https://huggingface.co/spaces/AmirAziz1221/Civil_Infrastructure_Pathology_Detection)**

Upload a road image or video and get the annotated result plus a downloadable Word report. Free Spaces sleep when idle, so the first load can take a minute.

## The Problem

Roads in remote regions often fail without anyone recording it. Surveys need trained engineers and vehicles, so damage is reported late or never. Potholes, cracks and sliding surfaces then cut access to hospitals, markets and schools.

## The Solution

Anyone with a phone records the road. The AI does the survey.

1. **Capture:** upload a photo or video of the road.
2. **Detect:** a YOLO model finds asphalt pathologies frame by frame.
3. **Retrieve:** each detected class is matched to an engineering knowledge catalog (RAG).
4. **Report:** a structured inspection report is generated, with an optional LLM-written version.

## Features

- Image and video detection with annotated output
- RAG-based diagnosis from a JSON knowledge catalog: severity, priority, risk, probable causes, recommended intervention and action deadline
- Engineering report in the app and as a downloadable Word (.docx) file
- Optional Grok (xAI) report writing, with an automatic fallback to a local report when no API key is set
- Adjustable confidence threshold
- Extensible design: more pathology models can be added without changing the pipeline

## Architecture

```
Image / Video
      |
      v
 YOLO asphalt model  -->  detections (class, confidence, box)
      |
      v
 RAG catalog lookup  -->  severity, priority, risk, recommendation, deadline
      |
      v
 Report generator (local template, or Grok when XAI_API_KEY is set)
      |
      v
 Annotated media + Markdown report + Word file
```

## Tech Stack

- **Detection:** Ultralytics YOLO, PyTorch, OpenCV
- **Interface:** Gradio
- **Report:** python-docx, xAI Grok API (optional)
- **Deployment:** Hugging Face Spaces

## Project Structure

```
VISIONARY_AI/
├── app.py                     # Gradio app: detection, RAG, report generation
├── best_asphalt.pt            # Trained YOLO weights (Git LFS)
├── knowledge/
│   └── asphalt_catalog.json   # Engineering knowledge for each pathology class
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone https://github.com/AmirAziz1221/VISIONARY_AI.git
cd VISIONARY_AI
git lfs pull            # downloads the model weights

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Open `http://localhost:7860`, choose the **Image Detection** or **Video Detection** tab, upload a file and click the run button.

### Optional: LLM-written reports

Set your xAI key before starting the app:

```bash
export XAI_API_KEY="your_key_here"        # Windows PowerShell: $env:XAI_API_KEY="your_key_here"
```

Without a key, the app still produces a complete local RAG report. On Hugging Face, add the key under **Settings → Variables and secrets**. Never commit API keys to the repository.

## Deployment on Hugging Face Spaces

The live demo runs as a Gradio Space. To deploy your own, create a Gradio Space, then push `app.py`, `best_asphalt.pt`, `knowledge/` and `requirements.txt` to it. Hugging Face also needs a settings block at the top of the Space's README (`sdk: gradio`, `app_file: app.py`).

## Report Priorities

| Priority | Meaning |
|---|---|
| P1 | Urgent: safety management required |
| P2 | Plan the repair within the maintenance programme |
| P3 | Routine preventive maintenance |

Exact timeframes come from `knowledge/asphalt_catalog.json` and can be edited to match local standards.

## Roadmap

- Concrete defect detection (cracks, spalling, exposed rebar)
- Facade defect detection (cracks, falling tiles, water damage)
- Electric tower inspection (corrosion, leaning, missing bolts)
- GPS-tagged defect maps and unique defect tracking across video frames
- Mobile-friendly capture and offline inference with ONNX/TFLite

## Limitations

- Video counts are per processed frame, so one defect seen in several frames may be counted more than once.
- Detection quality depends on image quality, lighting and the training data.
- Free CPU hosting is slow for long videos.

## Disclaimer

This project provides AI-assisted screening for preliminary engineering support only. All findings must be verified by a qualified civil engineer through field inspection before any repair decision.

## Team and Author

**Team Visionary AI**, AI Innovation Challenge 2026

**Amir Aziz**, Computer Vision Engineer
[LinkedIn](https://www.linkedin.com/in/amir-aziz-2868aa266) · [GitHub](https://github.com/AmirAziz1221)

> *Build Local. Solve Real. Scale Responsibly.*
