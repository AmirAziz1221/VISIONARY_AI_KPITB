from collections import Counter
from datetime import datetime
from html import escape

RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
CRITICAL_WORDS = ("slide", "slid", "slip", "landslide", "washout", "collapse", "subsid")
ACTIONS = {
    "Critical": ("Warn traffic and send an emergency team", "Within 24 hours"),
    "High": ("Dispatch a repair crew", "Within 7 days"),
    "Medium": ("Schedule maintenance", "Within 30 days"),
    "Low": ("Monitor and re-scan", "Next survey cycle"),
    "None": ("No action needed", "-"),
}


def severity_of(det):
    """Heuristic: keyword + box size relative to the frame. Tune for your classes."""
    name = det["class"].lower()
    a = det["area_ratio"]
    if any(w in name for w in CRITICAL_WORDS) and det["confidence"] >= 0.5:
        return "Critical"
    if a >= 0.08:
        return "High"
    if a >= 0.02:
        return "Medium"
    return "Low"


def add_severity(dets):
    for d in dets:
        d["severity"] = severity_of(d)
    return dets


def frame_score(dets):
    return sum(RANK[d["severity"]] * d["confidence"] for d in dets)


def summarise(dets, frames):
    by_class = Counter(d["class"] for d in dets)
    by_sev = Counter(d["severity"] for d in dets)
    top = max((d["severity"] for d in dets), key=RANK.get, default="None")
    action, timeline = ACTIONS[top]
    return {
        "frames_analysed": frames,
        "detections_total": len(dets),
        "by_class": dict(by_class),
        "by_severity": dict(by_sev),
        "overall_priority": top,
        "recommended_action": action,
        "timeline": timeline,
    }


def build_html(rid, summary, meta, images_b64, dets):
    rows = "".join(
        f"<tr><td>{escape(d['class'])}</td><td>{d['severity']}</td><td>{d['confidence']}</td>"
        f"<td>{d.get('time_s', '-')}</td></tr>"
        for d in sorted(dets, key=lambda d: -RANK[d["severity"]])[:50]
    )
    imgs = "".join(f"<img src='data:image/jpeg;base64,{b}'>" for b in images_b64)
    loc = f"{meta['lat']}, {meta['lon']}" if meta.get("lat") is not None else "not provided"
    cls = ", ".join(f"{escape(k)}: {v}" for k, v in summary["by_class"].items()) or "none"
    return f"""<!doctype html><meta charset=utf-8><title>Road Report {rid}</title>
<style>body{{font-family:Arial;max-width:900px;margin:30px auto;padding:0 16px}}
img{{width:100%;margin:8px 0;border-radius:8px}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #ddd;padding:8px;text-align:left}}.p{{font-size:24px;font-weight:700;color:#b26a00}}</style>
<h1>Road Condition Engineering Report</h1>
<p>Report ID: {rid} · Generated: {datetime.now():%Y-%m-%d %H:%M} · Source: {escape(meta['source'])} · Location: {loc}</p>
<p class=p>Overall priority: {summary['overall_priority']}</p>
<p><b>Recommended action:</b> {summary['recommended_action']} · <b>Timeline:</b> {summary['timeline']}</p>
<p><b>Detections:</b> {summary['detections_total']} across {summary['frames_analysed']} frame(s). {cls}</p>
{imgs}<h2>Findings (top 50)</h2><table><tr><th>Defect</th><th>Severity</th><th>Confidence</th><th>Time (s)</th></tr>{rows}</table>
<p style="color:#666;font-size:13px">Automated screening. Counts are per sampled frame, not unique defects.
Severity is a heuristic. A qualified engineer must verify findings before action.</p>"""
