"""Minimal web layer: upload spec -> store -> view inventory.
Run: uvicorn app:app --reload
"""
import os

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from sentinel import SpecError, ingest
from sentinel.planner import build_plan
from sentinel.store import Store

app = FastAPI(title="SentinelAPI — Phase 1")
store = Store(os.getenv("SENTINEL_DB", "sentinel.db"))


@app.post("/specs")
async def upload(file: UploadFile):
    try:
        inv = ingest(await file.read())
    except SpecError as e:
        raise HTTPException(422, str(e))
    sid = store.save(inv)
    return {"id": sid, "title": inv.title, "endpoints": len(inv.endpoints), "warnings": inv.warnings}


@app.get("/specs")
def list_specs():
    return store.list()


@app.get("/specs/{sid}")
def get_spec(sid: str):
    inv = store.get(sid)
    if not inv:
        raise HTTPException(404, "Not found")
    return inv


@app.post("/specs/{sid}/plan")
def make_plan(sid: str, use_llm: bool = True):
    """Phase 2: build a test plan from a stored inventory. Plans nothing to run
    against real targets — output is authorized-sandbox-only documentation."""
    from sentinel.models import Inventory
    data = store.get(sid)
    if not data:
        raise HTTPException(404, "Not found")
    plan = build_plan(Inventory.from_dict(data), use_llm=use_llm)
    return plan.to_dict()


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


PAGE = """<!doctype html><meta charset=utf-8><title>SentinelAPI</title>
<style>body{font:14px system-ui;max-width:960px;margin:2em auto;padding:0 1em}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left}
.err{color:#b00}.m{font-weight:600;font-family:monospace}</style>
<h2>SentinelAPI · Spec Ingest</h2>
<input type=file id=f accept=".json,.yaml,.yml"> <button onclick=up()>Upload</button>
<p id=msg></p><div id=out></div>
<script>
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function up(){
  const f=document.getElementById('f').files[0]; if(!f) return;
  const fd=new FormData(); fd.append('file',f);
  const r=await fetch('/specs',{method:'POST',body:fd}), j=await r.json(), msg=document.getElementById('msg');
  if(!r.ok){msg.className='err';msg.textContent='Error: '+j.detail;document.getElementById('out').innerHTML='';return}
  msg.className='';msg.textContent=`Stored ${j.id} — ${j.endpoints} endpoints`+(j.warnings.length?` · ${j.warnings.length} warning(s)`:'');
  window._sid=j.id;
  const inv=await (await fetch('/specs/'+j.id)).json();
  document.getElementById('out').innerHTML=`<h3>${esc(inv.title)} ${esc(inv.version)} (OpenAPI ${esc(inv.spec_version)})</h3>
  <button onclick=plan()>Build test plan (Phase 2)</button><div id=plan></div>
  ${inv.warnings.map(w=>`<div class=err>⚠ ${esc(w)}</div>`).join('')}
  <table><tr><th>Method</th><th>Path</th><th>Params</th><th>Body</th><th>Auth</th><th>Responses</th></tr>
  ${inv.endpoints.map(e=>`<tr><td class=m>${e.method}</td><td>${esc(e.path)}</td>
  <td>${e.params.map(p=>esc(p.name)+'<small>('+p.location+')</small>').join(', ')}</td>
  <td>${e.request_body?esc(e.request_body.content_types.join(', ')):''}</td>
  <td>${e.requires_auth?esc(e.security.flatMap(Object.keys).join(', ')):'<b class=err>none</b>'}</td>
  <td>${Object.keys(e.responses).join(', ')}</td></tr>`).join('')}</table>`;
}
async function plan(){
  const p=await (await fetch(`/specs/${window._sid}/plan`,{method:'POST'})).json();
  const col={high:'#b00',medium:'#c60',low:'#888'};
  document.getElementById('plan').innerHTML=`<p><small>scope: ${esc(p.scope)} · model: ${esc(p.model)} · skipped: ${p.skipped.length}</small></p>`+
  p.endpoints.map(e=>`<div style="border-left:4px solid ${col[e.risk]};padding:4px 10px;margin:8px 0">
   <span class=m>${e.method} ${esc(e.path)}</span> <b style=color:${col[e.risk]}>${e.risk}</b>
   <div><small>${esc(e.reason)}</small></div>
   ${e.test_cases.map(c=>`<div style=margin-top:4px>• <b>${esc(c.category)}</b> ${esc(c.hypothesis)}
     <br><small>accounts: ${c.required_accounts.map(a=>esc(a.role)).join(', ')} — ${c.steps.map(s=>esc(s.action)).join(' ')}</small></div>`).join('')}
  </div>`).join('');
}
</script>"""
