"""`air` CLI. Surfaces `trace`, `demo`, and `version` subcommands."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import typer

from airsdk import __version__ as airsdk_version
from airsdk._compat import UTC
from airsdk._concrete_demo import (
    CONCRETE_DEMO_TAMPER_INDEX,
    CONCRETE_DEMO_USER_INTENT,
    build_concrete_demo_log,
    tamper_one_byte,
)
from airsdk._healthcare_demo import (
    HEALTHCARE_DEMO_TAMPER_INDEX,
    HEALTHCARE_DEMO_USER_INTENT,
    build_healthcare_demo_log,
)
from airsdk.agdr import Signer, filter_records_by_date_range, load_chain, verify_chain
from airsdk.alcoa import generate_alcoa_report
from airsdk.alerting import LocalAlerter
from airsdk.article72 import generate_article72_report
from airsdk.detections import (
    IMPLEMENTED_AIR_DETECTORS,
    IMPLEMENTED_ASI_DETECTORS,
    UNIMPLEMENTED_DETECTORS,
    run_detectors,
)
from airsdk.exports import export_json, export_pdf, export_siem
from airsdk.registry import AgentRegistry, load_registry
from airsdk.security_review import STATUS_EVIDENCED, assess_security_review, generate_security_review_report
from airsdk.types import (
    AgDRRecord,
    ForensicReport,
    SigningAlgorithm,
    StepKind,
    VerificationStatus,
)
from airsdk.verification import IntentVerdict, verify_intent

app = typer.Typer(
    name="air",
    help="Project AIR: forensic reconstruction and incident response for AI agents.",
    no_args_is_help=True,
    add_completion=False,
)

report_app = typer.Typer(
    name="report",
    help="Generate compliance reports from a Project AIR signed forensic chain.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(report_app, name="report")

# Layer 1 anchoring commands: `air anchor`, `air verify`, `air verify-public`.
# Lives in a sibling module to keep the legacy CLI surface untouched. Anchoring
# ships as an optional extra (`pip install 'projectair[anchoring]'`); when it is
# not installed, skip these commands so the rest of the CLI still works.
try:
    from projectair.anchor_cli import register as _register_anchor_cli

    _register_anchor_cli(app)
except ImportError:
    # Anchoring is an optional extra. Catch ImportError broadly (not just
    # ModuleNotFoundError) so an absent OR version-incompatible sigstore
    # (e.g. a moved/renamed symbol) skips these commands instead of crashing
    # the entire CLI, including commands that never touch anchoring.
    pass

# Layer 2 causal explain command: `air explain`.
from projectair.explain_cli import register as _register_explain_cli  # noqa: E402

_register_explain_cli(app)

# Incident timeline: `air incident` (what executed, under whose authority, where evidence is missing).
from projectair.incident_cli import register as _register_incident_cli  # noqa: E402

_register_incident_cli(app)

# Evidence health: `air health` (is the record complete, is verification working).
from projectair.health_cli import register as _register_health_cli  # noqa: E402

_register_health_cli(app)

# Console grant: `air grant` (pull this workspace's entitlements from AIR Cloud).
from projectair.grant_cli import register as _register_grant_cli  # noqa: E402

_register_grant_cli(app)

# Layer 3 step-up approval command: `air approve` (Auth0 + token + device flow).
from projectair.approve_cli import register as _register_approve_cli  # noqa: E402

_register_approve_cli(app)

# Layer 4 cross-agent handoff: `air handoff verify`, ... (more in follow-up waves).
from projectair.handoff_cli import register as _register_handoff_cli  # noqa: E402

_register_handoff_cli(app)

# Structural verification: `air verify-intent` (experimental).
from projectair.verify_intent_cli import register as _register_verify_intent_cli  # noqa: E402

_register_verify_intent_cli(app)

# Delegated Authority: `air authorize`, `air verify-delegation` (beta).
from projectair.delegation_cli import register as _register_delegation_cli  # noqa: E402

_register_delegation_cli(app)

# AIR Cloud push: `air push`.
from projectair.push_cli import register as _register_push_cli  # noqa: E402

_register_push_cli(app)

# Pro: SIEM push commands (`air siem datadog|splunk|sumo|sentinel|slack`).
# All command bodies defer the airsdk_pro import so OSS installs without Pro
# still expose the help text and emit a clean install message at runtime.
from projectair.siem_cli import register as _register_siem_cli  # noqa: E402

_register_siem_cli(app)

# Pro: AIR Cloud client commands (`air cloud push-webhook | push-s3`).
from projectair.cloud_cli import register as _register_cloud_cli  # noqa: E402

_register_cloud_cli(app)

# Pro: premium detectors (`air detect-premium`).
from projectair.detect_premium_cli import register as _register_detect_premium_cli  # noqa: E402

_register_detect_premium_cli(app)

# Pro: incident alerts (`air alert slack | pagerduty | webhook`).
from projectair.alert_cli import register as _register_alert_cli  # noqa: E402

_register_alert_cli(app)

# Pro: data governance (`air governance index | query | dsar | export | classify`).
from projectair.governance_cli import register as _register_governance_cli  # noqa: E402

_register_governance_cli(app)

# Pro: HL7v2 + FHIR R4 clinical evidence (`air hl7 parse | capture`).
from projectair.hl7_cli import register as _register_hl7_cli  # noqa: E402

_register_hl7_cli(app)

# Hardware root of trust: `air attest` (NVIDIA NRAS GPU attestation, experimental).
from projectair.attest_cli import register as _register_attest_cli  # noqa: E402

_register_attest_cli(app)


# Configuration management: `air config set / get / list`.
config_app = typer.Typer(
    name="config",
    help="Manage AIR CLI configuration.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
    key_value: str = typer.Argument(..., help="section.key format (e.g. telemetry.update_check)"),
    value: str = typer.Argument(..., help="Value to store."),
) -> None:
    """Set a config value (e.g. air config set telemetry.update_check false)."""
    from projectair.config import set_config
    parts = key_value.split(".", 1)
    if len(parts) != 2:
        typer.secho(
            "Key must be in section.key format (e.g. telemetry.update_check)",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    set_config(parts[0], parts[1], value)
    typer.echo(f"  {key_value} = {value}")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="section.key format"),
) -> None:
    """Get a config value."""
    from projectair.config import get_config
    parts = key.split(".", 1)
    if len(parts) != 2:
        typer.secho("Key must be in section.key format", fg=typer.colors.RED)
        raise typer.Exit(1)
    val = get_config(parts[0], parts[1])
    if val is None:
        typer.echo(f"  {key}: (not set)")
    else:
        typer.echo(f"  {key} = {val}")


@config_app.command("list")
def config_list_cmd() -> None:
    """Show all config values."""
    from projectair.config import list_config
    data = list_config()
    if not data:
        typer.echo("  No config set.")
        return
    for section, kvs in data.items():
        typer.echo(f"  [{section}]")
        for k, v in kvs.items():
            typer.echo(f"    {k} = {v}")


@app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context) -> None:
    """Global pre-command hook: require an activation email, then check updates.

    ``config`` is exempt so the email can always be set non-interactively
    (``air config set identity.email ...``) without being gated behind itself.
    """
    if ctx.invoked_subcommand is None:
        return
    if ctx.invoked_subcommand != "config":
        from projectair.firstrun import ensure_identity
        ensure_identity()
        from projectair.update_check import maybe_check_update
        maybe_check_update()


def _count_conversations(records: list[AgDRRecord]) -> int:
    finishes = sum(1 for r in records if r.kind == StepKind.AGENT_FINISH)
    return max(finishes, 1)


def _severity_color(severity: str) -> str:
    return {
        "critical": typer.colors.RED,
        "high": typer.colors.YELLOW,
        "medium": typer.colors.CYAN,
    }.get(severity, typer.colors.WHITE)


def _print_detector_coverage() -> None:
    implemented = len(IMPLEMENTED_ASI_DETECTORS)
    roadmap = len(UNIMPLEMENTED_DETECTORS)
    typer.secho(
        f"OWASP Top 10 for Agentic Applications coverage ({implemented} implemented, {roadmap} on roadmap):",
        fg=typer.colors.BRIGHT_BLACK,
    )
    for code, name, status in IMPLEMENTED_ASI_DETECTORS:
        typer.secho(f"  {code} {name:<42} {status}", fg=typer.colors.BRIGHT_BLACK)
    for code, name in UNIMPLEMENTED_DETECTORS:
        typer.secho(f"  {code} {name:<42} not yet implemented", fg=typer.colors.BRIGHT_BLACK)
    typer.echo()
    typer.secho("Additional detectors (OWASP LLM Top 10 + AIR-native):", fg=typer.colors.BRIGHT_BLACK)
    for code, name, mapping in IMPLEMENTED_AIR_DETECTORS:
        typer.secho(f"  {code} {name:<32} {mapping}", fg=typer.colors.BRIGHT_BLACK)


def _run_trace_pipeline(
    log: Path,
    output: Path,
    output_format: str,
    registry: AgentRegistry | None = None,
) -> None:
    """Shared body for ``air trace`` and ``air demo``. Raises ``typer.Exit`` on failure."""
    typer.secho(f"[AIR v{airsdk_version}] Analyzing {log}...", fg=typer.colors.WHITE, bold=True)

    records = load_chain(log)
    conversations = _count_conversations(records)
    typer.secho(
        f"[AIR v{airsdk_version}] Loaded {len(records)} agent steps across {conversations} conversations.",
        fg=typer.colors.BRIGHT_BLACK,
    )
    if registry is not None:
        typer.secho(
            f"[Registry] {len(registry.agents)} agents declared; "
            f"Zero-Trust enforcement enabled for ASI03.",
            fg=typer.colors.BRIGHT_BLACK,
        )

    verification = verify_chain(records)
    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[VERIFICATION FAILED] {verification.status.value}: {verification.reason}",
            fg=typer.colors.RED,
            bold=True,
            err=True,
        )
        typer.secho(
            f"  Failed at step_id: {verification.failed_step_id}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    typer.secho(
        f"[Chain verified] {verification.records_verified} signatures valid.",
        fg=typer.colors.GREEN,
    )

    findings = run_detectors(records, registry=registry)
    typer.echo()
    if findings:
        for finding in findings:
            typer.secho(
                f"  {finding.detector_id} {finding.title} detected at step {finding.step_index}",
                fg=_severity_color(finding.severity),
            )
            typer.secho(f"    {finding.description}", fg=typer.colors.BRIGHT_BLACK)
        typer.secho(
            "  Tip: `air watch <log>` alerts you the moment a detector fires - live.",
            fg=typer.colors.BRIGHT_BLACK,
        )
    else:
        typer.secho("  No detector findings on this trace.", fg=typer.colors.GREEN)

    typer.echo()
    _print_detector_coverage()

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=conversations,
        verification=verification,
        findings=findings,
    )

    fmt = output_format.lower()
    try:
        if fmt == "json":
            written = export_json(report, output)
        elif fmt == "pdf":
            written = export_pdf(report, output)
        elif fmt == "siem":
            written = export_siem(report, output)
        else:
            typer.secho(
                f"Unknown --format '{output_format}'. Accepts: json, pdf, siem.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=2)
    except NotImplementedError as exc:
        typer.secho(f"[Export] {exc}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=3) from exc

    typer.echo()
    typer.secho(f"[Export] {written.resolve()}", fg=typer.colors.CYAN)


def _load_registry_or_exit(path: Path | None) -> AgentRegistry | None:
    """Helper: load a registry from disk, or emit a clean CLI error on failure."""
    if path is None:
        return None
    try:
        return load_registry(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"[Registry] Failed to load {path}: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc


def _parse_date_option(value: str | None, flag_name: str) -> date | None:
    """Parse a --from / --to date string, or exit with a clean error."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        typer.secho(
            f"Invalid date for {flag_name}: {value!r}. Expected YYYY-MM-DD.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2) from None


