"""Rights-gated local newspaper PDF intake and purge. No Telegram or Gemini access.

For authorized files ONLY. This deliberately does NOT auto-upload PDFs anywhere.
A successful local purge is never evidence of Gemini/Drive remote deletion.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

from market_engine import save_json

NOW=lambda:dt.datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()


def file_sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as reader:
        for chunk in iter(lambda:reader.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def db_conn(db):
    db=Path(db)
    db.parent.mkdir(parents=True,exist_ok=True)
    connection=sqlite3.connect(db)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS jobs(
      sha256 TEXT PRIMARY KEY, publisher TEXT NOT NULL, source_reference TEXT NOT NULL,
      local_path TEXT NOT NULL, page_count INT, state TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL, purge_receipt TEXT,
      error TEXT, model_upload_id TEXT, temp_drive_file_id TEXT)""")
    connection.commit()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def check_pdf(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>50*1024*1024 or path.stat().st_size<32:
        raise ValueError("PDF missing or outside permitted per-file local size limits (50 MB)")
    with path.open("rb") as f:
        if f.read(5)!=b"%PDF-":raise ValueError("Not a PDF signature")
    try:
        from pypdf import PdfReader
        reader=PdfReader(str(path), strict=True)
        if reader.is_encrypted:raise ValueError("Protected PDF: do not bypass access controls")
        n=len(reader.pages)
    except ImportError:
        raise RuntimeError("pypdf required for validated page count; install locally from approved package repository")
    if not 1<=n<=1000:raise ValueError("Unsupported page count")
    return n


def register(path, *, db, publisher, source_reference, usage_permitted):
    if not usage_permitted:
        raise PermissionError("Rights gate failed: source not affirmatively approved for local text research")
    if not publisher or not source_reference:raise ValueError("Publisher and exact source reference are mandatory")
    pages=check_pdf(path)
    sha=file_sha256(path)
    with db_conn(db) as con:
        prior=con.execute("SELECT state FROM jobs WHERE sha256=?",(sha,)).fetchone()
        if prior:
            raise ValueError(f"Duplicate PDF sha256 already registered (state={prior[0]})")
        con.execute("INSERT INTO jobs(sha256,publisher,source_reference,local_path,page_count,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (sha,publisher,source_reference,str(Path(path).resolve()),pages,"DOWNLOADED",NOW(),NOW()))
        con.commit()
    return {"sha256":sha,"pages":pages,"state":"DOWNLOADED","note":"NOT read or validated, NOT uploaded"}


def validate_and_purge(*, db, sha256, extracted_json_file, durable_output):
    """Extraction JSON format: {sha256, pages:[{page_index:1, status:EXTRACTED/NO_RELEVANT_ARTICLES,
    facts:[{claim,source_page,source_url,verified_status}]}]}. Fully covered only.
    Will never purge on missing page coverage, verification or remote upload IDs.
    """
    payload=json.loads(Path(extracted_json_file).read_text(encoding="utf-8"))
    with db_conn(db) as con:
        rec=con.execute("SELECT local_path,page_count,state,model_upload_id,temp_drive_file_id FROM jobs WHERE sha256=?",(sha256,)).fetchone()
        if rec is None:raise KeyError("Unregistered hash")
        path,num_pages,state,model_id,drive_id=rec
        if state!="DOWNLOADED":raise ValueError(f"Unexpected job state {state}")
        if model_id or drive_id:
            raise PermissionError("Remote files recorded: purge blocked until specific remote deletion verified")
        if payload.get("sha256")!=sha256:raise ValueError("Extraction and registered file hash mismatch")
        pages=payload.get("pages")
        if not isinstance(pages,list) or len(pages)!=num_pages:
            raise ValueError("Incomplete PDF page coverage; retain original for retry")
        indexes=[x.get("page_index") for x in pages]
        if sorted(indexes)!=list(range(1,num_pages+1)):
            raise ValueError("Duplicate/missing page index; retain original")
        facts=[]
        for page in pages:
            if page.get("status") not in ("EXTRACTED","NO_RELEVANT_ARTICLES"):
                raise ValueError("Unreadable or unvalidated page; retain for retry")
            if page["status"]=="NO_RELEVANT_ARTICLES" and page.get("facts"):
                raise ValueError("Contradictory page state")
            for f in page.get("facts",[]):
                if (f.get("source_page")!=page["page_index"] or not f.get("source_url")
                    or not f.get("claim") or f.get("verified_status")!="VERIFIED"):
                    raise ValueError("Unverified claim or missing evidence; retain for retry")
                facts.append(f)
        if not Path(path).is_file() or file_sha256(path)!=sha256:
            raise ValueError("Local file missing or modified")
        out={"sha256":sha256,"pages_checked":num_pages,"facts":facts,"validated_at_ist":NOW(),
             "verification_type":"provided structured source checks (not direct Gemini/ChatGPT PDF claim)",
             "source":"local licensed / authorized PDF", "source_reference":con.execute("SELECT source_reference FROM jobs WHERE sha256=?",(sha256,)).fetchone()[0]}
        dest=Path(durable_output)
        if dest.exists():raise FileExistsError("No overwrite of published facts file")
        save_json(dest,out)
        if not dest.is_file() or not json.loads(dest.read_text(encoding="utf-8")).get("sha256")==sha256:
            raise IOError("Published fact record could not be independently read back")
        # Mark durable publish before destructive local operation.
        con.execute("UPDATE jobs SET state='PUBLISHED',updated_at=? WHERE sha256=?",(NOW(),sha256));con.commit()
        os.unlink(path)
        if Path(path).exists():
            con.execute("UPDATE jobs SET state='PURGE_FAILED',error=?,updated_at=? WHERE sha256=?",("Local path still exists",NOW(),sha256));con.commit()
            raise IOError("Local purge not verified")
        receipt={"local_path_absent":True,"removed_at_ist":NOW(),"local_sha256":sha256,
                 "gemini_remote_deletion":"NOT APPLICABLE / NEVER UPLOADED",
                 "google_drive_remote_deletion":"NOT APPLICABLE / NEVER UPLOADED"}
        con.execute("UPDATE jobs SET state='PURGED',purge_receipt=?,updated_at=? WHERE sha256=?",
                    (json.dumps(receipt),NOW(),sha256));con.commit()
        return receipt


def overdue_jobs(db, max_age_hours=24):
    threshold=dt.datetime.now(ZoneInfo("Asia/Kolkata"))-dt.timedelta(hours=max_age_hours)
    with db_conn(db) as con:
        rows=con.execute("SELECT sha256,state,created_at,updated_at FROM jobs WHERE state!='PURGED'").fetchall()
    return [{"sha256":r[0],"state":r[1],"updated_at":r[3]} for r in rows
            if dt.datetime.fromisoformat(r[2])<threshold]
