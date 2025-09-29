
import os, json, yaml, re, time
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from jinja2 import Template
from pypdf import PdfReader
from openai import OpenAI, APIConnectionError, APIError, RateLimitError
from .schemas import FieldEvidence, flatten_values, expand_evidence

def read_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def extract_pdf_text(pdf_path: str, max_pages: int = 100) -> str:
    reader = PdfReader(pdf_path)
    pages = []
    for i, p in enumerate(reader.pages[:max_pages]):
        txt = p.extract_text() or ""
        pages.append(f"[Page {i+1}]\n{txt}")
    return "\n\n".join(pages)

def build_enum_hints(cfg: dict) -> str:
    enums = cfg.get("enums", {})
    keys = [
        "desc.doc_type","desc.venue_type","desc.domain_scope","desc.study_goal","desc.methodology_tags","desc.novelty_type","desc.evaluation_type",
        "survey.method_class","research.primary_type","research.secondary_tags","research.validation_level",
        "algorithm_family","network_type","failure_model","adversary_type",
        "module.sig_scheme","module.commit_rule","module.view_change","module.leader_selection","module.batching_policy","module.data_availability",
        "evaluation_env","workload_type","baseline_type","proof_method","artifact_reuse_ready","bottleneck_primary","bottleneck_evidence",
        "iot.class","iot.crypto_accel","intermittency_pattern","extraction_status","venue.trust_rating",
        # RQ-extended enums
        "module.quorum_system","module.pacemaker_type","module.fast_path_type","module.dag_type","module.mempool_ordering",
        "crypto.multi_sig_type","crypto.pq_support","crypto.zk_usage",
        "attack.catalog","attacker.sim",
        "iot.link_layer","iot.reliability_target","iot.crypto_offload",
        "metric.set"
    ]
    lines = []
    for k in keys:
        if k in enums:
            vals = "; ".join(map(str, enums[k]))
            lines.append(f"- {k}: {vals}")
    return "\n".join(lines)

def render_prompt(template_path: str, citation_header: str, field_list: List[str], pdf_text: str, enum_hints: str, citation_format: str | None = None) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())
    return tmpl.render(citation_header=citation_header, field_list=field_list, pdf_text=pdf_text, enum_hints=enum_hints, citation_format=citation_format)

def call_llm(prompt: str, model: str = None) -> Dict[str, Any]:
    model = model or os.getenv("OPENAI_MODEL","gpt-5")
    base_url = os.getenv("OPENAI_BASE_URL")
    # 支持自定义超时
    try:
        timeout_s = float(os.getenv("OPENAI_TIMEOUT", "60"))
    except Exception:
        timeout_s = 60.0
    client = OpenAI(base_url=base_url, timeout=timeout_s, max_retries=0)
    last_err = None
    # temperature 策略：默认不发送（兼容部分兼容端点只接受默认=1）。
    env_temp = os.getenv("OPENAI_TEMPERATURE", "")
    use_temperature = False
    temperature_value: float | None = None
    if env_temp.strip() != "":
        try:
            temperature_value = float(env_temp)
            use_temperature = True
        except Exception:
            # 非法值则忽略，走不带 temperature 的调用
            use_temperature = False
            temperature_value = None

    force_no_temperature = False
    for attempt in range(4):
        try:
            params: Dict[str, Any] = {
                "model": model,
                "messages": [{"role":"user","content": prompt}],
            }
            # 仅当显式设定且未被强制禁用时，才发送 temperature
            if use_temperature and not force_no_temperature:
                params["temperature"] = temperature_value
            # 如果后端支持，可开启 JSON 严格模式（保持注释，避免不兼容端点报错）
            # params["response_format"] = {"type":"json_object"}

            resp = client.chat.completions.create(**params)
            text = resp.choices[0].message.content
            m = re.search(r"\{[\s\S]*\}\s*$", text)
            payload = m.group(0) if m else text
            return json.loads(payload)
        except APIConnectionError as e:
            last_err = e
            time.sleep(2 ** attempt)
        except RateLimitError as e:
            last_err = e
            time.sleep(2 ** attempt + 1)
        except APIError as e:
            last_err = e
            status = getattr(e, "status_code", None)
            message_text = str(e)
            # 400 且 temperature 不被支持时，移除 temperature 重试
            if status == 400 and ("temperature" in message_text and ("unsupported" in message_text or "unsupported_value" in message_text)):
                force_no_temperature = True
                time.sleep(0.5)
                continue
            if status is not None and 500 <= status < 600:
                time.sleep(2 ** attempt)
            else:
                break
        except Exception as e:
            last_err = e
            # 对可能的超时/读超时进行一次快速重试
            if "timed out" in str(e).lower():
                time.sleep(2 ** attempt)
                continue
            break
    raise RuntimeError(f"LLM call failed (network/KEY/BASE_URL?): {last_err}")