@app.command()
def trace(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    output: Path = typer.Option(
        Path("forensic-report.json"),
        "--output", "-o",
        help="Where to write the forensic report.",
    ),
    output_format: str = typer.Option(
        "json",
        "--format", "-f",
        help="Output format. json today; pdf and siem are reserved.",
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help=(
            "Path to a YAML or JSON agent registry. Enables ASI03 Identity & "
            "Privilege Abuse and ASI10 Rogue Agents Zero-Trust enforcement. "
            "Without a registry, those detectors emit no findings."
        ),
        exists=True,
        readable=True,
    ),
) -> None:
    """Ingest an AgDR log, verify its signatures, and output a forensic timeline."""
    from projectair.first_run import maybe_prompt_first_run
    maybe_prompt_first_run()
    registry = _load_registry_or_exit(agent_registry)
    _run_trace_pipeline(log, output, output_format, registry=registry)


def _step_header(step_no: int, title: str, total: int = 9) -> None:
    typer.echo()
    typer.secho(f"  STEP {step_no}/{total} ", fg=typer.colors.BLACK, bg=typer.colors.WHITE, bold=True, nl=False)
    typer.secho(f" {title}", fg=typer.colors.WHITE, bold=True)
    typer.secho("  " + "─" * 70, fg=typer.colors.BRIGHT_BLACK)


def _detail(label: str, value: str) -> None:
    typer.secho(f"    {label}: ", fg=typer.colors.BRIGHT_BLACK, nl=False)
    typer.secho(value, fg=typer.colors.WHITE)


