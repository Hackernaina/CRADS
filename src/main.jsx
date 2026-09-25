import React, { useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity, AlertTriangle, ArrowUpRight, Bot, CheckCircle2, ChevronRight,
  CircleDot, CloudUpload, Code2, FileJson, GitBranch, Gauge, KeyRound,
  LayoutDashboard, LockKeyhole, Menu, Network, Play, Radar, RefreshCw,
  Search, Server, Shield, ShieldAlert, ShieldCheck, Terminal, Upload,
  X, Zap
} from "lucide-react";
import "./styles.css";

const findings = [
  {
    id: "BOLA-001",
    severity: "Critical",
    type: "Broken Object-Level Authorization",
    endpoint: "GET /orders/{order_id}",
    status: "Confirmed",
    summary: "User A can access an order belonging to User B.",
    evidence: "Expected 403 Forbidden, received 200 OK with another user's order.",
    poc: "GET /orders/201\\nAuthorization: Bearer <USER_A_TOKEN>",
    recommendation: "Validate object ownership against the authenticated user before returning the resource."
  },
  {
    id: "DATA-002",
    severity: "High",
    type: "Potential Sensitive Data Exposure",
    endpoint: "GET /users/{user_id}",
    status: "Needs review",
    summary: "Response contains fields that may not be required by the client.",
    evidence: "password_hash, internal_notes and api_key-like fields detected.",
    poc: "GET /users/102\\nAuthorization: Bearer <USER_TOKEN>",
    recommendation: "Return only fields required by the client and remove secrets from API responses."
  },
  {
    id: "AUTH-003",
    severity: "High",
    type: "Authentication Misconfiguration",
    endpoint: "GET /payments/{payment_id}",
    status: "Confirmed",
    summary: "Sensitive payment resource responds without authentication.",
    evidence: "Unauthenticated request returned 200 OK.",
    poc: "GET /payments/301",
    recommendation: "Require authentication and reject unauthenticated access with 401."
  },
  {
    id: "RATE-004",
    severity: "Medium",
    type: "Weak Rate Limiting",
    endpoint: "POST /login",
    status: "Potential",
    summary: "No 429 response observed during controlled test requests.",
    evidence: "Test burst completed without an apparent rate-limit response.",
    poc: "POST /login\\nContent-Type: application/json\\n\\n{ \"email\": \"test@example.com\" }",
    recommendation: "Apply endpoint-appropriate throttling and return 429 when limits are exceeded."
  }
];

const endpoints = [
  ["GET", "/users/{user_id}", "Auth", "2 findings"],
  ["GET", "/orders/{order_id}", "Auth", "1 critical"],
  ["POST", "/orders", "Auth", "Clean"],
  ["GET", "/payments/{payment_id}", "Auth", "1 high"],
  ["POST", "/login", "Public", "1 medium"],
  ["GET", "/products/{product_id}", "Public", "Clean"],
];

