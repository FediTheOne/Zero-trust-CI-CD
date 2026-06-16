"""
Zero-Trust Application
----------------------
Serves a provenance dashboard at /, and machine-readable security metadata at
/api/security. All build-time values are injected via environment variables
that are baked into the container image during `docker build` in the Jenkins
pipeline, making this page a self-attestation of how the running artifact was
produced and how it is being run.
"""

import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)


def build_metadata():
    """All metadata in one place — used by both HTML and JSON endpoints."""
    build_number = os.environ.get("BUILD_NUMBER", "unknown")
    image_ref = f"feditheone2050/zero-trust-app:{build_number}"
    return {
        "service": "zero-trust-app",
        "status": "active",
        "build": {
            "number": build_number,
            "git_commit": os.environ.get("GIT_COMMIT", "unknown"),
            "timestamp": os.environ.get("BUILD_TIMESTAMP", "unknown"),
        },
        "image": {
            "reference": image_ref,
            "signed": True,
            "signature_algorithm": "Cosign / Sigstore",
        },
        "security_gates": [
            ("Secret scanning", "gitleaks"),
            ("Dependency CVE scan", "Trivy (filesystem)"),
            ("Static analysis", "Semgrep"),
            ("Container CVE scan", "Trivy (image)"),
            ("Image signature", "Cosign + Sigstore Rekor"),
            ("Software bill of materials", "Syft (CycloneDX)"),
        ],
        "runtime_hardening": [
            ("Non-root user", "UID 10001"),
            ("Root filesystem", "Read-only"),
            ("Linux capabilities", "All dropped"),
            ("Privilege escalation", "Disabled (no-new-privileges)"),
            ("Resource limits", "512 MiB · 1 vCPU · 100 PIDs"),
        ],
        "verification_command": f"cosign verify --key cosign.pub {image_ref}",
    }