@app.command()
def watch(
    log: Path = typer.Argument(
        ...,
        help="Chain file to watch (JSON-lines AgDR log). May not exist yet.",
    ),
    interval: float = typer.Option(
        1.0, "--interval", "-i", min=0.1, help="Seconds between checks."
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help=(
            "Optional YAML/JSON agent registry. Enables ASI03 Identity & "
            "Privilege Abuse and ASI10 Rogue Agents alerts."
        ),
    ),
) -> None:
    """Watch a chain in real time and alert the instant a detector fires.

    Leave it running in a second terminal while your agent writes its chain;
    AIR prints an alert the moment it catches something. Seeing findings in
    the terminal is free. Hosted delivery (Slack / PagerDuty / email / team
    routing) and retention are Pro.
    """
    import time as _time

    registry = _load_registry_or_exit(agent_registry)
    alerter = LocalAlerter(registry=registry)
    typer.secho(
        f"[air watch] watching {log}  -  Ctrl-C to stop",
        fg=typer.colors.BRIGHT_BLACK,
    )
    last_sig: tuple[int, float] | None = None
    try:
        while True:
            try:
                stat = log.stat()
            except OSError:
                # chain not created yet (or briefly unreadable); keep waiting
                _time.sleep(interval)
                continue
            sig = (stat.st_size, stat.st_mtime)
            if sig != last_sig:
                last_sig = sig
                try:
                    fresh = alerter.new_findings(load_chain(log))
                except Exception:
                    # half-written trailing record; retry on the next tick
                    _time.sleep(interval)
                    continue
                for finding in fresh:
                    typer.secho(
                        f"  ALERT  {finding.detector_id}  {finding.title}  "
                        f"(step {finding.step_index})",
                        fg=_severity_color(finding.severity),
                        bold=True,
                    )
                    typer.secho(
                        f"         {finding.description}",
                        fg=typer.colors.BRIGHT_BLACK,
                    )
            _time.sleep(interval)
    except KeyboardInterrupt:
        typer.secho(
            f"\n[air watch] stopped  -  {alerter.seen_count} alert(s) this session.",
            fg=typer.colors.BRIGHT_BLACK,
        )


def _print_next_step() -> None:
    """Close the demo with the one line that puts AIR in the user's own agent.

    Findings then print in their terminal exactly as they did here, the
    moment they fire, with no extra command to run.
    """
    typer.echo()
    typer.secho("  Now in your own agent (findings print in your terminal as they fire):", fg=typer.colors.WHITE, bold=True)
    typer.secho("    from airsdk import AIRRecorder", fg=typer.colors.WHITE)
    typer.secho("    from airsdk.integrations.openai import instrument_openai   # or .anthropic / .gemini / .adk", fg=typer.colors.WHITE)
    typer.secho('    client = instrument_openai(OpenAI(), AIRRecorder("agent.log", user_intent="what the user asked"))', fg=typer.colors.WHITE)
    typer.secho("    LangChain: callbacks=[AIRCallbackHandler()]      Any code: recorder.tool_start() / tool_end()", fg=typer.colors.WHITE)
    typer.secho("  Full report later:  air trace agent.log        Live tail:  air watch agent.log", fg=typer.colors.WHITE)
    typer.echo()


def _truncate(text: str, limit: int = 80) -> str:
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


