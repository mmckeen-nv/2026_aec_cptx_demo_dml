"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type DiagnosticCheck = {
  id: string;
  label: string;
  state: "pass" | "fail" | "warn";
  detail: string;
  latencyMs?: number;
};
type Service = {
  id: "hermes" | "rhino" | "blender" | "comfy" | "memory";
  name: string;
  online: boolean;
  status: "healthy" | "degraded" | "offline";
  detail: string;
  resolvable: boolean;
  checkedAt: string;
  checks: DiagnosticCheck[];
};
type Phase = { id: number; name: string; detail: string; state: "done" | "active" | "waiting" };
type Status = {
  running: boolean;
  runLabel: string;
  elapsed: string;
  restart: { status: "idle" | "preflighting" | "ready" | "error"; error?: string | null };
  preflight: {
    status: "idle" | "running" | "passed" | "failed";
    startedAt?: string;
    completedAt?: string;
    failedRequired?: number;
    totalChecks?: number;
    checks?: DiagnosticCheck[];
    error?: string;
  };
  sceneState: {
    status: "unknown" | "verifying" | "empty" | "occupied" | "error";
    rhinoCount?: number;
    rhinoTableCount?: number;
    blenderCount?: number;
    blenderDefaultBaseline?: boolean;
    verifiedAt?: string;
    error?: string;
  };
  services: Service[];
  phases: Phase[];
  currentPhase: number;
  updatedAt: string;
};
type Activity = { time: string; kind: string; text: string };
type Metrics = {
  series: Array<{ at: string; tps: number; toolRate: number; retries: number }>;
  current: { tps: number; toolRate: number };
  totals: {
    tokensGenerated: number;
    modelCalls: number;
    toolCalls: number;
    retries: number;
    dmlCalls: number;
    memoryRecalls: number;
    memoriesAccessed: number;
    memoryStores: number;
  };
  memoryActivity: {
    recallActive: boolean;
    writeActive: boolean;
    lastRecallAt: string | null;
    lastStoreAt: string | null;
  };
  windowSeconds: number;
};

const emptyStatus: Status = {
  running: false,
  runLabel: "Ready",
  elapsed: "00:00",
  restart: { status: "idle" },
  preflight: { status: "idle" },
  sceneState: { status: "unknown" },
  services: [],
  phases: [],
  currentPhase: 0,
  updatedAt: new Date(0).toISOString(),
};

const feeds = [
  { key: "rhino", eyebrow: "MODELING", title: "Rhino 3D", tag: "Live viewport", phase: 2 },
  { key: "blender", eyebrow: "SCENE", title: "Blender", tag: "Live viewport", phase: 4 },
  { key: "depth", eyebrow: "CONTROL PASS", title: "Depth", tag: "Control pass", phase: 6 },
  { key: "comfy", eyebrow: "STYLIZATION", title: "FLUX.2", tag: "Source / final", phase: 7 },
];

const emptyMetrics: Metrics = {
  series: Array.from({ length: 20 }, () => ({ at: "", tps: 0, toolRate: 0, retries: 0 })),
  current: { tps: 0, toolRate: 0 },
  totals: { tokensGenerated: 0, modelCalls: 0, toolCalls: 0, retries: 0, dmlCalls: 0, memoryRecalls: 0, memoriesAccessed: 0, memoryStores: 0 },
  memoryActivity: { recallActive: false, writeActive: false, lastRecallAt: null, lastStoreAt: null },
  windowSeconds: 20,
};