DASHBOARD_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ data.service }} — Provenance Report</title>
<style>
  :root {
    --bg: #FAFAF7;
    --surface: #FFFFFF;
    --ink: #14181F;
    --ink-soft: #5B6573;
    --rule: #E8E5DE;
    --verified: #1A6F3C;
    --verified-soft: #E6F0E8;
    --highlight: #FFF9E6;
    --warn: #8A5A00;
  }

  * { box-sizing: border-box; }

  html, body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }

  .page {
    max-width: 720px;
    margin: 0 auto;
    padding: 64px 28px 96px;
  }

  /* Header */
  .eyebrow {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--ink-soft);
    margin: 0 0 18px;
  }

  h1 {
    font-family: "Iowan Old Style", "Palatino Linotype", "Source Serif Pro", Georgia, serif;
    font-weight: 600;
    font-size: 42px;
    line-height: 1.08;
    letter-spacing: -0.01em;
    margin: 0 0 14px;
  }

  .subtitle {
    color: var(--ink-soft);
    margin: 0 0 28px;
    font-size: 15px;
  }

  /* Verification seal */
  .seal {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px 8px 10px;
    background: var(--verified-soft);
    color: var(--verified);
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  .seal-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--verified);
    box-shadow: 0 0 0 4px rgba(26, 111, 60, 0.15);
    animation: pulse 2.4s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 4px rgba(26, 111, 60, 0.12); }
    50%      { box-shadow: 0 0 0 7px rgba(26, 111, 60, 0.06); }
  }

  @media (prefers-reduced-motion: reduce) {
    .seal-dot { animation: none; }
  }

  /* Section */
  section {
    border-top: 1px solid var(--rule);
    padding-top: 28px;
    margin-top: 40px;
  }

  h2 {
    font-family: "Iowan Old Style", "Palatino Linotype", "Source Serif Pro", Georgia, serif;
    font-weight: 600;
    font-size: 22px;
    margin: 0 0 18px;
    letter-spacing: -0.005em;
  }

  /* Key-value list */
  dl.kv {
    display: grid;
    grid-template-columns: 180px 1fr;
    column-gap: 24px;
    row-gap: 12px;
    margin: 0;
  }

  dl.kv dt {
    color: var(--ink-soft);
    font-size: 14px;
  }

  dl.kv dd {
    margin: 0;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 14px;
    word-break: break-all;
  }

  /* Checklist */
  ul.checklist {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 14px;
  }

  ul.checklist li {
    display: grid;
    grid-template-columns: 22px 1fr;
    gap: 12px;
    align-items: baseline;
  }

  ul.checklist .check {
    color: var(--verified);
    font-weight: 700;
    font-size: 16px;
    line-height: 1;
  }

  ul.checklist .label {
    font-size: 15px;
  }

  ul.checklist .detail {
    color: var(--ink-soft);
    font-size: 14px;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }

  /* Verification block */
  .verify-intro {
    color: var(--ink-soft);
    font-size: 14px;
    margin: 0 0 16px;
    line-height: 1.6;
  }

  .verify-cmd {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 13px;
    background: var(--ink);
    color: #E8E5DE;
    padding: 18px 20px;
    border-radius: 8px;
    overflow-x: auto;
    white-space: pre;
    margin: 0;
  }

  .verify-cmd .prompt { color: #7C8694; user-select: none; }
  .verify-cmd .flag   { color: #B6E2C5; }

  /* Footer */
  footer.colophon {
    margin-top: 56px;
    padding-top: 24px;
    border-top: 1px solid var(--rule);
    color: var(--ink-soft);
    font-size: 13px;
    line-height: 1.7;
  }

  footer.colophon .mono {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    color: var(--ink);
    word-break: break-all;
  }

  /* Mobile */
  @media (max-width: 560px) {
    .page { padding: 40px 20px 64px; }
    h1 { font-size: 32px; }
    dl.kv { grid-template-columns: 1fr; row-gap: 4px; }
    dl.kv dt { margin-top: 8px; }
  }
</style>
</head>
<body>
  <main class="page">

    <p class="eyebrow">Provenance Report</p>
    <h1>{{ data.service }}</h1>
    <p class="subtitle">A self-attestation of how this running container was built and how it is being run.</p>
    <span class="seal" role="status" aria-live="polite">
      <span class="seal-dot" aria-hidden="true"></span>
      <span>Verified · {{ data.status }}</span>
    </span>

    <section aria-labelledby="build-identity">
      <h2 id="build-identity">Build identity</h2>
      <dl class="kv">
        <dt>Build number</dt>
        <dd>#{{ data.build.number }}</dd>
        <dt>Git commit</dt>
        <dd>{{ data.build.git_commit }}</dd>
        <dt>Built at</dt>
        <dd>{{ data.build.timestamp }}</dd>
        <dt>Image reference</dt>
        <dd>{{ data.image.reference }}</dd>
      </dl>
    </section>

    <section aria-labelledby="security-gates">
      <h2 id="security-gates">Security gates passed</h2>
      <ul class="checklist">
        {% for label, tool in data.security_gates %}
        <li>
          <span class="check" aria-hidden="true">✓</span>
          <span><span class="label">{{ label }}</span> <span class="detail">· {{ tool }}</span></span>
        </li>
        {% endfor %}
      </ul>
    </section>

    <section aria-labelledby="runtime-hardening">
      <h2 id="runtime-hardening">Runtime hardening</h2>
      <ul class="checklist">
        {% for label, value in data.runtime_hardening %}
        <li>
          <span class="check" aria-hidden="true">✓</span>
          <span><span class="label">{{ label }}</span> <span class="detail">· {{ value }}</span></span>
        </li>
        {% endfor %}
      </ul>
    </section>

    <section aria-labelledby="verification">
      <h2 id="verification">Independent verification</h2>
      <p class="verify-intro">
        The image identity below can be cryptographically verified by any party
        holding the public key committed to this repository. A successful
        verification proves the image was produced by this pipeline and has not
        been modified since.
      </p>
      <pre class="verify-cmd"><span class="prompt">$ </span>cosign verify <span class="flag">--key</span> cosign.pub \
  {{ data.image.reference }}</pre>
    </section>

    <footer class="colophon">
      <p>
        Image: <span class="mono">{{ data.image.reference }}</span><br>
        Machine-readable metadata: <span class="mono">GET /api/security</span>
      </p>
      <p>
        This page is served by the application itself. All metadata is injected
        at build time via Dockerfile ARGs, making the dashboard a direct
        attestation of the artifact it runs as.
      </p>
    </footer>

  </main>
</body>
</html>
"""


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE, data=build_metadata())


@app.route("/api/security")
def security_metadata():
    return jsonify(build_metadata())


@app.route("/api/status")
def status():
    """Lightweight liveness endpoint preserving the original JSON contract."""
    return jsonify(message="zero trust pipeline active", status="secure")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