function Badge({ children, tone="neutral" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function Severity({ value }) {
  return <Badge tone={value.toLowerCase()}>{value}</Badge>;
}

function Stat({ icon: Icon, label, value, hint }) {
  return (
    <div className="stat-card">
      <div className="stat-icon"><Icon size={18}/></div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
        {hint && <div className="stat-hint">{hint}</div>}
      </div>
    </div>
  );
}

function Sidebar({ page, setPage }) {
  const items = [
    ["dashboard", "Dashboard", LayoutDashboard],
    ["scan", "New Scan", Radar],
    ["findings", "Findings", ShieldAlert],
    ["attack-surface", "Attack Surface", Network],
    ["history", "Scan History", Activity],
    ["ci", "CI / CD", GitBranch],
  ];
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Shield size={20}/></div>
        <div><strong>Sentinel<span>API</span></strong><small>Zero-trust scanner</small></div>
      </div>
      <div className="workspace">
        <span>WORKSPACE</span>
        <button><Server size={15}/> Demo E-Commerce API <ChevronRight size={14}/></button>
      </div>
      <nav>
        {items.map(([id,label,Icon]) => (
          <button key={id} className={page===id ? "nav-item active" : "nav-item"} onClick={()=>setPage(id)}>
            <Icon size={17}/><span>{label}</span>
            {id==="findings" && <em>4</em>}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="safe-box"><ShieldCheck size={17}/><div><strong>Safe scanning</strong><small>Sandbox target only</small></div></div>
        <button className="user-row"><div className="avatar">NA</div><div><strong>Nainika</strong><small>Developer</small></div></button>
      </div>
    </aside>
  );
}

function Header({ page, setMobile }) {
  const titles = {
    dashboard: ["Security overview", "Monitor your API security posture."],
    scan: ["New security scan", "Upload an API definition and configure your scan."],
    findings: ["Security findings", "Investigate, reproduce and remediate detected issues."],
    "attack-surface": ["Attack surface", "Map endpoints, resources and security boundaries."],
    history: ["Scan history", "Track security changes across previous scans."],
    ci: ["CI / CD security gate", "Automate API security checks before deployment."]
  };
  const [title, subtitle] = titles[page] || titles.dashboard;
  return <header className="topbar">
    <button className="mobile-menu" onClick={()=>setMobile(true)}><Menu size={20}/></button>
    <div><h1>{title}</h1><p>{subtitle}</p></div>
    <div className="header-actions">
      <div className="target-pill"><CircleDot size={13}/> Demo target <span>Online</span></div>
      <button className="icon-button"><Search size={18}/></button>
      <div className="avatar">NA</div>
    </div>
  </header>;
}

function Dashboard({ setPage, selectedFinding, setSelectedFinding }) {
  return <main className="content">
    <section className="hero">
      <div>
        <div className="eyebrow"><Zap size={14}/> LAST SCAN · 4 MIN AGO</div>
        <h2>Your API has <span>4 security findings.</span></h2>
        <p>SentinelAPI tested 42 endpoints with 126 automated security checks.</p>
      </div>
      <button className="primary" onClick={()=>setPage("scan")}><Play size={16}/> Run new scan</button>
    </section>

    <div className="stats-grid">
      <Stat icon={Server} value="42" label="Endpoints scanned" hint="6 new since last scan"/>
      <Stat icon={Gauge} value="126" label="Security tests" hint="BOLA, auth, exposure, rate limit"/>
      <Stat icon={ShieldAlert} value="4" label="Findings" hint="2 require immediate attention"/>
      <Stat icon={CheckCircle2} value="92%" label="Protected endpoints" hint="↑ 8% from previous scan"/>
    </div>

    <div className="dashboard-grid">
      <section className="panel findings-panel">
        <div className="panel-head"><div><h3>Priority findings</h3><p>Evidence-backed issues detected in the latest scan.</p></div><button className="text-btn" onClick={()=>setPage("findings")}>View all <ArrowUpRight size={14}/></button></div>
        <div className="finding-list">
          {findings.slice(0,3).map(f=><button className="finding-row" key={f.id} onClick={()=>setSelectedFinding(f)}>
            <div className={`finding-icon ${f.severity.toLowerCase()}`}>{f.severity==="Critical"?<AlertTriangle size={17}/>:<ShieldAlert size={17}/>}</div>
            <div className="finding-main"><strong>{f.type}</strong><span>{f.endpoint}</span></div>
            <Severity value={f.severity}/><ChevronRight size={16} className="chevron"/>
          </button>)}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><h3>Risk distribution</h3><p>Latest scan by severity.</p></div></div>
        <div className="risk-chart">
          <div className="donut"><div><strong>4</strong><span>findings</span></div></div>
          <div className="legend">
            <div><i className="dot critical"></i> Critical <b>1</b></div>
            <div><i className="dot high"></i> High <b>2</b></div>
            <div><i className="dot medium"></i> Medium <b>1</b></div>
            <div><i className="dot low"></i> Low <b>0</b></div>
          </div>
        </div>
      </section>
    </div>

    <section className="panel">
      <div className="panel-head"><div><h3>API security coverage</h3><p>What SentinelAPI checks automatically.</p></div></div>
      <div className="coverage-grid">
        {[
          [LockKeyhole,"Authorization flaws","BOLA / IDOR and function-level authorization","tested", "green"],
          [Code2,"Data exposure","Sensitive and unnecessary response fields","tested", "green"],
          [KeyRound,"Authentication","Missing or weak authentication controls","tested", "green"],
          [Gauge,"Rate limiting","Controlled abuse and throttling signals","tested", "amber"],
        ].map(([Icon,title,desc,status,tone])=><div className="coverage-card" key={title}><div className="coverage-icon"><Icon size={18}/></div><div><strong>{title}</strong><p>{desc}</p></div><Badge tone={tone}>{status}</Badge></div>)}
      </div>
    </section>
  </main>;
}

function ScanPage({ setPage }) {
  const [drag, setDrag] = useState(false);
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [checks, setChecks] = useState([true, true, true, false]);
  const fileInput = useRef(null);

  const selectFile = (nextFile) => {
    if (!nextFile) return;
    const validExtension = /\.(json|ya?ml)$/i.test(nextFile.name);
    if (!validExtension) {
      setFile(null);
      setFileError("Choose an OpenAPI or Swagger JSON, YAML, or YML file.");
      return;
    }
    if (nextFile.size > 10 * 1024 * 1024) {
      setFile(null);
      setFileError("The specification must be 10 MB or smaller.");
      return;
    }
    setFile(nextFile);
    setFileError("");
  };

  const openFilePicker = () => fileInput.current?.click();

  return <main className="content">
    <div className="scan-layout">
      <section className="panel scan-card">
        <div className="section-number">01</div>
        <h3>Provide your API definition</h3>
        <p>Upload an OpenAPI / Swagger JSON or YAML file. Live traffic support can be connected later.</p>
        <input
          ref={fileInput}
          className="file-input"
          type="file"
          accept=".json,.yaml,.yml,application/json,application/yaml,text/yaml"
          onChange={(event) => {
            selectFile(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
        <div
          className={drag ? "dropzone drag" : "dropzone"}
          onDragEnter={(event) => { event.preventDefault(); setDrag(true); }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setDrag(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDrag(false);
            selectFile(event.dataTransfer.files?.[0]);
          }}
          onClick={openFilePicker}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") openFilePicker();
          }}
        >
          {file ? <><div className="upload-success"><CheckCircle2 size={26}/></div><strong>{file.name}</strong><span>Specification selected · ready to scan</span><button className="small-btn" onClick={(event)=>{event.stopPropagation();openFilePicker();}}>Replace file</button></> :
          <><div className="upload-icon"><CloudUpload size={26}/></div><strong>Choose your OpenAPI file</strong><span>Click to browse or drop JSON, YAML, or YML · up to 10 MB</span></>}
        </div>
        {fileError && <p className="upload-error" role="alert">{fileError}</p>}
      </section>

      <section className="panel scan-card">
        <div className="section-number">02</div>
        <h3>Configure security tests</h3>
        <p>Select which controlled checks should run against the authorized sandbox target.</p>
        <div className="check-list">
          {["Authorization / BOLA","Sensitive data exposure","Authentication misconfiguration","Rate limiting"].map((x,i)=><label key={x}>
            <input
              type="checkbox"
              checked={checks[i]}
              onChange={() => setChecks((current) => current.map((enabled, index) => index === i ? !enabled : enabled))}
            />
            <span><b>{x}</b><small>{["Cross-user object access","Sensitive response fields","Missing auth controls","Controlled request bursts"][i]}</small></span>
            <button
              type="button"
              className={`toggle ${checks[i] ? "on" : ""}`}
              aria-label={`${checks[i] ? "Disable" : "Enable"} ${x}`}
              aria-pressed={checks[i]}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                setChecks((current) => current.map((enabled, index) => index === i ? !enabled : enabled));
              }}
            />
          </label>)}
        </div>
      </section>
    </div>
    <section className="panel scan-target">
      <div><div className="section-number">03</div><h3>Authorized target</h3><p>Only scan systems you own or have explicit permission to test.</p></div>
      <div className="target-input"><LockKeyhole size={16}/><span>http://localhost:8000</span><Badge tone="green">Sandbox</Badge></div>
      <button className="primary" onClick={()=>setPage("findings")}><Radar size={16}/> Start scan</button>
    </section>
  </main>;
}

function FindingsPage({ selectedFinding, setSelectedFinding }) {
  const [filter, setFilter] = useState("All");
  const visible = filter==="All" ? findings : findings.filter(f=>f.severity===filter);
  return <main className="content">
    <div className="filterbar">
      <div className="filters">{["All","Critical","High","Medium"].map(x=><button key={x} className={filter===x?"filter active":"filter"} onClick={()=>setFilter(x)}>{x}{x!=="All" && <span>{findings.filter(f=>f.severity===x).length}</span>}</button>)}</div>
      <button className="secondary"><RefreshCw size={15}/> Re-test selected</button>
    </div>
    <div className="findings-layout">
      <section className="panel">
        <div className="panel-head"><div><h3>Findings</h3><p>Each result includes evidence and a reproducible proof of concept.</p></div><Badge tone="neutral">{visible.length} results</Badge></div>
        <div className="table">
          {visible.map(f=><button className={`table-row ${selectedFinding?.id===f.id?"selected":""}`} key={f.id} onClick={()=>setSelectedFinding(f)}>
            <div className={`severity-bar ${f.severity.toLowerCase()}`}></div>
            <div className="finding-main"><strong>{f.type}</strong><span>{f.endpoint}</span></div>
            <Severity value={f.severity}/><span className="status-text">{f.status}</span><ChevronRight size={15}/>
          </button>)}
        </div>
      </section>
      <FindingDetail finding={selectedFinding || findings[0]} />
    </div>
  </main>;
}

function FindingDetail({ finding }) {
  return <aside className="panel detail-panel">
    <div className="detail-top"><Severity value={finding.severity}/><span>{finding.id}</span></div>
    <h3>{finding.type}</h3>
    <code className="endpoint">{finding.endpoint}</code>
    <p>{finding.summary}</p>
    <div className="detail-block"><label>Evidence</label><div className="evidence"><AlertTriangle size={15}/>{finding.evidence}</div></div>
    <div className="detail-block"><label>Proof of concept</label><pre>{finding.poc}</pre><button className="copy-btn">Copy request</button></div>
    <div className="detail-block"><label>Recommended remediation</label><div className="remediation"><CheckCircle2 size={15}/>{finding.recommendation}</div></div>
    <div className="ai-box"><div className="ai-title"><Bot size={16}/> Sentinel AI analysis <Badge tone="purple">Beta</Badge></div><p>The evidence suggests an authorization boundary is not being enforced consistently. Fix the server-side authorization check, then use <b>Re-test</b> to validate the remediation.</p></div>
  </aside>;
}

function AttackSurface() {
  return <main className="content">
    <section className="panel">
      <div className="panel-head"><div><h3>API attack surface</h3><p>42 endpoints discovered from the OpenAPI specification.</p></div><Badge tone="green">42 discovered</Badge></div>
      <div className="endpoint-table">
        <div className="endpoint-head"><span>Method</span><span>Endpoint</span><span>Access</span><span>Result</span></div>
        {endpoints.map(([method,path,access,result])=><div className="endpoint-row" key={path}><Badge tone={method==="GET"?"blue":"purple"}>{method}</Badge><code>{path}</code><span>{access}</span><span className={result.includes("Clean")?"clean":result.includes("critical")?"critical-text":"high-text"}>{result}</span></div>)}
      </div>
    </section>
    <section className="panel graph-panel">
      <div className="panel-head"><div><h3>Resource relationship map</h3><p>Visualize potential authorization boundaries.</p></div></div>
      <div className="graph">
        <div className="node root">API</div><div className="line l1"></div><div className="node user">Users</div><div className="node order danger">Orders <small>1 critical</small></div><div className="node payment warning">Payments <small>1 high</small></div><div className="node product">Products</div>
      </div>
    </section>
  </main>;
}

function History() {
  return <main className="content"><section className="panel"><div className="panel-head"><div><h3>Scan history</h3><p>Security posture across previous scans.</p></div><button className="secondary"><RefreshCw size={15}/> Refresh</button></div>
    <div className="history-list">{[
      ["Today, 14:02","OpenAPI v1.8","42","4","2 critical","Current"],
      ["Today, 11:18","OpenAPI v1.7","36","7","3 critical","Previous"],
      ["Yesterday, 18:42","OpenAPI v1.6","36","9","4 critical","Previous"],
    ].map(r=><div className="history-row" key={r[0]}><div><strong>{r[0]}</strong><span>{r[1]}</span></div><span>{r[2]} endpoints</span><span>{r[3]} findings</span><span className="critical-text">{r[4]}</span><Badge tone={r[5]==="Current"?"green":"neutral"}>{r[5]}</Badge><ChevronRight size={15}/></div>)}</div>
  </section></main>;
}

function CI() {
  return <main className="content"><div className="ci-grid">
    <section className="panel ci-card"><div className="ci-icon"><GitBranch size={22}/></div><h3>Security gate for CI/CD</h3><p>Fail builds when configured severity thresholds are detected.</p><div className="code-box"><span>$</span> sentinel scan openapi.yaml --fail-on critical</div><div className="pipeline"><div><CheckCircle2 size={17}/> Build</div><div><ChevronRight size={15}/></div><div><Radar size={17}/> SentinelAPI</div><div><ChevronRight size={15}/></div><div><ShieldCheck size={17}/> Pass / Fail</div></div></section>
    <section className="panel"><div className="panel-head"><div><h3>Gate policy</h3><p>Example frontend configuration.</p></div></div><div className="policy"><label>Fail on <select defaultValue="critical"><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option></select></label><label className="switch-row"><input type="checkbox" defaultChecked/> Block deployment</label><label className="switch-row"><input type="checkbox" defaultChecked/> Comment findings on PR</label></div></section>
  </div></main>;
}

function App() {
  const [page,setPage]=useState("dashboard");
  const [mobile,setMobile]=useState(false);
  const [selectedFinding,setSelectedFinding]=useState(null);
  const body = page==="dashboard" ? <Dashboard setPage={setPage} selectedFinding={selectedFinding} setSelectedFinding={(f)=>{setSelectedFinding(f);setPage("findings")}}/> :
    page==="scan" ? <ScanPage setPage={setPage}/> :
    page==="findings" ? <FindingsPage selectedFinding={selectedFinding} setSelectedFinding={setSelectedFinding}/> :
    page==="attack-surface" ? <AttackSurface/> :
    page==="history" ? <History/> : <CI/>;
  return <div className="app">
    <div className={mobile?"mobile-overlay open":"mobile-overlay"} onClick={()=>setMobile(false)}></div>
    <div className={mobile?"mobile-sidebar open":"mobile-sidebar"}><Sidebar page={page} setPage={(p)=>{setPage(p);setMobile(false)}}/><button className="mobile-close" onClick={()=>setMobile(false)}><X/></button></div>
    <div className="desktop-sidebar"><Sidebar page={page} setPage={setPage}/></div>
    <div className="main"><Header page={page} setMobile={setMobile}/>{body}</div>
  </div>;
}

createRoot(document.getElementById("root")).render(<App />);