function memoryEventTime(value: string | null) {
  if (!value) return "none this run";
  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function isMemoryHarnessCheck(check: DiagnosticCheck) {
  return /(^|[-_\s])(dml|cma|daystrom|ollama)([-_\s/]|$)/i.test(`${check.id} ${check.label}`);
}

function DiagnosticCheckCard({ check }: { check: DiagnosticCheck }) {
  return (
    <article className={`diagnostic-check check-${check.state}`}>
      <i />
      <div><strong>{check.label}</strong><span>{check.detail}</span></div>
    </article>
  );
}

function PreflightCheckList({ checks }: { checks: DiagnosticCheck[] }) {
  const memoryChecks = checks.filter(isMemoryHarnessCheck);
  const primaryChecks = checks.filter((check) => !isMemoryHarnessCheck(check));
  const memoryFailures = memoryChecks.filter((check) => check.state === "fail").length;
  const memoryWarnings = memoryChecks.filter((check) => check.state === "warn").length;
  const memoryPasses = memoryChecks.length - memoryFailures - memoryWarnings;
  const memoryState = memoryFailures ? "fail" : memoryWarnings ? "warn" : "pass";

  return (
    <div className="diagnostic-checks">
      {memoryChecks.length > 0 && (
        <details className={`diagnostic-group check-${memoryState}`} open={memoryFailures > 0}>
          <summary>
            <i />
            <div>
              <strong>Memory Harness</strong>
              <span>
                {memoryPasses} passed
                {memoryWarnings ? ` · ${memoryWarnings} warning${memoryWarnings === 1 ? "" : "s"}` : ""}
                {memoryFailures ? ` · ${memoryFailures} failed` : ""}
              </span>
            </div>
            <b>DETAILS</b>
          </summary>
          <div className="diagnostic-group-items">
            {memoryChecks.map((check) => <DiagnosticCheckCard check={check} key={check.id} />)}
          </div>
        </details>
      )}
      {primaryChecks.map((check) => <DiagnosticCheckCard check={check} key={check.id} />)}
    </div>
  );
}

function LiveFeed({
  feed,
  tick,
  enabled,
}: {
  feed: (typeof feeds)[number];
  tick: number;
  enabled: boolean;
}) {
  const [source, setSource] = useState(
    enabled ? `/api/live/${feed.key}` : "/standby-nvidia-aec.png",
  );
  const [locking, setLocking] = useState(false);
  const [displayMode, setDisplayMode] = useState("standby");
  const [fluxProgress, setFluxProgress] = useState({
    state: "idle",
    nodes: 0,
    steps: 0,
    ahead: 0,
  });
  const [signalVersion, setSignalVersion] = useState("standby");
  const signal = useRef("");
  const mode = useRef("standby");
  const objectUrl = useRef<string | null>(null);
  const lockTimer = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!enabled) {
      if (objectUrl.current) {
        URL.revokeObjectURL(objectUrl.current);
        objectUrl.current = null;
      }
      setSource("/standby-nvidia-aec.png");
      setDisplayMode("standby");
      setFluxProgress({ state: "idle", nodes: 0, steps: 0, ahead: 0 });
      setLocking(false);
      signal.current = "";
      mode.current = "standby";
      return () => { cancelled = true; };
    }
    fetch(`/api/live/${feed.key}?v=${tick}`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("feed unavailable");
        const nextMode = response.headers.get("X-AEC-Mode") ?? "standby";
        const nextSignal = response.headers.get("X-AEC-Signal") ?? "";
        if (feed.key === "comfy") {
          setFluxProgress({
            state: response.headers.get("X-AEC-Flux-State") ?? "idle",
            nodes: Number(response.headers.get("X-AEC-Flux-Nodes") ?? 0),
            steps: Number(response.headers.get("X-AEC-Flux-Steps") ?? 0),
            ahead: Number(response.headers.get("X-AEC-Flux-Ahead") ?? 0),
          });
        }
        const blob = await response.blob();
        if (cancelled) return;
        const nextUrl = URL.createObjectURL(blob);
        if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
        objectUrl.current = nextUrl;
        setSource(nextUrl);
        setDisplayMode(nextMode);
        if (nextMode !== "standby" && (nextSignal !== signal.current || mode.current === "standby")) {
          setSignalVersion(`${nextSignal}-${Date.now()}`);
          setLocking(false);
          window.setTimeout(() => setLocking(true), 20);
          if (lockTimer.current) window.clearTimeout(lockTimer.current);
          lockTimer.current = window.setTimeout(() => setLocking(false), 820);
        }
        signal.current = nextSignal;
        mode.current = nextMode;
      })
      .catch(() => undefined);
    return () => { cancelled = true; };
  }, [enabled, feed.key, tick]);

  useEffect(() => () => {
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    if (lockTimer.current) window.clearTimeout(lockTimer.current);
  }, []);

  return (
    <article className={`feed-card feed-${feed.key} ${locking ? "signal-lock" : ""}`}>
      <div className="feed-label">
        <div>
          <p>{feed.eyebrow}</p>
          <h3>{feed.title}</h3>
        </div>
        <span className={`feed-mode mode-${displayMode}`}><i /> {
          !enabled
            ? `Queued · Phase ${feed.phase}`
            : feed.key === "comfy"
            ? displayMode === "final"
              ? "FLUX.2 final"
              : displayMode === "source"
                ? "Source · awaiting FLUX.2"
                : "Standby"
            : displayMode === "standby"
              ? "Standby"
              : feed.tag
        }</span>
      </div>
      <img key={signalVersion} src={source} alt={`${feed.title} latest output`} />
      {feed.key === "comfy" && fluxProgress.state !== "idle" && (
        <div className={`flux-progress flux-${fluxProgress.state}`} role="status" aria-live="polite">
          <div className="flux-progress-copy">
            <span><i /> {fluxProgress.state === "processing" ? "FLUX.2 PROCESSING" : "FLUX.2 QUEUED"}</span>
            <strong>
              {fluxProgress.state === "processing"
                ? "Generating stylized frame"
                : `${fluxProgress.ahead} job${fluxProgress.ahead === 1 ? "" : "s"} ahead`}
            </strong>
          </div>
          <div className="flux-progress-rail" aria-hidden="true"><span /></div>
          <small>
            ComfyUI live queue
            {fluxProgress.steps ? ` · ${fluxProgress.steps} sampling steps` : ""}
            {fluxProgress.nodes ? ` · ${fluxProgress.nodes} nodes` : ""}
          </small>
        </div>
      )}
      <div className="scanline" />
      <div key={`sweep-${signalVersion}`} className="signal-sweep" aria-hidden="true" />
    </article>
  );
}

