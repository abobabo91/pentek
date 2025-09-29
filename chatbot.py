import os
import re
from io import BytesIO
from typing import Dict, Any, List, Tuple

import streamlit as st
from openai import OpenAI
import PyPDF2


# =========================
# ----- Streamlit UI  -----
# =========================

st.set_page_config(page_title="Startup Due Diligence (Docs + Web)")
st.title("🚀 Startup Due Diligence — Docs + Web + Citations")

# =========================
# ------ OpenAI Client ----
# =========================

def get_api_key() -> str:
    try:
        return st.secrets["openai"]["OPENAI_API_KEY"]
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    st.error("Missing OpenAI API key. Put it in st.secrets['openai']['OPENAI_API_KEY'] or the OPENAI_API_KEY environment variable.")
    st.stop()

client = OpenAI(api_key=api_key)


# =========================
# -------- Helpers --------
# =========================

MODEL_CHOICES = [
    "gpt-5-nano",
    "gpt-4o",
    "gpt-4o-mini",
]
DEFAULT_MODEL = "gpt-5-nano"

# --- sanitize wrappers from model output (SDK annotations, zero-width, etc.) ---
_CITE_WRAP_RE = re.compile(r"\ue200.*?\ue201", flags=re.DOTALL)  # internal cite wrappers
_TURN_FILE_RE = re.compile(r"\[turn\d+file\d+\]")                # internal file ids
_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060"), None)

def sanitize_text(s: str) -> str:
    if not s:
        return s
    s = _CITE_WRAP_RE.sub("", s)
    s = _TURN_FILE_RE.sub("", s)
    s = s.translate(_ZERO_WIDTH)
    return s.strip()

def base_system_instructions() -> str:
    return (
        "You are a startup due diligence assistant.\n"
        "Use BOTH the uploaded PDF text AND the web (via web_search) as needed.\n"
        "Always include inline numeric citations like [1], [2] directly in the text where you use evidence.\n"
        "Always end with a 'References:' section listing sources in order of appearance.\n"
        "For files: include the filename + a short quote.\n"
        "For web: include the page title + full URL.\n"
        "Be concise, structured, and critical.\n"
    )

def one_pager_prompt(file_text: str) -> str:
    return (
        "Write a very concise one-pager (max 200 words) from the uploaded documents.\n"
        "Format output in clean Markdown with clear section headers.\n"
        "Sections: 1) Problem & solution, 2) Core technology, 3) Traction & business model, 4) Risks.\n"
        f"Uploaded document content:\n{file_text[:8000]}"
    )


def claims_and_validation_prompt(file_text: str) -> str:
    return (
        "Task: Extract the startup’s TECHNOLOGY CLAIMS from the uploaded files, then validate each claim by running multiple web searches.\n"
        "Output at least 5 technology claims.\n"
        "For EACH claim, perform deep web searches (company site, docs, press, benchmarks, patents, papers, GitHub, credible media/industry sources).\n"
        "For EACH claim, you MUST run at least one (but preferably 2-3) distinct web_search query. When searching keep the scope of the company.\n"
        "For EACH claim, use at least 3 citations from the searches.\n"
        "Output format:\n"
        "A) List of extracted technology claims (numbered, short, precise, one per line).\n"
        "Summarize the best evidence you find and critically assess. Cite files inline.\n"
        "B) Validation table (one row per claim): {Claim} | {Assessment: Supported / Plausible but unverified / Questionable or contradicts} | {Key Evidence (1-3 bullets)}\n"
        "C) Executive summary of the validation results in max 150 words.\n\n"
        "Important:\n"
        "-Use inline link citations for every evidence-based sentence and end with References.\n"
        "-Only cite the websearch results not the original document.\n"
        "-Format output in clean Markdown with headings and a compact table.\n"
        f"Uploaded document content:\n{file_text[:8000]}"
    )




def extract_pdf_text(uploaded_files) -> str:
    text_chunks = []
    for f in uploaded_files:
        try:
            reader = PyPDF2.PdfReader(BytesIO(f.getvalue()))
            for page in reader.pages:
                text_chunks.append(page.extract_text() or "")
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")
    return "\n".join(text_chunks)