def run_extraction(pdf_path: str, citation_header: str, codebook_path: str, prompt_template_path: str, citation_format: str | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    cfg = read_yaml(codebook_path)
    fields_cfg = cfg.get("fields", [])
    field_names = [f["name"] for f in fields_cfg]
    # optional max pages from env
    try:
        max_pages = int(os.getenv("EXTRACT_MAX_PAGES", "100"))
    except:
        max_pages = 100
    pdf_text = extract_pdf_text(pdf_path, max_pages=max_pages)
    # 可选字符上限截断，避免提示过长引发超时
    try:
        max_chars = int(os.getenv("EXTRACT_MAX_CHARS", "0"))
    except Exception:
        max_chars = 0
    if max_chars and max_chars > 0 and len(pdf_text) > max_chars:
        suffix = "\n\n[TRUNCATED DUE TO EXTRACT_MAX_CHARS]"
        pdf_text = pdf_text[: max(0, max_chars - len(suffix))] + suffix
    enum_hints = build_enum_hints(cfg)
    prompt = render_prompt(prompt_template_path, citation_header, field_names, pdf_text, enum_hints, citation_format=citation_format)
    if os.getenv("MOCK_EXTRACT","false").lower() == "true":
        data = {name: {"value":"NA","evidence":"NA","location":"NA"} for name in field_names}
        return data, {"mock": True, "prompt_tokens": len(prompt.split())}
    result = call_llm(prompt)
    for name in field_names:
        result.setdefault(name, {"value":"NA","evidence":"NA","location":"NA"})
    return result, {"mock": False, "prompt_tokens": len(prompt.split())}

def append_outputs(master_csv: str, evidence_csv: str, paper_id: str, extracted: Dict[str, Any], codebook_path: str):
    os.makedirs(os.path.dirname(master_csv), exist_ok=True)
    os.makedirs(os.path.dirname(evidence_csv), exist_ok=True)

    cfg = read_yaml(codebook_path)
    unknown = cfg["settings"]["unknown_token"]

    fe_map = {k: FieldEvidence(**v) for k, v in extracted.items()}
    row = flatten_values(fe_map, unknown_token=unknown)
    row["paper_id"] = paper_id

    import pandas as pd
    if os.path.exists(master_csv):
        df = pd.read_csv(master_csv)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(master_csv, index=False)

    ev_rows = expand_evidence(paper_id, fe_map)
    if os.path.exists(evidence_csv):
        ev = pd.read_csv(evidence_csv)
        ev = pd.concat([ev, pd.DataFrame(ev_rows)], ignore_index=True)
    else:
        ev = pd.DataFrame(ev_rows)
    ev.to_csv(evidence_csv, index=False)

    # Save raw JSON
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    raw_path = raw_dir / f"{paper_id}_{ts}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)


def guess_title_from_citation(citation_header: str, citation_format: Optional[str] = None) -> Optional[str]:
    """Heuristically extract a likely title from a citation string.
    Works for common APA/ACM/IEEE-like patterns. Returns None if uncertain.
    """
    if not citation_header or not citation_header.strip():
        return None
    text = " ".join(citation_header.strip().split())

    # 1) Titles in quotes
    m = re.search(r"[“\"']([^”\"']{5,200})[”\"']", text)
    if m:
        candidate = m.group(1).strip()
        if 5 <= len(candidate) <= 200 and len(candidate.split()) >= 3:
            return candidate

    # 2) After year in parentheses: Smith ... (2021). Title. Venue ...
    m = re.search(r"\((19|20)\d{2}[a-z]?\)\.?\s+([^\.]{5,200})\.", text)
    if m:
        candidate = m.group(2).strip()
        if 5 <= len(candidate) <= 200 and len(candidate.split()) >= 3:
            return candidate

    # 3) Before 'In Proceedings' or 'In Proc.' segments
    m = re.search(r"\.\s+([^\.]{5,200})\.\s+In\s", text)
    if m:
        candidate = m.group(1).strip()
        if 5 <= len(candidate) <= 200 and len(candidate.split()) >= 3:
            return candidate

    # 4) Fallback: longest sentence between first and second period
    parts = [p.strip() for p in text.split('.') if p.strip()]
    if len(parts) >= 2:
        for seg in parts[1:3]:
            if 5 <= len(seg) <= 200 and len(seg.split()) >= 3:
                return seg
    return None
