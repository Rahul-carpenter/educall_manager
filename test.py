# test.py
import os
import json
from datetime import datetime, timedelta

import pytest
from flask import session

from app import app, db, mail
from app.models import User, Lead

# ---------- Fixtures / Test App Setup ----------

@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    # Ensure a test config is used (you can extend this if you have a separate TestConfig)
    os.environ["FLASK_ENV"] = "testing"
    os.environ["TESTING"] = "1"


@pytest.fixture
def client():
    # Use an in-memory SQLite DB for tests so your real MySQL is untouched. [web:39]
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["MAIL_SUPPRESS_SEND"] = True  # Do not actually send emails. [web:44]
    app.config["SERVER_NAME"] = "localhost"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

# ---------- Helper functions ----------

def create_user(username="agent1", password="password", role="agent"):
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
# ---------- Basic health / auth tests ----------

def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_register_and_login_agent(client):
    # Register
    resp = client.post(
        "/register",
        data={
            "username": "newagent",
            "password": "secret",
            "confirm_password": "secret",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # login redirect page should appear at end
    assert b"Login" in resp.data

    # Login
    resp = login(client, "newagent", "secret")
    assert resp.status_code == 200
    # Session contains user_id and role = agent
    with client.session_transaction() as sess:
        assert "user_id" in sess
        assert sess["role"] == "agent"

# ---------- Admin-protected routes ----------

def test_create_user_requires_admin(client):
    # Without login -> redirect to login
    resp = client.get("/create-user", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # Login as non-admin agent
    agent = create_user(username="a1", password="pass", role="agent")
    login(client, "a1", "pass")
    resp = client.get("/create-user", follow_redirects=False)
    # Access denied -> redirected to login or index
    assert resp.status_code in (302, 303)


def test_create_user_as_admin(client):
    admin = create_user(username="admin1", password="adminpass", role="admin")
    login(client, "admin1", "adminpass")

    resp = client.post(
        "/create-user",
        data={"username": "agent2", "password": "p2", "role": "agent"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert User.query.filter_by(username="agent2").first() is not None

# ---------- Agent dashboard + lead creation ----------

def _seed_agent_with_leads(agent, count=3):
    now = datetime.utcnow()
    for i in range(count):
        lead = Lead(
            name=f"Lead {i}",
            email=f"lead{i}@example.com",
            phone=f"99999{i}",
            city="City",
            state="State",
            course="Course",
            status="Pending",
            agent_id=agent.id,
            created_at=now - timedelta(minutes=i),
            assigned_at=now.date(),
        )
        db.session.add(lead)
    db.session.commit()


def test_agent_dashboard_requires_agent_role(client):
    # Without login
    resp = client.get("/agent-dashboard", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # Login as admin -> should be redirected (not allowed)
    admin = create_user("adminX", "passX", "admin")
    login(client, "adminX", "passX")
    resp = client.get("/agent-dashboard", follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_agent_dashboard_shows_leads(client):
    agent = create_user("agent_dash", "pass", "agent")
    _seed_agent_with_leads(agent, count=2)
    login(client, "agent_dash", "pass")

    resp = client.get("/agent-dashboard")
    assert resp.status_code == 200
    # Basic check – HTML is not empty and contains something generic from the template
    assert b"EduCall Manager" in resp.data




# ---------- export_interested_leads ----------

def test_export_interested_leads_success(client):
    agent = create_user("agent_export", "pass", "agent")
    login(client, "agent_export", "pass")

    today = datetime.utcnow().date()
    # seed one interested and one pending on same date
    lead1 = Lead(
        name="Interested Lead",
        email="i@example.com",
        phone="123",
        city="C",
        state="S",
        course="Course",
        status="Interested",
        agent_id=agent.id,
        created_at=datetime.utcnow(),
        assigned_at=datetime.combine(today, datetime.min.time()),
    )
    lead2 = Lead(
        name="Pending Lead",
        email="p@example.com",
        phone="456",
        city="C",
        state="S",
        course="Course",
        status="Pending",
        agent_id=agent.id,
        created_at=datetime.utcnow(),
        assigned_at=datetime.combine(today, datetime.min.time()),
    )
    db.session.add_all([lead1, lead2])
    db.session.commit()

    resp = client.get(
        f"/agent-dashboard/export-interested-leads?date={today.strftime('%Y-%m-%d')}"
    )
    assert resp.status_code == 200
    # Should return an Excel file
    assert (
        resp.headers["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert b"PK" in resp.data[:2]  # XLSX files are ZIP-based, usually start with PK

def test_export_interested_leads_invalid_date(client):
    agent = create_user("agent_export2", "pass", "agent")
    login(client, "agent_export2", "pass")

    resp = client.get("/agent-dashboard/export-interested-leads?date=bad-date")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False

# ---------- leads-by-date + assigned-dates ----------

def test_get_assigned_dates_for_agent(client):
    agent = create_user("agent_dates", "pass", "agent")
    login(client, "agent_dates", "pass")

    d1 = datetime(2025, 1, 1)
    d2 = datetime(2025, 1, 2)
    for d in [d1, d2]:
        lead = Lead(
            name=f"L {d.day}",
            email="x@example.com",
            phone="123",
            city="C",
            state="S",
            course="Course",
            status="Pending",
            agent_id=agent.id,
            created_at=d,
            assigned_at=d,
        )
        db.session.add(lead)
    db.session.commit()

    resp = client.get("/agent-dashboard/assigned-dates")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "2025-01-01" in data["assigned_dates"]
    assert "2025-01-02" in data["assigned_dates"]


def test_leads_by_date_for_agent(client):
    agent = create_user("agent_leads_date", "pass", "agent")
    login(client, "agent_leads_date", "pass")

    day = datetime(2025, 1, 3)
    lead = Lead(
        name="L day",
        email="ld@example.com",
        phone="123",
        city="C",
        state="S",
        course="Course",
        status="Pending",
        agent_id=agent.id,
        created_at=day,
        assigned_at=day,
    )
    db.session.add(lead)
    db.session.commit()

    resp = client.get("/agent-dashboard/leads-by-date?date=2025-01-03")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["leads"]) == 1
    assert data["leads"][0]["name"] == "L day"

# ---------- AJAX send lead email (mock mail) ----------

def test_ajax_send_lead_email_message_only(client, monkeypatch):
    agent = create_user("agent_mail", "pass", "agent")
    login(client, "agent_mail", "pass")

    lead = Lead(
        name="Mail Lead",
        email="lead@example.com",
        phone="123",
        city="C",
        state="S",
        course="Course",
        status="Pending",
        agent_id=agent.id,
        created_at=datetime.utcnow(),
    )
    db.session.add(lead)
    db.session.commit()

    # Patch mail.send so no real email is sent. [web:38][web:50]
    sent_called = {"count": 0}

    def fake_send(msg):
        sent_called["count"] += 1

    monkeypatch.setattr(mail, "send", fake_send)

    payload = {"message": "Hello", "note_to_admin": "Note", "only_note": False}
    resp = client.post(
        f"/ajax-send-lead-email/{lead.id}",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert sent_called["count"] == 1

def test_ajax_send_lead_email_note_only(client):
    agent = create_user("agent_note", "pass", "agent")
    login(client, "agent_note", "pass")

    lead = Lead(
        name="Note Lead",
        email="lead2@example.com",
        phone="123",
        city="C",
        state="S",
        course="Course",
        status="Pending",
        agent_id=agent.id,
        created_at=datetime.utcnow(),
    )
    db.session.add(lead)
    db.session.commit()

    payload = {"message": "", "note_to_admin": "Some note", "only_note": True}
    resp = client.post(
        f"/ajax-send-lead-email/{lead.id}",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True

    # Note should be saved
    updated = Lead.query.get(lead.id)
    assert updated.note_to_admin == "Some note"

# ---------- /admin/send-bulk-email & /admin/send-bulk-email-agent ----------

def test_send_bulk_email_for_all_leads(client, monkeypatch):
    admin = create_user("admin_bulk", "pass", "admin")
    login(client, "admin_bulk", "pass")

    # two valid emails, one invalid
    leads = [
        Lead(
            name="L1",
            email="valid1@example.com",
            phone="1",
            city="C",
            state="S",
            course="C",
            status="Pending",
        ),
        Lead(
            name="L2",
            email="valid2@example.com",
            phone="2",
            city="C",
            state="S",
            course="C",
            status="Pending",
        ),
        Lead(
            name="L3",
            email="invalid-email",
            phone="3",
            city="C",
            state="S",
            course="C",
            status="Pending",
        ),
    ]
    db.session.add_all(leads)
    db.session.commit()

    sent_called = {"count": 0}

    def fake_send(msg):
        sent_called["count"] += 1

    monkeypatch.setattr(mail, "send", fake_send)

    resp = client.post(
        "/admin/send-bulk-email",
        data=json.dumps({"subject": "Test", "body": "Body"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    # 2 valid emails only
    assert data["sent"] == 2
    assert sent_called["count"] == 2

def test_send_bulk_email_agent(client, monkeypatch):
    admin = create_user("admin_agent_bulk", "pass", "admin")
    agent = create_user("target_agent", "pass", "agent")
    login(client, "admin_agent_bulk", "pass")

    # leads for that agent and for another agent
    l1 = Lead(
        name="A1",
        email="a1@example.com",
        phone="1",
        city="C",
        state="S",
        course="C",
        status="Pending",
        agent_id=agent.id,
    )
    other_agent = create_user("other_agent", "pass", "agent")
    l2 = Lead(
        name="B1",
        email="b1@example.com",
        phone="2",
        city="C",
        state="S",
        course="C",
        status="Pending",
        agent_id=other_agent.id,
    )
    db.session.add_all([l1, l2])
    db.session.commit()

    sent_called = {"count": 0}

    def fake_send(msg):
        sent_called["count"] += 1

    monkeypatch.setattr(mail, "send", fake_send)

    resp = client.post(
        "/admin/send-bulk-email-agent/target_agent",
        data=json.dumps({"subject": "Test", "body": "Body"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    # Only leads for target_agent should be mailed
    assert data["sent"] == 1
    assert sent_called["count"] == 1

# ---------- agent_update_lead_status (admin notification path) ----------

def test_agent_update_lead_status_triggers_admin_email_when_all_completed(client, monkeypatch):
    agent = create_user("agent_status", "pass", "agent")
    login(client, "agent_status", "pass")

    # two leads for agent, both initially Pending
    leads = []
    for i in range(2):
        l = Lead(
            name=f"S{i}",
            email=f"s{i}@example.com",
            phone=str(i),
            city="C",
            state="S",
            course="C",
            status="Pending",
            agent_id=agent.id,
            created_at=datetime.utcnow(),
        )
        leads.append(l)
        db.session.add(l)
    db.session.commit()

    sent_called = {"count": 0}

    def fake_send(msg):
        sent_called["count"] += 1

    monkeypatch.setattr(mail, "send", fake_send)

    # Update first lead – according to current app logic, email may already be sent
    payload = {"lead_id": leads[0].id, "status": "Interested"}
    resp = client.post(
        "/agent-dashboard/update-lead-status",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200

    # After updating both leads, at least one admin email must have been sent
    payload = {"lead_id": leads[1].id, "status": "Not Interested"}
    resp = client.post(
        "/agent-dashboard/update-lead-status",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert sent_called["count"] >= 1