def extract_sources_and_quotes(final_response) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Extracts:
      - web_sources: list of {title, url, snippet?}
      - file_quotes: list of {filename, quote}
    """
    web_sources: List[Dict[str, str]] = []
    file_quotes: List[Dict[str, str]] = []
    try:
        for block in getattr(final_response, "output", []) or []:
            if getattr(block, "type", "") == "output_text":
                anns = getattr(block, "annotations", None) or []
                for a in anns:
                    if not isinstance(a, dict):
                        continue
                    if a.get("type") == "web_citation":
                        web_sources.append({
                            "title": a.get("title") or "Source",
                            "url": a.get("url") or "",
                            "snippet": a.get("snippet") or ""
                        })
    except Exception:
        pass

    # Deduplicate
    seen_urls = set()
    dedup_web = []
    for s in web_sources:
        u = s.get("url", "")
        if u and u not in seen_urls:
            dedup_web.append(s)
            seen_urls.add(u)

    return dedup_web[:20], file_quotes


def ensure_references_section(answer_text: str, files_list: List[Dict[str, str]], web_list: List[Dict[str, str]]) -> str:
    refs_lines = []
    idx = 1
    for f in files_list:
        refs_lines.append(f"[{idx}] **{f['filename']}** — {f['quote']}")
        idx += 1
    for w in web_list:
        title = w.get("title") or "Source"
        url = w.get("url") or ""
        snippet = w.get("snippet") or ""
        if url:
            refs_lines.append(f"[{idx}] [{title}]({url})" + (f" — {snippet}" if snippet else ""))
        else:
            refs_lines.append(f"[{idx}] {title}" + (f" — {snippet}" if snippet else ""))
        idx += 1

    if refs_lines:
        if re.search(r"(?im)^\s*references\s*:", answer_text):
            return answer_text + "\n\n" + "\n".join(refs_lines)
        else:
            return answer_text + "\n\n**References:**\n" + "\n".join(refs_lines)
    return answer_text


def run_streamed_response(model: str, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]):
    streamed_text = ""
    final_response_obj = None
    with client.responses.stream(
        model=model,
        input=messages,
        tools=tools
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                streamed_text += event.delta
        stream.until_done()
        final_response_obj = stream.get_final_response()
    return sanitize_text(streamed_text), final_response_obj


# =========================
# ---- Session State -------
# =========================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_text" not in st.session_state:
    st.session_state.uploaded_text = ""

if "dd_onepager" not in st.session_state:
    st.session_state.dd_onepager = None
if "dd_validation" not in st.session_state:
    st.session_state.dd_validation = None


# =========================
# ---- Upload & Controls ---
# =========================

st.header("⚙️ Model & Sources")
model_choice = st.selectbox("Model", options=MODEL_CHOICES, index=MODEL_CHOICES.index(DEFAULT_MODEL))

uploaded_files = st.file_uploader(
    "Upload PDF pitch decks, one-pagers, plans, etc.",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.session_state.uploaded_text = extract_pdf_text(uploaded_files)
    st.success(f"Extracted text from {len(uploaded_files)} PDF(s).")

dd_clicked = st.button("🧪 Run Due Diligence", type="primary", disabled=not st.session_state.uploaded_text)


# =========================
# ---- Due Diligence Flow --
# =========================

def run_due_diligence_onepager(model: str, file_text: str):
    messages = [
        {"role": "system", "content": base_system_instructions()},
        {"role": "user", "content": one_pager_prompt(file_text)}
    ]
    text, resp_obj = run_streamed_response(model, messages, tools=[{"type": "web_search"}])
    web_sources, file_quotes = extract_sources_and_quotes(resp_obj)
    final_text = ensure_references_section(text, file_quotes, web_sources)
    return final_text

def run_due_diligence_validation(model: str, file_text: str):
    messages = [
        {"role": "system", "content": base_system_instructions()},
        {"role": "user", "content": claims_and_validation_prompt(file_text)}
    ]
    text, resp_obj = run_streamed_response(model, messages, tools=[{"type": "web_search"}])
    web_sources, file_quotes = extract_sources_and_quotes(resp_obj)
    final_text = ensure_references_section(text, file_quotes, web_sources)
    return final_text


if dd_clicked:
    st.subheader("📄 One-pager from Documents")
    with st.spinner("Summarizing uploaded materials..."):
        try:
            st.session_state.dd_onepager = run_due_diligence_onepager(model_choice, st.session_state.uploaded_text)
            st.markdown(st.session_state.dd_onepager)
        except Exception as e:
            st.error(f"One-pager error: {e}")

    st.divider()

    st.subheader("🔍 Claims Extraction & Validation (Docs + Web)")
    with st.spinner("Extracting claims and validating with deep web searches..."):
        try:
            st.session_state.dd_validation = run_due_diligence_validation(model_choice, st.session_state.uploaded_text)
            st.markdown(st.session_state.dd_validation)
        except Exception as e:
            st.error(f"Validation error: {e}")



if st.session_state.dd_onepager and not dd_clicked:
    with st.expander("📄 Last One-pager from Documents", expanded=False):
        st.markdown(st.session_state.dd_onepager)

if st.session_state.dd_validation and not dd_clicked:
    with st.expander("🔍 Last Claims & Validation One-pager", expanded=False):
        st.markdown(st.session_state.dd_validation)


# =========================
# ---- Chat History --------
# =========================

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask anything about the uploaded docs or the company (I can also browse the web)…")

if user_input:
    safe_user = sanitize_text(user_input)
    st.session_state.chat_history.append({"role": "user", "content": safe_user})
    with st.chat_message("user"):
        st.markdown(safe_user)

    with st.chat_message("assistant"):
        bubble = st.empty()
        try:
            messages = [{"role": "system", "content": base_system_instructions()}] + st.session_state.chat_history
            if st.session_state.uploaded_text:
                messages.append({"role": "system", "content": f"Uploaded document content:\n{st.session_state.uploaded_text[:8000]}"})
            text, resp_obj = run_streamed_response(
                model_choice,
                messages=messages,
                tools=[{"type": "web_search"}]
            )
            web_sources, file_quotes = extract_sources_and_quotes(resp_obj)
            final_with_refs = ensure_references_section(text, file_quotes, web_sources)
            bubble.markdown(final_with_refs)
            st.session_state.chat_history.append({"role": "assistant", "content": final_with_refs})
        except Exception as e:
            bubble.error(f"Error: {e}")
