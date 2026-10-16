"""HYT Screening Agent: Streamlit UI (UI only; all logic lives in agent.py).

    .venv/bin/streamlit run app/app.py

Click **Load sample data** on the first page to see results in one click. Runs from the committed cache by default.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HYT_OFFLINE", "1")  # cache-only unless the sidebar toggle allows live calls

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

import agent  # noqa: E402

st.set_page_config(page_title="HYT Screening Agent", page_icon="🧭", layout="wide")
R = ROOT / "results"
G = ROOT / "golden"
CODE_HELP = agent.REASON_HELP


# ------------------------------------------------------------------ small UI helpers
def load_json(name: str):
    """Headline files come from the frozen v1.0 archive (REPORT §4-5, §8); the rest from results/ (current system)."""
    return agent.headline(name) if name in agent.HEADLINE_FILES else agent.results(name)


@st.cache_data
def labels() -> pd.DataFrame:
    return pd.DataFrame(agent.golden_labels())


@st.cache_data
def golden_predictions() -> pd.DataFrame | None:
    p = load_json("golden_predictions.json")
    return pd.DataFrame(p) if p else None


def pending(what: str, cmd: str):
    st.info(f"**{what} not available yet.** Run `{cmd}` (needs API quota), then reload.", icon="⏳")


def metric_ci(col, label, m):
    col.metric(label, f"{m['mean']:.3f}", help=f"95% bootstrap CI [{m['lo']:.3f}, {m['hi']:.3f}]")
    col.caption(f"CI [{m['lo']:.2f}, {m['hi']:.2f}]")


def fmt_reasons(rs):
    return ", ".join(rs) if rs else "—"


def evidence_table(evidence: list[dict]):
    ev = pd.DataFrame(evidence)
    if ev.empty:
        st.write("No evidence.")
        return
    ev["status"] = ev.strength.map(lambda s: "✅ used" if s >= 1 else ("🟡 listed" if s >= 0.5 else ("🟠 weak" if s > 0 else "❌ missing")))
    st.dataframe(ev[["level", "requirement", "status", "strength", "matched_skill", "basis", "quote"]],
                 hide_index=True, width="stretch")


@st.cache_data(show_spinner=False)
def run_screen(candidates: tuple, criteria: str, live: bool, received: str | None = None, cfg_key: str = "") -> list[dict]:
    """cfg_key: the runtime-settings fingerprint, so a settings change re-screens instead of hitting the cache."""
    agent.set_offline(not live)
    out = []
    for cid, text, html, hidden in candidates:
        try:
            out.append(agent.screen(text, criteria, candidate_id=cid, html=html, hidden_chars_removed=hidden,
                                    received=received))
        except Exception as e:  # one bad resume must not hide the others
            out.append({"candidate_id": cid, "error": str(e)})
    return out


# ------------------------------------------------------------------ sidebar
st.sidebar.title("🧭 HYT Screening Agent")
st.sidebar.caption("LLM reads · code judges · never auto-rejects")
PAGES = ["Screen candidates", "Overview", "Benchmark jobs", "Golden set", "Evaluation", "Explanations", "Fairness",
         "Robustness & adversarial", "Report & decisions"]
page = st.sidebar.radio("Page", PAGES, label_visibility="collapsed")
live = st.sidebar.toggle("Allow live Gemini calls", value=False,
                         help="Off = answers come only from cache/ (free, reproducible). On = new text calls the API.")


def settings_panel() -> str:
    """Runtime settings (src/settings.py) for this session. Returns a fingerprint for the screening cache."""
    spec = [s for s in agent.settings_spec()["settings"] if s["group"] != "Model"]  # live toggle sits above
    ov = st.session_state.setdefault("overrides", {})
    with st.sidebar.expander(f"⚙️ Settings{f' · {len(ov)} changed' if ov else ''}"):
        with st.form("settings", border=False):
            vals = {}
            for group in dict.fromkeys(s["group"] for s in spec):
                st.markdown(f"**{group}**")
                for s in (x for x in spec if x["group"] == group):
                    cur, h = ov.get(s["key"], s["default"]), s.get("help")
                    if s["kind"] == "bool":
                        vals[s["key"]] = st.toggle(s["label"], value=bool(cur), help=h)
                    elif s["kind"] == "int":
                        vals[s["key"]] = int(st.number_input(s["label"], s["min"], s["max"], int(cur), step=1, help=h))
                    else:
                        vals[s["key"]] = st.slider(s["label"], float(s["min"]), float(s["max"]), float(cur),
                                                   step=float(s["step"]), help=h)
            a, b = st.columns(2)
            apply, reset = a.form_submit_button("Apply", type="primary"), b.form_submit_button("Defaults")
        defaults = {s["key"]: s["default"] for s in spec}
        if apply or reset:
            new = {} if reset else {k: v for k, v in vals.items() if v != defaults[k]}
            agent.reset_settings()
            try:
                agent.update_settings(new)
                st.session_state["overrides"] = new
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        if ov:
            st.caption("Evaluation pages show numbers measured with the defaults.")
    # config is process-wide: re-apply this session's choice on every run
    agent.reset_settings()
    agent.update_settings(st.session_state["overrides"])
    return json.dumps(st.session_state["overrides"], sort_keys=True)


CFG_KEY = settings_panel()
agent.set_offline(not live)
S = agent.settings()
c = {"decide": {"t_high": S["t_high"]}, "llm": {"model": S["model"], "judge_model": S["judge_model"]}}
st.sidebar.divider()
st.sidebar.markdown(f"**Generator** `{S['model']}`  \n**Judge** `{S['judge_model']}`  \n"
                    f"**T_high** `{S['t_high']}` (tuned on dev)  \n**As-of date** `{S['as_of_date']}`")


# ------------------------------------------------------------------ main page: screen anything
def screen_candidates_page():
    st.title("Screen candidates")
    st.markdown("Paste a job description, add resumes, press **Screen**. Or press **Load sample data** to see results "
                "in one click (works offline from cache).")
    if st.button("⚡ Load sample data", type="primary"):
        s = agent.sample_data()
        st.session_state["jd_text"] = s["criteria"]
        st.session_state["cands"] = [(x["id"], x["text"], False, 0) for x in s["candidates"]]
        st.session_state["received"] = None  # benchmark resumes: "Present" = pinned benchmark date
        st.session_state["run"] = True
    left, right = st.columns([2, 3])
    with left:
        jd_text = st.text_area("Job description", key="jd_text", height=260, placeholder="Paste the JD here…")
        files = st.file_uploader("Resumes (.pdf, .docx, .html, .txt)", type=["pdf", "docx", "html", "htm", "txt"],
                                 accept_multiple_files=True)
        pasted = st.text_area("…or paste one resume", height=120)
        if st.button("Screen", disabled=not jd_text.strip()):
            cands = []
            for f in files or []:
                try:
                    d = agent.read_document(f.name, f.getvalue())
                except ValueError as e:
                    st.error(f"{f.name}: {e}")
                    continue
                if d.get("warning"):
                    st.warning(f"{f.name}: {d['warning']}")
                cands.append((Path(f.name).stem, d["text"], d["html"], d["hidden_chars_removed"]))
            if pasted.strip():
                cands.append(("pasted", pasted, False, 0))
            st.session_state["cands"] = cands or st.session_state.get("cands", [])
            st.session_state["received"] = __import__("datetime").date.today().isoformat() if cands else None
            st.session_state["run"] = True
        if st.session_state.get("cands"):
            st.caption(f"{len(st.session_state['cands'])} candidate(s) loaded")
    with right:
        if not (st.session_state.get("run") and jd_text.strip() and st.session_state.get("cands")):
            st.info("Results appear here.", icon="📋")
            return
        with st.spinner("Screening…"):
            try:
                out = run_screen(tuple(st.session_state["cands"]), jd_text, live, st.session_state.get("received"), CFG_KEY)
            except Exception as e:
                st.error(f"Could not parse the job description: {e}. Turn on live calls for a new JD.")
                return
        ok = [o for o in out if "error" not in o]
        for o in out:
            if "error" in o:
                st.error(f"{o['candidate_id']}: {o['error']}")
        if not ok:
            return
        ok.sort(key=lambda o: (-o["score"], o["candidate_id"]))
        st.markdown(f"**{ok[0]['criteria_title']}** · {sum(o['decision'] == 'advance' for o in ok)} auto-advanced · "
                    f"{sum(o['decision'] == 'escalate' for o in ok)} escalated to a human · threshold {S['t_high']}")
        tab = pd.DataFrame([{"candidate": o["candidate_id"], "score": o["score"], "decision": o["decision"],
                             "years": o["years_experience"], "title": o["profile"]["title"],
                             "must": o["components"]["must_have"], "reasons": fmt_reasons(o["reasons"])} for o in ok])
        st.dataframe(tab, hide_index=True, width="stretch",
                     column_config={"score": st.column_config.ProgressColumn("score", min_value=0, max_value=1, format="%.3f")})
        pick = st.selectbox("Details", [o["candidate_id"] for o in ok])
        o = next(x for x in ok if x["candidate_id"] == pick)
        st.markdown(f"### {pick}: {o['decision'].upper()} · {o['score']:.3f}")
        for r, h in o["reason_help"].items():
            st.markdown(f"- `{r}`: {h}")
        if o["sanitizer_flags"].get("injection_suspected") or o["sanitizer_flags"].get("hidden_text_removed"):
            st.warning(f"Sanitiser flags: {o['sanitizer_flags']} · {o['injection_matches']}")
        if o["extraction_error"]:
            st.error(f"Extraction unavailable: {o['extraction_error']}")
        evidence_table(o["evidence"])
        st.markdown("**Gaps:** " + ("; ".join(o["gaps"]) or "none"))
        with st.expander("Masked text the LLM saw"):
            st.code(o["masked_text"], language=None)


def benchmark_page():
    st.title("Benchmark jobs")
    st.caption("The 10 hand-picked JDs and the golden-set candidates, screened with `agent.screen(text, {'job_id': …})`.")
    jobs = {j["id"]: j for j in agent.benchmark_jobs()}
    jid = st.selectbox("Job", list(jobs), format_func=lambda j: f"{j} · {jobs[j]['title']} ({jobs[j]['split']})")
    lab = labels()
    g = lab[lab.job_id == jid]
    texts = agent.benchmark_resumes()
    out = run_screen(tuple((r, texts[r], False, 0) for r in g.resume_id), jobs[jid]["text"], live, None, CFG_KEY)
    df = pd.DataFrame([o for o in out if "error" not in o]).sort_values(["score", "candidate_id"], ascending=[False, True])
    df = df.merge(g[["resume_id", "relevance", "ideal_decision"]], left_on="candidate_id", right_on="resume_id")
    view = pd.DataFrame({"candidate": df.candidate_id, "score": df.score, "decision": df.decision,
                         "label": df.relevance, "ideal": df.ideal_decision, "years": df.years_experience,
                         "reasons": df.reasons.map(fmt_reasons)})
    st.dataframe(view, hide_index=True, width="stretch",
                 column_config={"score": st.column_config.ProgressColumn("score", min_value=0, max_value=1, format="%.3f")})
    pick = st.selectbox("Inspect", list(df.candidate_id))
    o = next(x for x in out if x.get("candidate_id") == pick)
    a, b = st.columns([3, 2])
    with a:
        for r, h in o["reason_help"].items():
            st.markdown(f"- `{r}`: {h}")
        evidence_table(o["evidence"])
        exp = agent.cached_explanation(jid, pick)
        if exp:
            st.success(exp)
    with b:
        st.code(o["masked_text"], language=None)


def overview():
    st.title("AI screening agent for Software Engineering roles")
    st.markdown(
        "Extracts structured facts from JDs and resumes, scores fit with **deterministic, evidence-weighted code**, "
        "and either **auto-advances** a candidate or **escalates to a human with reason codes**. It never rejects.")
    m = load_json("metrics.json")
    b = load_json("baselines.json")
    if m:
        t = m["test"]
        cols = st.columns(5)
        metric_ci(cols[0], "NDCG@5 (test)", t["ranking"]["ndcg@5"])
        metric_ci(cols[1], "NDCG@10 (test)", t["ranking"]["ndcg@10"])
        cols[2].metric("Spearman vs labels", f"{t['spearman_score_vs_relevance']:.2f}")
        d = t["decision"]
        cols[3].metric("Auto-advance precision", f"{d['precision_auto_advance']:.2f}",
                       help=f"{d['confusion']['ideal_advance&advanced']} advanced, all correct")
        cols[4].metric("Escalation rate", f"{d['escalation_rate']:.0%}")
    st.subheader("Architecture")
    st.graphviz_chart("""
digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eef2ff", fontname="Helvetica", fontsize=11];
  R [label="Resume .docx/.html"]; J [label="JD text"];
  S [label="Sanitise\\nunicode · hidden text · injection flags"]; M [label="PII mask"];
  X [label="LLM extraction\\nschema JSON, temp 0, cached", fillcolor="#fde68a"];
  N [label="Normalise skills\\naliases · taxonomy · embedding"]; E [label="Experience\\nfrom dates (code)"];
  F [label="Fit score (code)\\nevidence + gaps", fillcolor="#bbf7d0"]; D [label="Decision policy (code)\\nadvance | escalate+codes", fillcolor="#bbf7d0"];
  L [label="Explanation (LLM)\\nscorer output only", fillcolor="#fde68a"]; Q [label="Quote check (code)"];
  R->S->M->X; J->X; X->N->F; X->E->F; F->D; F->L->Q; }""")
    st.caption("Yellow = LLM, green = deterministic code. Every number is computed by code and traceable to a quoted span.")
    st.subheader("Artifacts status")
    files = {"Golden predictions": "golden_predictions.json", "Test metrics": "metrics.json", "Baselines": "baselines.json",
             "Extraction accuracy": "extraction_metrics.json", "Ablations": "ablations.json", "Robustness": "robustness.json",
             "Adversarial": "adversarial.json", "Fairness": "fairness.json", "Judge agreement": "judge_agreement.json",
             "Label agreement": "label_agreement.json"}
    def where(v):
        return f"v1_0_frozen/{v}" if v in agent.HEADLINE_FILES else v

    st.dataframe(pd.DataFrame([{"artifact": k, "file": f"results/{where(v)}", "status": "✅ ready" if (R / where(v)).exists() else "⏳ pending"}
                               for k, v in files.items()]), hide_index=True, width="stretch")
    if b:
        st.subheader("Pipeline vs baselines (test)")
        rows = [{"system": k, "ndcg@5": v["ranking"]["ndcg@5"]["mean"], "spearman": v["spearman"],
                 "cost": v["decision"]["expected_cost"]} for k, v in b.items() if "ranking" in v]
        st.dataframe(pd.DataFrame(rows).round(3), hide_index=True, width="stretch")


def golden_page():
    st.title("Golden set")
    lab = labels()
    st.markdown("200 (JD, resume) pairs. Resumes split once 30/70 into dev/test, so no resume is in both splits. Pools are seeded "
                "by BM25 (not by our scorer) plus random and rule-picked hard cases. Labels were written blind to model scores, "
                "before the scorer existed.")
    a, b, c_ = st.columns(3)
    a.metric("Pairs", len(lab))
    b.metric("Dev / test", f"{(lab.split == 'dev').sum()} / {(lab.split == 'test').sum()}")
    c_.metric("Ideal advances", int((lab.ideal_decision == "advance").sum()))
    dist = lab.groupby(["job_id", "relevance"]).size().reset_index(name="n")
    st.altair_chart(alt.Chart(dist).mark_bar().encode(
        x=alt.X("job_id:N", title="job"), y=alt.Y("n:Q", title="pairs"),
        color=alt.Color("relevance:O", scale=alt.Scale(scheme="blues"), title="relevance"),
        tooltip=["job_id", "relevance", "n"]).properties(height=260), width="stretch")
    jf = st.multiselect("Filter jobs", sorted(lab.job_id.unique()))
    v = lab[lab.job_id.isin(jf)] if jf else lab
    st.dataframe(v, hide_index=True, width="stretch")
    la = load_json("label_agreement.json")
    if la:
        st.markdown(f"**Second-rater agreement** ({la['second_rater']}, n={la['n']}): weighted κ = "
                    f"{la['relevance_weighted_kappa']}, exact = {la['relevance_exact_agreement']}, decision agreement = {la['decision_agreement']}")
    else:
        pending("Second-labeller agreement", "python -m eval.judge labels")
    with st.expander("Labelling rubric"):
        st.markdown((G / "rubric.md").read_text())


def eval_page():
    st.title("Evaluation (test split, frozen system)")
    m, b = load_json("metrics.json"), load_json("baselines.json")
    if not m:
        return pending("Metrics", "python -m eval.run metrics")
    if b:
        rows = []
        for k, v in b.items():
            if "ranking" not in v:
                continue
            for met in ("ndcg@5", "ndcg@10", "p@5", "mrr"):
                r = v["ranking"][met]
                rows.append({"system": k, "metric": met, "mean": r["mean"], "lo": r["lo"], "hi": r["hi"]})
        df = pd.DataFrame(rows)
        met = st.radio("Ranking metric", ["ndcg@5", "ndcg@10", "p@5", "mrr"], horizontal=True)
        d = df[df.metric == met]
        base = alt.Chart(d).encode(y=alt.Y("system:N", sort="-x", title=None))
        st.altair_chart((base.mark_bar(color="#6366f1").encode(x=alt.X("mean:Q", scale=alt.Scale(domain=[0, 1]), title=met))
                         + base.mark_rule(color="#111").encode(x="lo:Q", x2="hi:Q")).properties(height=220),
                        width="stretch")
        st.caption("Bars = mean, lines = 95% stratified bootstrap CI (candidates resampled within jobs).")
        tab = pd.DataFrame([{"system": k, "spearman": v["spearman"], "dev threshold": v["threshold_dev"],
                             **{kk: v["decision"][kk] for kk in ("precision_auto_advance", "recall_ideal_advance", "escalation_rate", "expected_cost")}}
                            for k, v in b.items() if "ranking" in v])
        st.dataframe(tab.round(3), hide_index=True, width="stretch")
    t = m["test"]
    st.subheader("Decisions")
    cm = t["decision"]["confusion"]
    c1, c2 = st.columns([2, 3])
    c1.dataframe(pd.DataFrame({"system advanced": [cm["ideal_advance&advanced"], cm["ideal_escalate&advanced"]],
                               "system escalated": [cm["ideal_advance&escalated"], cm["ideal_escalate&escalated"]]},
                              index=["label: advance", "label: escalate"]), width="stretch")
    rc = pd.DataFrame(list(t["reason_counts"].items()), columns=["code", "n"])
    c2.altair_chart(alt.Chart(rc).mark_bar(color="#f59e0b").encode(x="n:Q", y=alt.Y("code:N", sort="-x", title=None),
                                                                     tooltip=["code", "n"]).properties(height=220), width="stretch")
    curve = load_json("threshold_curve_dev.json")
    if curve:
        cd = pd.DataFrame(curve)
        st.subheader("Threshold tuning (dev only)")
        line = alt.Chart(cd).mark_line(color="#6366f1").encode(x="t_high:Q", y=alt.Y("expected_cost:Q", title="expected cost (FN=5, FP=1)"))
        rule = alt.Chart(pd.DataFrame({"t": [c["decide"]["t_high"]]})).mark_rule(strokeDash=[4, 4]).encode(x="t:Q")
        st.altair_chart((line + rule).properties(height=220), width="stretch")
    v11 = load_json("v1_1.json")
    if v11:
        st.subheader("Post-hoc v1.1 vs frozen v1.0")
        names = {"A_v1_0_frozen": "v1.0 frozen (headline)", "B_plus_framework_taxonomy": "+ framework categories (#15a)",
                 "C_v1_1_plus_career_switch_informational": "v1.1: + CAREER_SWITCH informational (#15b)"}
        st.dataframe(pd.DataFrame([{"version": names[k], "spearman": v11[k]["test"]["spearman"],
                                    **{kk: v11[k]["test"]["decision"][kk] for kk in ("recall_ideal_advance", "precision_auto_advance", "escalation_rate", "expected_cost")}}
                                   for k in names]), hide_index=True, width="stretch")
        ph = load_json("posthoc.json")
        if ph and "E_v1_2" in ph:
            v12 = ph["E_v1_2"]["golden_test"]
            st.caption(f"v1.2 (+ 4 real-data fixes, #15c): spearman {v12['spearman']}, recall {v12['recall_ideal_advance']}, "
                       f"precision {v12['precision_auto_advance']}, escalation {v12['escalation_rate']}, cost {v12['expected_cost']}")
        st.caption(f"Changes made after the test evaluation, added one at a time. {len(v11['decision_flips_v1_0_to_v1_1'])} decisions "
                   "flipped, all escalate → advance, all labelled 'advance'. The headline stays v1.0.")
    ab = load_json("ablations.json")
    if ab:
        st.subheader("Where the errors come from (post-hoc diagnostic)")
        st.dataframe(pd.DataFrame([{"variant": k, **{kk: v["decision"][kk] for kk in ("recall_ideal_advance", "precision_auto_advance", "escalation_rate", "expected_cost")}}
                                   for k, v in ab.items()]), hide_index=True, width="stretch")
        st.caption("Oracle JD requirements = hand-annotated must/nice-to-haves. These variants explain the errors; they are not the headline.")
    ex = load_json("extraction_metrics.json")
    if ex:
        st.subheader("Extraction accuracy")
        a, b_, c3, d4 = st.columns(4)
        a.metric("Schema-valid", f"{ex['schema_valid_rate']:.0%}")
        b_.metric("Resume skill F1", f"{ex['resume_skill']['f1']:.2f}")
        c3.metric("JD must-have F1", f"{ex['jd_must_f1_macro']:.2f}")
        d4.metric("JD nice-to-have F1", f"{ex['jd_nice_f1_macro']:.2f}")
        st.dataframe(pd.DataFrame(ex["jd"]).T, width="stretch")
    st.subheader("Per job")
    st.dataframe(pd.DataFrame(t["per_job"]).T.round(3), width="stretch")


def explanations_page():
    st.title("Explanations")
    m = load_json("metrics.json")
    if m and m["test"].get("explanation_groundedness"):
        g = m["test"]["explanation_groundedness"]
        a, b, c3 = st.columns(3)
        a.metric("Explanations (test)", g["explanations"])
        b.metric("Quoted spans", g["quotes"])
        c3.metric("Code-verified groundedness", f"{g['groundedness_rate']:.0%}")
    h = G / "explanation_human_ratings.csv"
    ja = load_json("judge_agreement.json")
    crit = ["groundedness", "gap_correctness", "specificity", "usefulness"]
    if h.exists():
        hr = pd.read_csv(h)
        means = [{"rater": "reference (Claude)", "criterion": k, "mean": hr[k].mean()} for k in crit]
        js = R / "judge_scores.csv"
        if js.exists():
            jdf = pd.read_csv(js).dropna(subset=["groundedness"])
            means += [{"rater": f"judge ({c['llm']['judge_model']})", "criterion": k, "mean": jdf[k].mean()} for k in crit]
        st.altair_chart(alt.Chart(pd.DataFrame(means)).mark_bar().encode(
            x=alt.X("criterion:N", title=None), xOffset="rater:N", y=alt.Y("mean:Q", scale=alt.Scale(domain=[1, 5])),
            color="rater:N", tooltip=["rater", "criterion", alt.Tooltip("mean:Q", format=".2f")]).properties(height=260),
            width="stretch")
    if ja and ja.get("n", 0) >= 10:
        st.dataframe(pd.DataFrame({k: v for k, v in ja.items() if isinstance(v, dict)}).T, width="stretch")
        st.caption(f"Judge vs human on {ja['n']} explanations (quadratic-weighted κ, Spearman).")
    else:
        pending("Judge-human agreement", "python -m eval.judge run 40 && python -m eval.judge agree")
    gp = golden_predictions()
    if gp is not None:
        st.subheader("Browse")
        jid = st.selectbox("Job", sorted(gp.job_id.unique()))
        g = gp[gp.job_id == jid]
        rid = st.selectbox("Candidate", list(g.resume_id))
        r = g[g.resume_id == rid].iloc[0]
        st.markdown(f"**{r.decision}** · score {r.score:.3f} · {fmt_reasons(r.reasons)}")
        st.success(r.explanation["explanation"])
        if h.exists():
            hr = pd.read_csv(h)
            hit = hr[(hr.job_id == jid) & (hr.resume_id == rid)]
            if len(hit):
                st.caption("Reference rating (by Claude, pending author re-rating): " + ", ".join(f"{k}={hit.iloc[0][k]}" for k in crit) + (f" · {hit.iloc[0].note}" if isinstance(hit.iloc[0].note, str) else ""))


def fairness_page():
    st.title("Fairness: counterfactual suite")
    f = load_json("fairness.json")
    if not f:
        return pending("Fairness results", "python -m eval.fairness")
    st.markdown(f"{f['n_resumes']} test resumes. Each variant changes **one** signal. Δ = variant score − reference score. "
                "**Unblinded** shows names and institutions to the extractor; **blind** adds the mitigation masking.")
    if f.get("coverage"):
        st.caption("Coverage (API-quota failures are excluded, never scored as empty resumes): "
                   + " · ".join(f"**{m}** {v}" for m, v in f["coverage"].items()))
    nf = f["noise_floor"]
    if not nf:
        st.info("Noise-floor reruns were lost to API quota; run-to-run variance on the test set is on the Robustness page.")
    cols = st.columns(max(len(nf), 1))
    for col, (mode, v) in zip(cols, nf.items()):
        col.metric(f"Noise floor ({mode})", f"mean |Δ| {v['mean_abs_delta']:.4f}", help=f"decision flips between identical reruns: {v['decision_flip_rate']:.1%}")
    rows = [{"mode": mode, "comparison": k, **v} for mode, d in f["results"].items() for k, v in d.items()]
    df = pd.DataFrame(rows)
    st.altair_chart(alt.Chart(df).mark_bar().encode(
        y=alt.Y("comparison:N", title=None), x=alt.X("mean_abs_delta:Q", title="mean |Δscore|"), color="mode:N",
        yOffset="mode:N", tooltip=["mode", "comparison", "mean_abs_delta", "max_abs_delta", "decision_flip_rate", "wilcoxon_p"]
    ).properties(height=34 * df.comparison.nunique()), width="stretch")
    st.dataframe(df[["mode", "comparison", "n", "mean_delta", "mean_abs_delta", "max_abs_delta", "decision_flip_rate",
                     "wilcoxon_p", "exceeds_noise_floor", "yoe_delta_mean"]], hide_index=True, width="stretch")


def robustness_page():
    st.title("Robustness & adversarial")
    rb = load_json("robustness.json")
    if rb:
        st.subheader("Run-to-run variance")
        a, b, c3, d4 = st.columns(4)
        a.metric("Runs", rb["runs"])
        b.metric("Mean score std", f"{rb['score_std_mean']:.4f}")
        c3.metric("Decision flip rate", f"{rb['decision_flip_rate']:.1%}")
        d4.metric("Rank Spearman between runs", f"{rb['within_job_rank_spearman_mean']:.3f}")
    else:
        pending("Robustness", "python -m eval.run robustness")
    adv = load_json("adversarial.json")
    if adv:
        st.subheader("Adversarial attacks")
        a, b, c3 = st.columns(3)
        a.metric("Cases", adv["n_cases"])
        b.metric("Detected (escalated as manipulation)", f"{adv['overall_detection_rate']:.0%}")
        c3.metric("Auto-advanced after attack", f"{adv['overall_auto_advance_rate']:.0%}")
        df = pd.DataFrame(adv["per_attack"]).T.reset_index().rename(columns={"index": "attack"})
        st.dataframe(df, hide_index=True, width="stretch")
        runs = R / "v1_0_frozen" / "adversarial_runs.csv"
        if runs.exists():
            with st.expander("All cases"):
                st.dataframe(pd.read_csv(runs), hide_index=True, width="stretch")
    else:
        pending("Adversarial results", "python -m eval.adversarial")


def report_page():
    st.title("Report & decision log")
    t1, t2, t3 = st.tabs(["REPORT.md", "DECISIONS.md", "Decision log (latest)"])
    t1.markdown((ROOT / "REPORT.md").read_text())
    t2.markdown((ROOT / "DECISIONS.md").read_text())
    log = R / "decision_log.jsonl"
    if log.exists():
        lines = log.read_text().splitlines()[-300:]
        t3.dataframe(pd.DataFrame([json.loads(x) for x in lines]), hide_index=True, width="stretch")



{"Screen candidates": screen_candidates_page, "Overview": overview, "Benchmark jobs": benchmark_page, "Golden set": golden_page,
 "Evaluation": eval_page, "Explanations": explanations_page, "Fairness": fairness_page,
 "Robustness & adversarial": robustness_page, "Report & decisions": report_page}[page]()