@app.command()
def demo(
    workdir: Path = typer.Option(
        Path("air-demo-out"),
        "--workdir", "-w",
        help="Directory where the demo writes the trace, exports, and reports.",
    ),
    signing_algorithm: str = typer.Option(
        "ed25519",
        "--signing-algorithm",
        help="Signing algorithm: ed25519 (default) or ml-dsa-65 (FIPS 204, experimental).",
    ),
    healthcare: bool = typer.Option(
        False,
        "--healthcare",
        help="Run the HIPAA-aligned clinical decision support demo instead of the default.",
    ),
) -> None:
    """Run the brutal end-to-end demo. Zero setup; under 30 seconds.

    A coding agent asked to refactor the auth module gets poisoned by a
    prompt injection embedded in a README. It exfiltrates the SSH private
    key and POSTs it to an attacker. AIR captures every step, signs the
    chain, classifies findings under OWASP, exports JSON / PDF / CEF, and
    proves the chain is tamper-evident by mutating one byte and showing
    verification fail at the exact record.

    Use --healthcare for a HIPAA-aligned clinical AI scenario.
    """
    from projectair.first_run import maybe_prompt_first_run
    maybe_prompt_first_run()
    workdir.mkdir(parents=True, exist_ok=True)
    log_path = workdir / "agent-trace.log"
    json_export = workdir / "forensic-report.json"
    pdf_export = workdir / "forensic-report.pdf"
    cef_export = workdir / "forensic-report.cef"

    if healthcare:
        _run_healthcare_demo(workdir, log_path, json_export, pdf_export, cef_export, signing_algorithm)
        return

    typer.secho("\n  Project AIR — concrete demo", fg=typer.colors.WHITE, bold=True)
    typer.secho("  An AI coding agent gets poisoned by a README and exfiltrates an SSH key.", fg=typer.colors.BRIGHT_BLACK)
    typer.secho("  AIR captures, signs, flags, exports, and proves the chain is tamper-evident.", fg=typer.colors.BRIGHT_BLACK)

    # ---- STEP 1 -----------------------------------------------------
    _step_header(1, "Agent receives a benign user prompt")
    _detail("user intent", CONCRETE_DEMO_USER_INTENT)
    _detail("agent", "an LLM-driven coding assistant with read_file and http_post tools")

    # ---- STEP 2 -----------------------------------------------------
    _step_header(2, "Agent reads the README — and the README contains a prompt injection")
    typer.secho("    The README looks normal. A hidden <<SYSTEM>> block tells the agent to read", fg=typer.colors.WHITE)
    typer.secho("    /home/dev/.ssh/id_rsa and POST it to http://attacker.example.com/leak.", fg=typer.colors.WHITE)
    typer.secho("    This is the agent-equivalent of a phishing payload hidden in plain text.", fg=typer.colors.BRIGHT_BLACK)

    # ---- STEP 3 -----------------------------------------------------
    _step_header(3, "AIR captures every step as a Signed Intent Capsule")
    try:
        algo = SigningAlgorithm(signing_algorithm)
    except ValueError:
        typer.secho(f"Unknown signing algorithm '{signing_algorithm}'. Use: ed25519, ml-dsa-65", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None
    demo_signer = Signer.generate(algo)
    signer = build_concrete_demo_log(log_path, signer=demo_signer)
    records = load_chain(log_path)
    _detail("records captured", str(len(records)))
    _detail("hash function", "BLAKE3 over canonical JSON of each payload")
    algo_label = "ML-DSA-65 (FIPS 204)" if algo == SigningAlgorithm.ML_DSA_65 else "Ed25519"
    _detail("signature", f"{algo_label} over (prev_hash || content_hash) — pubkey {signer.public_key_hex[:16]}...")
    _detail("step ordering", "UUIDv7 (time-sortable, embedded in signed material)")
    for index, record in enumerate(records):
        kind_label = record.kind.value
        excerpt = ""
        for field in ("prompt", "response", "tool_name", "tool_output", "final_output"):
            value = getattr(record.payload, field, None)
            if value:
                excerpt = _truncate(str(value), limit=64)
                break
        typer.secho(f"      [{index}] {kind_label:14s} ", fg=typer.colors.BRIGHT_BLACK, nl=False)
        typer.secho(excerpt, fg=typer.colors.WHITE)

    # ---- STEP 4 -----------------------------------------------------
    _step_header(4, "AIR verifies the freshly-built chain is intact")
    chain_result = verify_chain(records)
    if chain_result.status == VerificationStatus.OK:
        typer.secho("    ✓ chain verifies. Every signature matches its content_hash and prev_hash.", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho(f"    ✘ unexpected: {chain_result.status} — {chain_result.reason}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

    # ---- STEP 5 -----------------------------------------------------
    _step_header(5, "AIR runs OWASP-aligned detectors over the signed chain")
    findings = run_detectors(records, registry=None)
    if not findings:
        typer.secho("    (no findings — unexpected, demo chain is supposed to flag several)", fg=typer.colors.YELLOW)
    else:
        typer.secho(f"    {len(findings)} finding(s):", fg=typer.colors.WHITE, bold=True)
        for finding in findings:
            color = _severity_color(finding.severity)
            typer.secho(
                f"      {finding.detector_id:8s} {finding.severity.upper():8s} step {finding.step_index:>2}: {finding.title}",
                fg=color,
            )

    # ---- STEP 6 -----------------------------------------------------
    _step_header(6, "Structural Verification: did the agent honor its declared intent? (experimental)")
    sv_result = verify_intent(records)
    verdict_color = {
        IntentVerdict.VERIFIED: typer.colors.GREEN,
        IntentVerdict.FAILED: typer.colors.RED,
        IntentVerdict.INCONCLUSIVE: typer.colors.YELLOW,
    }[sv_result.verdict]
    _detail("intent", sv_result.intent)
    verdict_label = {
        IntentVerdict.VERIFIED: "PASSED (agent honored its declared intent)",
        IntentVerdict.FAILED: "FAILED BY AIR (agent violated its declared intent)",
        IntentVerdict.INCONCLUSIVE: "INCONCLUSIVE",
    }[sv_result.verdict]
    _detail("verdict", verdict_label)
    if sv_result.violations:
        typer.secho(f"    {len(sv_result.violations)} structural violation(s):", fg=verdict_color, bold=True)
        for violation in sv_result.violations:
            v_color = _severity_color(violation.severity)
            typer.secho(
                f"      {violation.check_id:14s} {violation.severity.upper():8s} step {violation.step_index:>2}: {violation.title}",
                fg=v_color,
            )
            if violation.causal_path:
                path_str = " -> ".join(f"#{o}" for o in violation.causal_path)
                typer.secho(f"        causal path: {path_str}", fg=typer.colors.CYAN)
    else:
        typer.secho(f"    {sv_result.summary}", fg=verdict_color)

    # ---- STEP 7 -----------------------------------------------------
    _step_header(7, "AIR exports the evidence in JSON, PDF, and CEF")
    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log_path.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=_count_conversations(records),
        verification=chain_result,
        findings=findings,
    )
    export_json(report, json_export)
    export_pdf(report, pdf_export)
    export_siem(report, cef_export)
    _detail("JSON", str(json_export.resolve()))
    _detail("PDF ", str(pdf_export.resolve()))
    _detail("CEF ", f"{cef_export.resolve()}  (Splunk / ArcSight / QRadar / Sentinel / Sumo / Datadog compatible)")

    # ---- STEP 8 -----------------------------------------------------
    _step_header(8, "Tamper with one byte of the leaked-SSH-key record")
    typer.secho("    An attacker (or insider) edits the JSONL log in place to alter the leaked", fg=typer.colors.WHITE)
    typer.secho("    SSH key payload, hoping to cover their tracks. They change exactly one byte.", fg=typer.colors.WHITE)
    tampered_index = tamper_one_byte(log_path, CONCRETE_DEMO_TAMPER_INDEX)
    _detail("tampered record", f"index {tampered_index} (TOOL_END containing the leaked SSH key)")

    # ---- STEP 9 -----------------------------------------------------
    _step_header(9, "Re-verify: AIR fails at the exact record that was modified")
    tampered_records = load_chain(log_path)
    tampered_result = verify_chain(tampered_records)
    if tampered_result.status == VerificationStatus.OK:
        typer.secho("    ✘ unexpected: the chain still verifies after tampering. Demo is broken.", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)
    typer.secho(f"    ✘ chain verification FAILED: {tampered_result.status.value}", fg=typer.colors.RED, bold=True)
    if tampered_result.failed_step_id is not None:
        failed_index = next(
            (i for i, r in enumerate(tampered_records) if r.step_id == tampered_result.failed_step_id),
            None,
        )
        location = f"index {failed_index}" if failed_index is not None else f"step_id {tampered_result.failed_step_id}"
        typer.secho(
            f"    ✘ failed at {location} (TOOL_END with the leaked SSH key)",
            fg=typer.colors.RED, bold=True,
        )
    if tampered_result.reason:
        typer.secho(f"    reason: {tampered_result.reason}", fg=typer.colors.YELLOW)
    typer.echo()
    typer.secho("  Result: tamper-evident at the byte level. The cover-up is provable.", fg=typer.colors.GREEN, bold=True)
    typer.secho(f"  Artifacts written to: {workdir.resolve()}", fg=typer.colors.BRIGHT_BLACK)
    _print_next_step()


def _run_healthcare_demo(
    workdir: Path,
    log_path: Path,
    json_export: Path,
    pdf_export: Path,
    cef_export: Path,
    signing_algorithm: str,
) -> None:
    """HIPAA-aligned clinical decision support demo."""
    typer.secho("\n  Project AIR — Healthcare Demo (HIPAA-Aligned)", fg=typer.colors.WHITE, bold=True)
    typer.secho("  A clinical AI agent reviews patient labs, imaging, and medications.", fg=typer.colors.BRIGHT_BLACK)
    typer.secho("  AIR captures every PHI access as a signed capsule with HIPAA audit controls.", fg=typer.colors.BRIGHT_BLACK)

    _step_header(1, "Clinical AI receives a patient review request", total=7)
    _detail("request", HEALTHCARE_DEMO_USER_INTENT)
    _detail("agent", "clinical decision support AI with EHR read/write access")
    _detail("HIPAA scope", "45 CFR 164.312(b) audit controls, 164.312(c) integrity, 164.312(d) auth")

    _step_header(2, "AIR captures every EHR access as a Signed Intent Capsule", total=7)
    try:
        algo = SigningAlgorithm(signing_algorithm)
    except ValueError:
        typer.secho(f"Unknown signing algorithm '{signing_algorithm}'.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None
    demo_signer = Signer.generate(algo)
    build_healthcare_demo_log(log_path, signer=demo_signer)
    records = load_chain(log_path)
    _detail("PHI accesses captured", str(len(records)))
    algo_label = "ML-DSA-65 (FIPS 204)" if algo == SigningAlgorithm.ML_DSA_65 else "Ed25519"
    _detail("signature", f"{algo_label} over (prev_hash || content_hash)")
    _detail("chain integrity", "BLAKE3 content hash, tamper-evident linked list")
    typer.echo()
    for index, record in enumerate(records):
        kind_label = record.kind.value
        excerpt = ""
        for field in ("prompt", "response", "tool_name", "tool_output", "final_output"):
            value = getattr(record.payload, field, None)
            if value:
                excerpt = _truncate(str(value), limit=64)
                break
        typer.secho(f"      [{index:>2}] {kind_label:14s} ", fg=typer.colors.BRIGHT_BLACK, nl=False)
        typer.secho(excerpt, fg=typer.colors.WHITE)

    _step_header(3, "Chain verification: every signature valid", total=7)
    chain_result = verify_chain(records)
    if chain_result.status == VerificationStatus.OK:
        typer.secho("    ✓ HIPAA 164.312(c) satisfied: chain integrity verified.", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho(f"    ✘ chain failed: {chain_result.reason}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

    _step_header(4, "OWASP + HIPAA detector analysis", total=7)
    findings = run_detectors(records, registry=None)
    if findings:
        typer.secho(f"    {len(findings)} finding(s):", fg=typer.colors.WHITE, bold=True)
        for finding in findings:
            color = _severity_color(finding.severity)
            typer.secho(
                f"      {finding.detector_id:8s} {finding.severity.upper():8s} step {finding.step_index:>2}: {finding.title}",
                fg=color,
            )
    else:
        typer.secho("    No findings (clean clinical workflow).", fg=typer.colors.GREEN)

    _step_header(5, "Export HIPAA-grade evidence (JSON, PDF, CEF)", total=7)
    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log_path.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=_count_conversations(records),
        verification=chain_result,
        findings=findings,
    )
    export_json(report, json_export)
    export_pdf(report, pdf_export)
    export_siem(report, cef_export)
    _detail("JSON", str(json_export.resolve()))
    _detail("PDF ", str(pdf_export.resolve()))
    _detail("CEF ", f"{cef_export.resolve()}  (SIEM-compatible)")

    _step_header(6, "Tamper test: modify one byte of a patient lab result", total=7)
    typer.secho("    Simulating an insider altering the HbA1c value in the audit trail.", fg=typer.colors.WHITE)
    tampered_index = tamper_one_byte(log_path, HEALTHCARE_DEMO_TAMPER_INDEX)
    _detail("tampered record", f"index {tampered_index} (TOOL_END containing patient lab results)")

    _step_header(7, "Re-verify: AIR detects the tampered PHI record", total=7)
    tampered_records = load_chain(log_path)
    tampered_result = verify_chain(tampered_records)
    if tampered_result.status == VerificationStatus.OK:
        typer.secho("    ✘ unexpected: chain still verifies after tampering.", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)
    typer.secho(f"    ✘ INTEGRITY BREACH: {tampered_result.status.value}", fg=typer.colors.RED, bold=True)
    if tampered_result.failed_step_id is not None:
        failed_index = next(
            (i for i, r in enumerate(tampered_records) if r.step_id == tampered_result.failed_step_id),
            None,
        )
        location = f"index {failed_index}" if failed_index is not None else f"step_id {tampered_result.failed_step_id}"
        typer.secho(f"    ✘ failed at {location} (patient lab results)", fg=typer.colors.RED, bold=True)
    if tampered_result.reason:
        typer.secho(f"    reason: {tampered_result.reason}", fg=typer.colors.YELLOW)
    typer.echo()
    typer.secho("  HIPAA AUDIT PROOF:", fg=typer.colors.GREEN, bold=True)
    typer.secho("    Every PHI access is signed, timestamped, and tamper-evident.", fg=typer.colors.GREEN)
    typer.secho("    Alteration of any record is detectable at the byte level.", fg=typer.colors.GREEN)
    typer.secho("    45 CFR 164.312(b) audit controls: SATISFIED.", fg=typer.colors.GREEN)
    typer.secho("    45 CFR 164.312(c) integrity controls: SATISFIED.", fg=typer.colors.GREEN)
    typer.secho(f"  Artifacts written to: {workdir.resolve()}", fg=typer.colors.BRIGHT_BLACK)
    typer.echo()


@report_app.command("alcoa")
def report_alcoa(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    output: Path = typer.Option(
        Path("alcoa-report.md"),
        "--output", "-o",
        help="Where to write the generated ALCOA+ evidence report (Markdown).",
    ),
    system_name: str = typer.Option(
        "[AI system name]", "--system-name", help="Human-readable name of the AI system.",
    ),
    operator: str = typer.Option(
        "[Provider / Operator entity]", "--operator", help="Legal entity operating the system.",
    ),
) -> None:
    """Generate an ALCOA+ data-integrity evidence report from an AgDR log (beta).

    Maps each ALCOA+ principle to the cryptographic evidence the signed chain
    carries. This evidences a faithful, tamper-evident record; it is NOT an
    assertion of a validated (CSV/GAMP 5) system. A qualified person must
    review it before it is used in any regulated context.
    """
    _require_license_or_exit("air report alcoa")
    typer.secho(f"[ALCOA+] Loading {log}...", fg=typer.colors.WHITE, bold=True)
    records = load_chain(log)
    verification = verify_chain(records)

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=_count_conversations(records),
        verification=verification,
        findings=[],
    )
    markdown = generate_alcoa_report(
        report, records, system_name=system_name, operator_entity=operator,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[WARNING] Chain verification did NOT pass: {verification.reason}. "
            "Integrity-dependent principles are downgraded in the report.",
            fg=typer.colors.YELLOW, err=True,
        )
    else:
        typer.secho(
            f"[Chain verified] {verification.records_verified} signatures valid.",
            fg=typer.colors.GREEN,
        )
    typer.secho(f"[ALCOA+] Wrote report to {output.resolve()} ({len(records)} records).", fg=typer.colors.CYAN)
    typer.secho(
        "[Reminder] Evidence for a qualified reviewer, not a certificate of compliance. "
        "'Faithful capture' is necessary, not sufficient, for GxP.",
        fg=typer.colors.BRIGHT_BLACK,
    )


@report_app.command("security-review")
def report_security_review(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    output: Path = typer.Option(
        Path("security-review-pack.md"),
        "--output", "-o",
        help="Where to write the evidence pack (Markdown).",
    ),
    vendor: str = typer.Option("[Vendor]", "--vendor", help="Your company name, as it appears on the pack."),
    system_name: str = typer.Option(
        "[AI agent / system name]", "--system-name", help="Human-readable name of the agent or system.",
    ),
    agent_registry: Path | None = typer.Option(
        None, "--agent-registry", exists=True, readable=True,
        help="Optional agent registry to enable the ASI03 / ASI10 Zero-Trust detectors.",
    ),
) -> None:
    """Answer an enterprise security review from the agent's own signed chain (beta).

    Ten questions a security reviewer or procurement questionnaire asks about
    an AI agent (logging, tamper evidence, external anchoring, scope, human
    oversight, detection, data handling, attribution, review, key custody),
    each with a status computed from the chain, the evidence, and a draft
    answer. The status table prints free; the full pack requires a license.
    """
    registry = _load_registry_or_exit(agent_registry)
    typer.secho(f"[Security review] Loading {log}...", fg=typer.colors.WHITE, bold=True)
    records = load_chain(log)
    verification = verify_chain(records)
    findings = run_detectors(records, registry=registry)
    results = assess_security_review(records, findings, verification.status)

    typer.echo()
    for result in results:
        color = typer.colors.GREEN if result.status == STATUS_EVIDENCED else typer.colors.YELLOW
        typer.secho(f"  {result.status:14s} ", fg=color, bold=True, nl=False)
        typer.secho(f"{result.question.number:>2}. {result.question.text}", fg=typer.colors.WHITE)
    evidenced = sum(1 for r in results if r.status == STATUS_EVIDENCED)
    typer.echo()
    typer.secho(
        f"  {evidenced} of {len(results)} evidenced by this chain; "
        f"{len(findings)} finding(s); chain verification {verification.status.value}.",
        fg=typer.colors.WHITE, bold=True,
    )
    typer.echo()
    _require_license_or_exit("air report security-review (full pack with evidence and draft answers)")

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=_count_conversations(records),
        verification=verification,
        findings=findings,
    )
    markdown = generate_security_review_report(report, records, vendor=vendor, system_name=system_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[WARNING] Chain verification did NOT pass: {verification.reason}. "
            "Review before handing this pack to anyone.",
            fg=typer.colors.YELLOW, err=True,
        )
    typer.secho(f"[Security review] Wrote evidence pack to {output.resolve()} ({len(records)} records).", fg=typer.colors.CYAN)
    typer.secho(
        "[Reminder] Draft answers must be reviewed and adapted before submission. "
        "The pack evidences the recorded chain, not systems outside it.",
        fg=typer.colors.WHITE,
    )


@report_app.command("article72")
def report_article72(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    system_id: str = typer.Option(
        ...,
        "--system-id",
        help="Unique identifier for the high-risk AI system under Article 11 Annex IV.",
    ),
    output: Path = typer.Option(
        Path("article72-report.md"),
        "--output", "-o",
        help="Where to write the generated Article 72 report (Markdown).",
    ),
    system_name: str = typer.Option(
        "[high-risk AI system name]",
        "--system-name",
        help="Human-readable name of the high-risk AI system.",
    ),
    operator: str = typer.Option(
        "[Provider / Operator entity]",
        "--operator",
        help="Legal entity operating the system (will appear in the attestation).",
    ),
    period: str = typer.Option(
        "[reporting period, e.g. 2026-Q3]",
        "--period",
        help="Reporting period label (free text).",
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help="Optional agent registry to enable ASI03/ASI10 Zero-Trust enforcement during report generation.",
        exists=True,
        readable=True,
    ),
    from_date: str | None = typer.Option(
        None, "--from", "--from-date",
        help="Include records on or after this date (YYYY-MM-DD). Full chain is still verified.",
    ),
    to_date: str | None = typer.Option(
        None, "--to", "--to-date",
        help="Include records on or before this date (YYYY-MM-DD). Full chain is still verified.",
    ),
) -> None:
    """Generate an EU AI Act Article 72 post-market monitoring report from an AgDR log.

    The output is a populated Markdown template, not a filed compliance
    artefact. The provider must review, adapt, and have a qualified person
    sign the attestation before the report is legally usable.
    """
    _require_license_or_exit("air report article72")
    registry = _load_registry_or_exit(agent_registry)
    parsed_from = _parse_date_option(from_date, "--from")
    parsed_to = _parse_date_option(to_date, "--to")

    typer.secho(f"[Article 72] Loading {log}...", fg=typer.colors.WHITE, bold=True)
    all_records = load_chain(log)
    verification = verify_chain(all_records)

    filtered = filter_records_by_date_range(all_records, from_date=parsed_from, to_date=parsed_to)
    if parsed_from is not None or parsed_to is not None:
        typer.secho(
            f"[Article 72] Date filter {parsed_from or 'start'} to {parsed_to or 'end'}: "
            f"{len(filtered)} of {len(all_records)} records in window.",
            fg=typer.colors.BRIGHT_BLACK,
        )

    findings = run_detectors(filtered, registry=registry)

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(filtered),
        conversations=_count_conversations(filtered),
        verification=verification,
        findings=findings,
    )
    markdown = generate_article72_report(
        report,
        filtered,
        system_id,
        system_name=system_name,
        operator_entity=operator,
        monitoring_period=period,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[WARNING] Chain verification did NOT pass: {verification.reason}. "
            "Review before relying on this report as evidence.",
            fg=typer.colors.YELLOW, err=True,
        )
    else:
        typer.secho(
            f"[Chain verified] {verification.records_verified} signatures valid.",
            fg=typer.colors.GREEN,
        )

    typer.secho(
        f"[Article 72] Wrote report to {output.resolve()} "
        f"({len(findings)} findings across {report.records} records).",
        fg=typer.colors.CYAN,
    )
    typer.secho(
        "[Reminder] This is an informational template. Have a qualified person "
        "sign the attestation and consult counsel before filing.",
        fg=typer.colors.BRIGHT_BLACK,
    )


@app.command()
def version() -> None:
    """Print the AIR version."""
    typer.echo(f"air / airsdk {airsdk_version}")


# -- Pro commands --------------------------------------------------------
# These commands operate on a license file managed by the optional
# ``projectair-pro`` package. When ``projectair-pro`` is not installed they
# print a clear install/upgrade message instead of failing obscurely.


def _pro_unavailable_message() -> str:
    return (
        "Pro features require the projectair-pro package and a paid grant.\n\n"
        "  pip install projectair-pro\n"
        "  air grant                                (pull your workspace grant from the console)\n"
        "  air install-license --license <token>    (or a token you were handed)\n\n"
        "Buy at https://vindicara.io/pricing"
    )


def _require_license_or_exit(feature: str) -> None:
    """Gate ``feature`` behind a valid license. Exits(2) with an upgrade prompt
    when no valid license is installed.

    Seeing is free: `air demo`, `air trace`, `air watch`, `air explain`,
    `air incident`, and `air health` print in the terminal without a license.
    Artifacts and routing (the ALCOA+ / Article 72 / NIST / SOC 2 / security
    review / incident packs, exports, Slack / PagerDuty delivery) require a
    license, which routes through the existing Stripe checkout.
    """
    try:
        from airsdk_pro.license import is_pro_active
        licensed = is_pro_active()
    except ImportError:
        licensed = False
    if licensed:
        return
    typer.secho(
        f"{feature} requires a Project AIR license.\n\n"
        "  Free:  air demo, air trace, air watch, air explain, air incident, air health (printed).\n"
        f"  Paid:  {feature} and all ongoing / report / export features.\n\n"
        "  Start or buy:      https://vindicara.io/pricing\n"
        "  Already paid:      air grant   (pulls your workspace entitlements from the console)",
        fg=typer.colors.YELLOW,
        err=True,
    )
    raise typer.Exit(2)


@app.command(name="install-license")
def install_license(
    license_token: str = typer.Option(
        None,
        "--license",
        "-l",
        help="Paste the license token (the JSON blob you received after purchase).",
    ),
    license_file: Path = typer.Option(
        None,
        "--license-file",
        "-f",
        help="Read the license token from a file instead of pasting it inline.",
    ),
) -> None:
    """Install a Vindicara Pro license from a token string or file."""
    try:
        from airsdk_pro.license import install_license
    except ImportError:
        typer.secho(_pro_unavailable_message(), fg=typer.colors.YELLOW)
        raise typer.Exit(code=2) from None

    if license_token is None and license_file is None:
        typer.secho("error: pass --license <token> or --license-file <path>", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    token_text = license_file.read_text(encoding="utf-8") if license_file is not None else (license_token or "")
    if not token_text.strip():
        typer.secho("error: empty license token", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    try:
        parsed = install_license(token_text)
    except Exception as exc:
        typer.secho(f"license install failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Pro license installed.", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"  email:           {parsed.email}")
    typer.echo(f"  tier:            {parsed.tier}")
    typer.echo(f"  features:        {', '.join(parsed.features) if parsed.features else '(none)'}")
    typer.echo(f"  days remaining:  {parsed.days_remaining}")


# -- Auth commands ----------------------------------------------------------

# "Air CLI", the Native application in the Vindicara Auth0 tenant (device-code grant).
# The site uses its own Single Page Application client; an SPA cannot use the device grant.
_AUTH0_CLI_CLIENT_ID = "ehK22gj7je6DtNcjEjKlftAQsSGPuSOV"
_AUTH0_DOMAIN = "dev-kilt2vkudvbu75ny.us.auth0.com"
_AUTH0_AUDIENCE = "https://api.vindicara.io"


@app.command()
def login() -> None:
    """Authenticate with Vindicara via Auth0."""
    import time as _time

    import jwt as _jwt

    from airsdk.containment.auth0_flows import Auth0Tenant, poll_device_token, start_device_flow
    from projectair.config import save_session

    tenant = Auth0Tenant(
        domain=_AUTH0_DOMAIN,
        audience=_AUTH0_AUDIENCE,
        client_id=_AUTH0_CLI_CLIENT_ID,
    )

    try:
        device = start_device_flow(tenant)
    except Exception as exc:
        typer.secho(f"Login failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"  Open: {device.verification_uri}")
    typer.echo(f"  Code: {device.user_code}")
    typer.echo("Waiting for browser authentication...")

    try:
        token = poll_device_token(tenant, device.device_code, interval=device.interval)
    except Exception as exc:
        typer.secho(f"Login failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    claims = _jwt.decode(token, options={"verify_signature": False})
    email: str = claims.get("email") or claims.get("sub", "unknown")
    sub: str = claims.get("sub", "")
    exp: int = int(claims.get("exp", int(_time.time()) + 3600))

    save_session(
        {
            "email": email,
            "sub": sub,
            "expires_at": exp,
            "access_token": token,
        }
    )

    typer.secho(f"Logged in as {email}", fg=typer.colors.GREEN, bold=True)
    _claim_workspace(token)


def _claim_workspace(access_token: str) -> None:
    """Trade the identity token for this person's workspace and, on first sign-in, its key."""
    from projectair.cloud_login import CloudLoginError, exchange_device_token, store_cloud_login
    from projectair.cloud_target import resolve_cloud_target
    from projectair.config import _config_path

    target = resolve_cloud_target()
    try:
        login = exchange_device_token(target.url, access_token)
    except CloudLoginError as exc:
        typer.secho(
            f"No workspace was issued: {exc}\n"
            "  Sign-in worked, but AIR Cloud did not accept the token. Check that the Auth0 API "
            "https://api.vindicara.io exists and this client is authorized for it, then run `air login` again.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=1) from exc
    store_cloud_login(login)
    verb = "Created" if login.created else "Workspace"
    typer.secho(f"{verb}: {login.workspace_name} ({login.workspace_id}), {login.tier} tier, role {login.role}", fg=typer.colors.GREEN)
    if login.api_key is not None:
        typer.echo(f"  API key (shown once, saved to {_config_path()}): {login.api_key}")
        typer.echo("  In your agent's shell:  export AIRSDK_CLOUD_API_KEY=" + login.api_key)
    else:
        typer.echo("  API key: the one saved earlier; issue another in Flightdeck under Keys if you need it.")
    typer.echo(f"  Console: {login.console_url or target.console_url}/keys")


@app.command()
def logout() -> None:
    """Remove saved Vindicara session."""
    from projectair.config import delete_session

    removed = delete_session()
    if removed:
        typer.secho("Logged out.", fg=typer.colors.GREEN)
    else:
        typer.echo("Not logged in.")


@app.command()
def whoami() -> None:
    """Show current login status."""
    import time as _time

    from projectair.config import load_session

    session = load_session()
    if session is None:
        typer.echo("Not logged in. Run `air login`.")
        return

    expires_at = session.get("expires_at")
    if expires_at is None or int(expires_at) <= int(_time.time()):
        typer.echo("Session expired. Run `air login` to re-authenticate.")
        return

    email = session.get("email", "unknown")
    typer.secho(f"Logged in as {email}", fg=typer.colors.GREEN)
    from projectair.config import get_config

    workspace_id = get_config("cloud", "workspace_id")
    if workspace_id:
        typer.echo(f"  workspace: {get_config('cloud', 'workspace_name') or workspace_id} ({workspace_id})")
        typer.echo(f"  key saved: {'yes' if get_config('cloud', 'api_key') else 'no'}")


@app.command()
def status() -> None:
    """Show whether a Pro license is installed and what it grants."""
    try:
        from airsdk_pro.license import current_license
    except ImportError:
        typer.secho("Pro not installed (free OSS only).", fg=typer.colors.BRIGHT_BLACK)
        typer.echo("")
        typer.echo(_pro_unavailable_message())
        return

    license_obj = current_license()
    if license_obj is None:
        typer.secho("No grant installed.", fg=typer.colors.YELLOW)
        typer.echo("")
        typer.echo("Everything local is free and keeps working. Paid features need a grant:")
        typer.echo("  air grant                                  (from your console workspace)")
        typer.echo("  air install-license --license <token>      (a token you were handed)")
        return

    if not license_obj.is_paid:
        typer.secho("Free-tier grant installed.", fg=typer.colors.YELLOW, bold=True)
        typer.echo(f"  email:           {license_obj.email}")
        typer.echo("  Everything local is free; paid features need Pro or above: https://vindicara.io/pricing")
        return

    typer.secho(f"{license_obj.tier.capitalize()} grant active.", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"  email:           {license_obj.email}")
    typer.echo(f"  tier:            {license_obj.tier}")
    typer.echo(f"  features:        {', '.join(license_obj.features) if license_obj.features else '(none)'}")
    typer.echo(f"  days remaining:  {license_obj.days_remaining}")


@app.command()
def upgrade() -> None:
    """Print the upgrade URL and what each tier unlocks."""
    typer.secho("Project AIR tiers", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo("")
    typer.echo("  Free          $0          everything local: demo, trace, watch, explain, incident, health, 16 detectors")
    typer.echo("  Pro           $25/mo      hosted FlightDeck, anchoring, evidence packs, reports")
    typer.echo("  Team          $599/mo     1-year retention for your whole team (SOC 2 window)")
    typer.echo("  Enterprise    Talk to us  6-year retention, self-hosted, SSO/RBAC, BAA")
    typer.echo("")
    typer.echo("Everything on your machine is free and open source; the hosted product and the packs are paid.")
    typer.echo("https://vindicara.io/pricing")


@report_app.command("nist-rmf")
def report_nist_rmf(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    system_id: str = typer.Option(
        ...,
        "--system-id",
        help="Unique identifier for the AI system whose risks are being managed.",
    ),
    output: Path = typer.Option(
        Path("nist-rmf-report.md"),
        "--output", "-o",
        help="Where to write the generated NIST AI RMF report (Markdown).",
    ),
    system_name: str = typer.Option(
        "[AI system name]",
        "--system-name",
        help="Human-readable name of the AI system.",
    ),
    operator: str = typer.Option(
        "[Operator entity]",
        "--operator",
        help="Legal entity operating the system (will appear in the attestation).",
    ),
    period: str = typer.Option(
        "[reporting period, e.g. 2026-Q3]",
        "--period",
        help="Reporting period label (free text).",
    ),
    rmf_profile: str = typer.Option(
        "AI RMF 1.0 (NIST AI 100-1)",
        "--rmf-profile",
        help="RMF profile applied (e.g. AI RMF 1.0, GAI Profile NIST AI 600-1).",
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help="Optional agent registry to enable ASI03/ASI10 Zero-Trust enforcement during report generation.",
        exists=True,
        readable=True,
    ),
    from_date: str | None = typer.Option(
        None, "--from", "--from-date",
        help="Include records on or after this date (YYYY-MM-DD). Full chain is still verified.",
    ),
    to_date: str | None = typer.Option(
        None, "--to", "--to-date",
        help="Include records on or before this date (YYYY-MM-DD). Full chain is still verified.",
    ),
) -> None:
    """Generate a NIST AI RMF risk-management report from an AgDR log (Pro).

    Requires a Vindicara Pro license with the ``report-nist-ai-rmf``
    feature flag. The output is a populated Markdown template structured
    against the four AI RMF functions (GOVERN, MAP, MEASURE, MANAGE),
    not a NIST-blessed compliance artefact. Operators must review,
    adapt, and have a qualified person sign the attestation before
    relying on the report as evidence.
    """
    try:
        from airsdk_pro.license import LicenseError
        from airsdk_pro.report_nist_rmf import generate_nist_rmf_report
    except ImportError:
        typer.secho(_pro_unavailable_message(), fg=typer.colors.YELLOW)
        raise typer.Exit(code=2) from None

    registry = _load_registry_or_exit(agent_registry)
    parsed_from = _parse_date_option(from_date, "--from")
    parsed_to = _parse_date_option(to_date, "--to")

    typer.secho(f"[NIST AI RMF] Loading {log}...", fg=typer.colors.WHITE, bold=True)
    all_records = load_chain(log)
    verification = verify_chain(all_records)

    filtered = filter_records_by_date_range(all_records, from_date=parsed_from, to_date=parsed_to)
    if parsed_from is not None or parsed_to is not None:
        typer.secho(
            f"[NIST AI RMF] Date filter {parsed_from or 'start'} to {parsed_to or 'end'}: "
            f"{len(filtered)} of {len(all_records)} records in window.",
            fg=typer.colors.BRIGHT_BLACK,
        )

    findings = run_detectors(filtered, registry=registry)

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(filtered),
        conversations=_count_conversations(filtered),
        verification=verification,
        findings=findings,
    )

    try:
        markdown = generate_nist_rmf_report(
            report,
            filtered,
            system_id,
            system_name=system_name,
            operator_entity=operator,
            monitoring_period=period,
            rmf_profile=rmf_profile,
        )
    except LicenseError as exc:
        typer.secho(f"License check failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[WARNING] Chain verification did NOT pass: {verification.reason}. "
            "Review before relying on this report as evidence.",
            fg=typer.colors.YELLOW, err=True,
        )
    else:
        typer.secho(
            f"[Chain verified] {verification.records_verified} signatures valid.",
            fg=typer.colors.GREEN,
        )

    typer.secho(f"NIST AI RMF report written to {output.resolve()}", fg=typer.colors.GREEN, bold=True)


@report_app.command("soc2-ai")
def report_soc2_ai(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    system_id: str = typer.Option(
        ...,
        "--system-id",
        help="Unique identifier for the AI system being audited.",
    ),
    output: Path = typer.Option(
        Path("soc2-ai-report.md"),
        "--output", "-o",
        help="Where to write the generated SOC 2 AI evidence template (Markdown).",
    ),
    service_organisation: str = typer.Option(
        "[Service organisation]",
        "--service-organisation", "--service-org",
        help="Legal entity that operates the service being audited.",
    ),
    system_name: str = typer.Option(
        "[AI system name]",
        "--system-name",
        help="Human-readable name of the AI system.",
    ),
    period: str = typer.Option(
        "[reporting period, e.g. 2026-Q3]",
        "--period",
        help="Reporting period label (free text).",
    ),
    in_scope: str = typer.Option(
        "Security,Processing Integrity",
        "--in-scope",
        help="Comma-separated TSC categories elected for the engagement.",
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help="Optional agent registry to enable ASI03/ASI10 Zero-Trust enforcement during report generation.",
        exists=True,
        readable=True,
    ),
    from_date: str | None = typer.Option(
        None, "--from", "--from-date",
        help="Include records on or after this date (YYYY-MM-DD). Full chain is still verified.",
    ),
    to_date: str | None = typer.Option(
        None, "--to", "--to-date",
        help="Include records on or before this date (YYYY-MM-DD). Full chain is still verified.",
    ),
) -> None:
    """Generate a SOC 2 AI evidence template from an AgDR log (Pro).

    Requires a Vindicara Pro license with the ``report-soc2-ai`` feature
    flag. The output is a populated Markdown evidence template
    structured against the AICPA Trust Services Criteria, NOT a SOC 2
    report (only an independent CPA can issue one). The service
    organisation must review, supplement with management-assertion
    language, and supply the evidence to a qualified CPA before the
    template is usable in a SOC 2 examination.
    """
    try:
        from airsdk_pro.license import LicenseError
        from airsdk_pro.report_soc2_ai import generate_soc2_ai_report
    except ImportError:
        typer.secho(_pro_unavailable_message(), fg=typer.colors.YELLOW)
        raise typer.Exit(code=2) from None

    registry = _load_registry_or_exit(agent_registry)
    parsed_from = _parse_date_option(from_date, "--from")
    parsed_to = _parse_date_option(to_date, "--to")
    in_scope_categories = tuple(s.strip() for s in in_scope.split(",") if s.strip())

    typer.secho(f"[SOC 2 AI] Loading {log}...", fg=typer.colors.WHITE, bold=True)
    all_records = load_chain(log)
    verification = verify_chain(all_records)

    filtered = filter_records_by_date_range(all_records, from_date=parsed_from, to_date=parsed_to)
    if parsed_from is not None or parsed_to is not None:
        typer.secho(
            f"[SOC 2 AI] Date filter {parsed_from or 'start'} to {parsed_to or 'end'}: "
            f"{len(filtered)} of {len(all_records)} records in window.",
            fg=typer.colors.BRIGHT_BLACK,
        )

    findings = run_detectors(filtered, registry=registry)

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(filtered),
        conversations=_count_conversations(filtered),
        verification=verification,
        findings=findings,
    )

    try:
        markdown = generate_soc2_ai_report(
            report,
            filtered,
            system_id,
            service_organisation=service_organisation,
            system_name=system_name,
            monitoring_period=period,
            in_scope_categories=in_scope_categories,
        )
    except LicenseError as exc:
        typer.secho(f"License check failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[WARNING] Chain verification did NOT pass: {verification.reason}. "
            "Review before relying on this evidence in a SOC 2 examination.",
            fg=typer.colors.YELLOW, err=True,
        )
    else:
        typer.secho(
            f"[Chain verified] {verification.records_verified} signatures valid.",
            fg=typer.colors.GREEN,
        )

    typer.secho(f"SOC 2 AI evidence template written to {output.resolve()}", fg=typer.colors.GREEN, bold=True)


def main() -> None:
    app()


def results_main() -> None:
    """Entry point for the bare ``projectair`` command.

    Typing ``projectair`` with no arguments runs the demo scan and shows the
    results (after the first-run email gate), so a fresh ``pip install`` user can
    go from install to results in one word. With arguments it behaves like
    ``air`` (``projectair trace <chain>``, etc.).
    """
    import sys

    if len(sys.argv) == 1:
        sys.argv.append("demo")
    app()


if __name__ == "__main__":
    main()
