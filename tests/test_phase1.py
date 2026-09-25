from pathlib import Path

import pytest

from sentinel import SpecError, ingest

SAMPLE = (Path(__file__).parent.parent / "samples" / "vuln_api.yaml").read_text()


def ep(inv, eid):
    return next(e for e in inv.endpoints if e.id == eid)


def test_sample_inventory():
    inv = ingest(SAMPLE)
    assert inv.title == "VulnShop" and inv.spec_version == "3.0.3"
    assert len(inv.endpoints) == 7
    assert not ep(inv, "DELETE /admin/users").requires_auth
    assert not ep(inv, "GET /debug/config").requires_auth
    assert ep(inv, "GET /orders").requires_auth  # inherits global
    assert ep(inv, "GET /files").security == [{"apiKey": []}]
    u = ep(inv, "GET /users/{userId}")
    assert u.params[0].name == "userId" and u.params[0].location == "path"
    props = u.responses["200"]["schema"]["properties"]
    assert "password_hash" in props and props["manager"].get("circular")


def test_swagger2():
    inv = ingest("""swagger: '2.0'
info: {title: T, version: '1'}
host: api.x
basePath: /v1
paths:
  /p:
    post:
      parameters: [{name: b, in: body, schema: {type: object}}, {name: q, in: query, type: string}]
      responses: {'200': {description: ok, schema: {type: string}}}""")
    e = inv.endpoints[0]
    assert inv.servers == ["https://api.x/v1"]
    assert e.request_body["schema"] == {"type": "object"} and e.params[0].schema == {"type": "string"}


@pytest.mark.parametrize("bad", [b"", b"\xff\xfe", "[1,2]", "foo: [", "openapi: 4.0\npaths: {}",
                                 "info: {}\npaths: {}", "openapi: 3.0.0\ninfo: {}"])
def test_invalid(bad):
    with pytest.raises(SpecError):
        ingest(bad)


def test_broken_ref_warns():
    inv = ingest('{"openapi":"3.0.0","info":{"title":"T","version":"1"},"paths":{"/a":{"get":{"parameters":[{"$ref":"#/nope"}]}}}}')
    assert any("Broken $ref" in w for w in inv.warnings)


def test_preserves_all_media_types_and_required_form_fields():
    inv = ingest("""openapi: 3.0.3
info: {title: T, version: '1'}
paths:
  /multi:
    post:
      requestBody:
        content:
          application/json: {schema: {type: object}}
          application/xml: {schema: {type: string}}
      responses:
        '200':
          description: ok
          content:
            application/json: {schema: {type: object}}
            text/plain: {schema: {type: string}}
  /form:
    post:
      consumes: [multipart/form-data]
      parameters:
        - {name: avatar, in: formData, type: string, required: true}
        - {name: note, in: formData, type: string}
      responses: {'204': {description: done}}
""")
    multi = next(e for e in inv.endpoints if e.path == "/multi")
    assert multi.request_body["content_types"] == ["application/json", "application/xml"]
    assert multi.request_body["content"]["application/xml"]["schema"]["type"] == "string"
    assert multi.responses["200"]["content_types"] == ["application/json", "text/plain"]
    form = next(e for e in inv.endpoints if e.path == "/form")
    assert form.request_body is None


def test_preserves_required_swagger_form_fields():
    inv = ingest("""swagger: '2.0'
info: {title: T, version: '1'}
paths:
  /form:
    post:
      consumes: [multipart/form-data]
      parameters:
        - {name: avatar, in: formData, type: string, required: true}
        - {name: note, in: formData, type: string}
      responses: {'204': {description: done}}
""")
    form = next(e for e in inv.endpoints if e.path == "/form")
    assert form.request_body["required"] is True
    assert form.request_body["schema"]["required"] == ["avatar"]


def test_requires_info_metadata():
    with pytest.raises(SpecError, match="info.title"):
        ingest("openapi: 3.0.3\ninfo: {}\npaths: {}")


def test_api(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINEL_DB", str(tmp_path / "t.db"))
    import importlib, app
    importlib.reload(app)
    from fastapi.testclient import TestClient
    c = TestClient(app.app)
    r = c.post("/specs", files={"file": ("s.yaml", SAMPLE)})
    assert r.status_code == 200 and r.json()["endpoints"] == 7
    assert c.get(f"/specs/{r.json()['id']}").json()["endpoints"][0]["id"] == "POST /login"
    assert c.post("/specs", files={"file": ("x.json", "{bad")}).status_code == 422