function MetricSparkline({ values, color, label }: { values: number[]; color: string; label: string }) {
  const width = 260;
  const height = 48;
  const maximum = Math.max(1, ...values);
  const points = values.map((value, index) => {
    const x = values.length > 1 ? (index / (values.length - 1)) * width : width;
    const y = height - ((value / maximum) * (height - 5)) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg className="metric-sparkline" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label={label}>
      <line x1="0" y1={height - 2} x2={width} y2={height - 2} className="spark-baseline" />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function GuardedControl({
  tone,
  label,
  sublabel,
  busy,
  onActivate,
}: {
  tone: "stop" | "restart" | "preflight";
  label: string;
  sublabel: string;
  busy: boolean;
  onActivate: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`guarded-control guard-${tone} ${open ? "cover-open" : ""}`}>
      <button
        type="button"
        className="guard-cover"
        aria-label={`${open ? "Close" : "Open"} ${label} safety cover`}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <i aria-hidden="true" />
        <span>{label}</span>
      </button>
      <button
        type="button"
        className="mushroom-button"
        disabled={!open || busy}
        onClick={() => {
          onActivate();
          setOpen(false);
        }}
      >
        <i aria-hidden="true" />
        <span>{busy ? "WORKING" : label}</span>
        <small>{sublabel}</small>
      </button>
    </div>
  );
}

export default function Home() {
  const [status, setStatus] = useState<Status>(emptyStatus);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState("Local control plane connected");
  // Keep the server and first browser render identical; start cache-busting
  // only after hydration completes.
  const [imageTick, setImageTick] = useState(0);
  const [confirmReset, setConfirmReset] = useState(false);
  const [diagnosticService, setDiagnosticService] = useState<Service | null>(null);
  const [resolveTarget, setResolveTarget] = useState<Service | null>(null);
  const [showPreflight, setShowPreflight] = useState(false);
  const healthy = status.services.filter((service) => service.online).length;

  async function refresh() {
    try {
      const [statusResponse, activityResponse, metricsResponse] = await Promise.all([
        fetch("/api/status", { cache: "no-store" }),
        fetch("/api/activity", { cache: "no-store" }),
        fetch("/api/metrics", { cache: "no-store" }),
      ]);
      if (statusResponse.ok) setStatus(await statusResponse.json());
      if (activityResponse.ok) setActivity((await activityResponse.json()).events);
      if (metricsResponse.ok) setMetrics(await metricsResponse.json());
    } catch {
      setNotice("");
    }
  }

  useEffect(() => {
    setImageTick(Date.now());
    refresh();
    const refreshVisible = () => {
      if (!document.hidden) refresh();
    };
    const refreshImagesVisible = () => {
      if (!document.hidden) setImageTick(Date.now());
    };
    const resume = () => {
      if (!document.hidden) {
        setImageTick(Date.now());
        refresh();
      }
    };
    const statusTimer = window.setInterval(refreshVisible, 1000);
    const imageTimer = window.setInterval(refreshImagesVisible, 1000);
    document.addEventListener("visibilitychange", resume);
    return () => {
      window.clearInterval(statusTimer);
      window.clearInterval(imageTimer);
      document.removeEventListener("visibilitychange", resume);
    };
  }, []);

  async function launch(mode: "manual" | "automatic" | "reset") {
    setBusy(mode);
    setNotice(
      mode === "manual"
        ? "Opening an interactive Hermes run…"
        : mode === "reset"
          ? "Authorizing a clean Rhino and Blender scene reset…"
          : "Starting automatic Cliff House run…",
    );
    try {
      const response = await fetch(mode === "reset" ? "/api/system-control" : "/api/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: mode }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? "Control action failed");
      setNotice(result.message ?? "Hermes launch requested");
      if (mode === "reset") {
        setConfirmReset(false);
        setMetrics(emptyMetrics);
        setImageTick(Date.now());
      }
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Hermes could not be launched");
    } finally {
      setBusy(null);
    }
  }

  async function systemAction(action: "emergency-stop" | "restart") {
    setBusy(action);
    setNotice(action === "emergency-stop"
      ? "EMERGENCY STOP in progress…"
      : "Restarting services and running full preflight…");
    try {
      const response = await fetch("/api/system-control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? "System control failed");
      setNotice(result.message);
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "System control failed");
    } finally {
      setBusy(null);
    }
  }

  async function runPreflight() {
    setBusy("preflight");
    setNotice("Running the complete AEC preflight suite…");
    try {
      const response = await fetch("/api/preflight", { method: "POST" });
      const result = await response.json();
      setNotice(result.message ?? result.error ?? "Preflight finished");
      await refresh();
      if (!response.ok && result.preflight) {
        setDiagnosticService(null);
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Preflight could not run");
    } finally {
      setBusy(null);
    }
  }

  async function resolveService(service: Service) {
    setBusy(`resolve-${service.id}`);
    setNotice(`Recovering ${service.name} and verifying a functional round trip…`);
    try {
      const response = await fetch("/api/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service: service.id }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? `${service.name} recovery failed`);
      setNotice(result.message);
      setResolveTarget(null);
      setDiagnosticService(null);
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : `${service.name} recovery failed`);
      await refresh();
    } finally {
      setBusy(null);
    }
  }

  async function sendPrompt(event: FormEvent) {
    event.preventDefault();
    const query = prompt.trim();
    if (!query) return;
    setBusy("query");
    setNotice("Sending instruction to the AEC Hermes profile…");
    try {
      const response = await fetch("/api/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "query", query }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setPrompt("");
      setNotice(result.message);
    } catch {
      setNotice("Instruction could not be started");
    } finally {
      setBusy(null);
    }
  }

  const phaseProgress = useMemo(() => {
    if (!status.phases.length) return 0;
    return Math.round((status.phases.filter((phase) => phase.state === "done").length / status.phases.length) * 100);
  }, [status.phases]);
  const currentPhase =
    status.phases.find((phase) => phase.state === "active")
    ?? status.phases.find((phase) => phase.state === "waiting")
    ?? status.phases.at(-1);
  const pipelineNodes = [
    { name: "Rhino", detail: "Geometry source", service: "Rhino", phase: 2 },
    { name: "Blender", detail: "Scene + camera", service: "Blender", phase: 4 },
    { name: "Control", detail: "Depth pass", service: "Blender", phase: 6 },
    { name: "FLUX.2", detail: "Final frame", service: "ComfyUI", phase: 7 },
  ];

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">CC</span>
          <div>
            <p className="kicker">AEC AGENT CONTROL PLANE</p>
            <h1>Cliff House <span>/ Live Build</span></h1>
          </div>
        </div>
        <div className="top-status">
          <div className="safety-bank" aria-label="Guarded system controls">
            <GuardedControl
              tone="stop"
              label="EMERGENCY STOP"
              sublabel="STOP ACTIVE RUN"
              busy={busy === "emergency-stop"}
              onActivate={() => systemAction("emergency-stop")}
            />
            <GuardedControl
              tone="preflight"
              label="PREFLIGHT CHECK"
              sublabel="FULL SYSTEM TEST"
              busy={busy === "preflight"}
              onActivate={runPreflight}
            />
            <GuardedControl
              tone="restart"
              label="RESTART"
              sublabel="PREFLIGHT + IDLE"
              busy={busy === "restart"}
              onActivate={() => systemAction("restart")}
            />
          </div>
          <div className="health">
            <span className={`pulse ${status.running ? "live" : ""}`} />
            <div>
              <strong>{status.runLabel}</strong>
              <small>{healthy}/{status.services.length || 5} systems online</small>
            </div>
          </div>
          <div className="clock">
            <small>RUN TIME</small>
            <strong>{status.elapsed}</strong>
          </div>
          <button className="icon-button" onClick={refresh} aria-label="Refresh dashboard">↻</button>
        </div>
      </header>

      <section className="service-strip" aria-label="Service health">
        {status.services.map((service) => (
          <div className={`service service-${service.status}`} key={service.name}>
            <button className="service-detail" onClick={() => setDiagnosticService(service)} title={`Inspect ${service.name} diagnostics`}>
              <span className={service.online ? "dot online" : "dot"} />
              <strong>{service.name}</strong>
              <span>{service.detail}</span>
            </button>
            {!service.online && service.resolvable && (
              <button className="resolve-button" onClick={() => setResolveTarget(service)}>
                Resolve
              </button>
            )}
          </div>
        ))}
        <div className={`scene-proof scene-${busy === "reset" ? "verifying" : status.sceneState.status}`}>
          <span className="scene-proof-lamp" />
          <div>
            <strong>
              {busy === "reset" || status.sceneState.status === "verifying"
                ? "VERIFYING EMPTY SCENES"
                : status.sceneState.status === "empty"
                  ? "RESET COMPLETE · SCENES EMPTY"
                  : status.sceneState.status === "occupied"
                    ? "GEOMETRY PRESENT"
                    : status.sceneState.status === "error"
                      ? "RESET CHECK FAILED"
                      : "SCENE STATE UNVERIFIED"}
            </strong>
            <small>
              {status.sceneState.status === "empty" || status.sceneState.status === "occupied"
                ? `Rhino ${status.sceneState.rhinoCount ?? "?"} active / ${
                    status.sceneState.rhinoTableCount ?? "?"
                  } retained · Blender ${
                    status.sceneState.blenderDefaultBaseline
                      ? `default (${status.sceneState.blenderCount ?? "?"})`
                      : status.sceneState.blenderCount ?? "?"
                  }`
                : "Green requires empty Rhino and an empty/default-only Blender scene"}
            </small>
          </div>
        </div>
        <button
          className={`preflight-summary preflight-${busy === "preflight" ? "running" : status.preflight.status}`}
          onClick={() => setShowPreflight(true)}
        >
          <i />
          <span>
            <strong>{busy === "preflight" ? "PREFLIGHT RUNNING" : `PREFLIGHT ${status.preflight.status.toUpperCase()}`}</strong>
            <small>
              {status.preflight.totalChecks
                ? `${status.preflight.totalChecks} checks · ${status.preflight.failedRequired ?? 0} failed`
                : "Open the guarded switch to test"}
            </small>
          </span>
        </button>
        <p className="updated">Updated {new Date(status.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</p>
      </section>

      <div className="workspace">
        <aside className="phase-panel panel">
          <div className="panel-heading">
            <div>
              <p className="kicker">BUILD SEQUENCE</p>
              <h2>Phases</h2>
            </div>
            <span className="percent">{phaseProgress}%</span>
          </div>
          <div className="progress-track"><span style={{ width: `${phaseProgress}%` }} /></div>
          <ol className="phase-list">
            {status.phases.map((phase) => (
              <li className={phase.state} key={phase.id}>
                <span className="phase-index">{phase.state === "done" ? "✓" : String(phase.id).padStart(2, "0")}</span>
                <div>
                  <strong>{phase.name}</strong>
                  <small>{phase.detail}</small>
                </div>
                {phase.state === "active" && <span className="active-bars"><i /><i /><i /></span>}
              </li>
            ))}
          </ol>
          <div className="run-controls">
            <p className="kicker">NEW RUN</p>
            <button className="primary-button" disabled={busy !== null} onClick={() => launch("automatic")}>
              <span>▶</span> {busy === "automatic" ? "Starting…" : "Run automatically"}
            </button>
            <button className="secondary-button" disabled={busy !== null} onClick={() => launch("manual")}>
              <span>◉</span> Build manually
            </button>
            <button className="danger-button" disabled={busy !== null} onClick={() => setConfirmReset(true)}>
              <span>↺</span> Reset scenes
            </button>
          </div>
        </aside>

        <section className="visual-stage">
          <div className="feed-grid">
            {feeds.map((feed) => (
              <LiveFeed
                feed={feed}
                tick={imageTick}
                enabled={
                  status.currentPhase >= feed.phase
                  || status.phases.find((phase) => phase.id === feed.phase)?.state === "done"
                }
                key={feed.key}
              />
            ))}
          </div>
          <section className="pipeline-deck" aria-label="Visual pipeline telemetry">
            <header className="pipeline-deck-header">
              <div>
                <p className="kicker">PIPELINE TELEMETRY</p>
                {status.running ? <strong>Build in motion</strong> : null}
              </div>
              <span className="notice">{notice}</span>
            </header>
            <div className="metrics-grid">
              <article className="metric-card chart-card">
                <header>
                  <div><p className="kicker">TOKENS PER SECOND</p><strong>{metrics.current.tps.toFixed(1)}</strong></div>
                  <span>{metrics.totals.tokensGenerated.toLocaleString()} GENERATED</span>
                </header>
                <MetricSparkline values={metrics.series.map((point) => point.tps)} color="#c7f36b" label="Tokens per second over the last twenty seconds" />
              </article>
              <article className="metric-card chart-card">
                <header>
                  <div><p className="kicker">AGENT ACTIONS / SEC</p><strong>{metrics.current.toolRate.toFixed(2)}</strong></div>
                  <span>{metrics.totals.toolCalls} TOTAL</span>
                </header>
                <MetricSparkline values={metrics.series.map((point) => point.toolRate)} color="#60d9d2" label="Agent actions per second over the last twenty seconds" />
              </article>
              <article className="metric-card counter-card retry-card">
                <p className="kicker">TOOL CALL RETRIES</p>
                <strong>{metrics.totals.retries}</strong>
                <small>Rejected · failed · timed out</small>
              </article>
              <article className="metric-card counter-card memory-card">
                <div className="memory-head">
                  <p className="kicker">MEMORY HARNESS RECALL</p>
                  <div className="memory-lamps" aria-label="DML memory activity">
                    <span className={metrics.memoryActivity.recallActive ? "active" : metrics.memoryActivity.lastRecallAt ? "seen" : ""}><i />READ</span>
                    <span className={metrics.memoryActivity.writeActive ? "active" : metrics.memoryActivity.lastStoreAt ? "seen" : ""}><i />WRITE</span>
                  </div>
                </div>
                <div className="memory-primary">
                  <strong>{metrics.totals.memoryRecalls}</strong>
                  <span>RECALL OPERATIONS</span>
                </div>
                <small>
                  {metrics.totals.memoriesAccessed} records returned · last read {memoryEventTime(metrics.memoryActivity.lastRecallAt)}
                  <br />
                  {metrics.totals.dmlCalls} DML calls · {metrics.totals.memoryStores} stores · last write {memoryEventTime(metrics.memoryActivity.lastStoreAt)}
                </small>
              </article>
            </div>
            <div className="pipeline-flow">
              {pipelineNodes.map((node, index) => {
                const service = status.services.find((item) => item.name === node.service);
                const complete = status.phases[node.phase - 1]?.state === "done";
                const active = status.currentPhase === node.phase && status.running;
                return (
                  <article className={`pipeline-node ${complete ? "complete" : ""} ${active ? "active" : ""}`} key={node.name}>
                    <span className="node-index">{String(index + 1).padStart(2, "0")}</span>
                    <div>
                      <strong>{node.name}</strong>
                      <small>{node.detail}</small>
                    </div>
                    <span className={`node-health ${service?.online ? "online" : ""}`}>
                      {complete ? "Passed" : service?.online ? "Ready" : "Offline"}
                    </span>
                  </article>
                );
              })}
            </div>
            <div className="pipeline-summary">
              <article>
                <p className="kicker">CURRENT OBJECTIVE</p>
                <strong>{currentPhase?.name ?? "Awaiting run"}</strong>
                <small>{currentPhase?.detail ?? "Rhino and Blender are ready for a new build."}</small>
              </article>
              <article className="completion-card">
                <p className="kicker">RUN COMPLETION</p>
                <div><strong>{phaseProgress}%</strong><span>{status.elapsed}</span></div>
                <span className="completion-track"><i style={{ width: `${phaseProgress}%` }} /></span>
              </article>
              <article>
                <p className="kicker">DELIVERY TARGET</p>
                <strong>One stylized frame</strong>
                <small>1920 × 1080 · FLUX.2 direct · no animation</small>
              </article>
            </div>
          </section>
        </section>

        <aside className="agent-panel panel">
          <div className="panel-heading">
            <div>
              <p className="kicker">HERMES</p>
              <h2>Agent stream</h2>
            </div>
            <span className="streaming"><i /> LIVE</span>
          </div>
          <div className="activity" aria-live="polite">
            {activity.length === 0 ? (
              <div className="empty-log">Waiting for Hermes activity…</div>
            ) : activity.map((event, index) => (
              <article className="event" key={`${event.time}-${index}`}>
                <div className={`event-icon ${event.kind}`}>
                  {event.kind === "mcp" ? "MCP" : event.kind === "memory" ? "DML" : event.kind === "tool" ? "↗" : event.kind === "model" ? "AI" : "•"}
                </div>
                <div>
                  <time>{event.time}</time>
                  <p>{event.text}</p>
                </div>
              </article>
            ))}
          </div>
          <form className="composer" onSubmit={sendPrompt}>
            <label htmlFor="hermes-prompt">Send an instruction to Hermes</label>
            <textarea
              id="hermes-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="e.g. Run the Cliff House build automatically"
              rows={3}
            />
            <div className="composer-footer">
              <span>Full AEC profile · DML enabled</span>
              <button disabled={busy !== null || !prompt.trim()} aria-label="Send instruction">
                {busy === "query" ? "…" : "↑"}
              </button>
            </div>
          </form>
        </aside>
      </div>
      {confirmReset && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setConfirmReset(false)}>
          <section
            className="confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reset-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p className="kicker">DESTRUCTIVE LIVE-SCENE ACTION</p>
            <h2 id="reset-title">Reset Rhino and Blender?</h2>
            <p>
              This removes every object from the currently open Rhino document and Blender scene,
              verifies both are empty, and leaves the resident agent ready for a fresh run.
            </p>
            <div className="modal-note">
              Saved project files and run history are retained. Unsaved live-scene work is not.
            </div>
            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setConfirmReset(false)}>Cancel</button>
              <button className="modal-confirm" disabled={busy !== null} onClick={() => launch("reset")}>
                {busy === "reset" ? "Resetting…" : "Reset both scenes"}
              </button>
            </div>
          </section>
        </div>
      )}
      {diagnosticService && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setDiagnosticService(null)}>
          <section className="confirm-modal diagnostic-modal" role="dialog" aria-modal="true" aria-labelledby="diagnostic-title" onMouseDown={(event) => event.stopPropagation()}>
            <p className="kicker">FUNCTIONAL SERVICE DIAGNOSTICS</p>
            <h2 id="diagnostic-title">{diagnosticService.name} · {diagnosticService.status}</h2>
            <p>{diagnosticService.detail}</p>
            <div className="diagnostic-checks">
              {diagnosticService.checks.map((check) => (
                <article className={`diagnostic-check check-${check.state}`} key={check.id}>
                  <i />
                  <div>
                    <strong>{check.label}</strong>
                    <span>{check.detail}</span>
                  </div>
                </article>
              ))}
            </div>
            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setDiagnosticService(null)}>Close</button>
              {!diagnosticService.online && diagnosticService.resolvable && (
                <button className="modal-confirm" onClick={() => {
                  setDiagnosticService(null);
                  setResolveTarget(diagnosticService);
                }}>Resolve {diagnosticService.name}</button>
              )}
            </div>
          </section>
        </div>
      )}
      {resolveTarget && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setResolveTarget(null)}>
          <section className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="resolve-title" onMouseDown={(event) => event.stopPropagation()}>
            <p className="kicker">TARGETED SERVICE RECOVERY</p>
            <h2 id="resolve-title">Recover {resolveTarget.name}?</h2>
            <p>
              {resolveTarget.id === "hermes"
                ? "This replaces the failed coordinator with a warm, idle Hermes worker and verifies it is responsive."
                : `This restarts ${resolveTarget.name}, reconnects its MCP bridge, and requires a successful functional tool round trip.`}
            </p>
            {resolveTarget.id !== "hermes" && (
              <div className="modal-note">Unsaved work in {resolveTarget.name} will be lost.</div>
            )}
            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setResolveTarget(null)}>Cancel</button>
              <button className="modal-confirm" disabled={busy !== null} onClick={() => resolveService(resolveTarget)}>
                {busy === `resolve-${resolveTarget.id}` ? "Recovering…" : `Resolve ${resolveTarget.name}`}
              </button>
            </div>
          </section>
        </div>
      )}
      {showPreflight && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowPreflight(false)}>
          <section className="confirm-modal diagnostic-modal preflight-modal" role="dialog" aria-modal="true" aria-labelledby="preflight-title" onMouseDown={(event) => event.stopPropagation()}>
            <p className="kicker">COMPLETE AEC READINESS RECEIPT</p>
            <h2 id="preflight-title">Preflight · {status.preflight.status}</h2>
            <p>
              {status.preflight.status === "idle"
                ? "No full preflight has been run from this control session."
                : `${status.preflight.totalChecks ?? 0} checks completed with ${status.preflight.failedRequired ?? 0} required failures.`}
            </p>
            <PreflightCheckList checks={status.preflight.checks ?? []} />
            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setShowPreflight(false)}>Close</button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
