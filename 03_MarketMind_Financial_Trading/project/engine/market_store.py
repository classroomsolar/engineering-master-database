"""ACID NSE EOD archive store: authoritative immutable SQLite ledger.

All bars for an archive date and its SHA receipt commit in a single transaction.
Legacy CSVs are optional regenerable exports, *never* the source of truth.
"""
from __future__ import annotations
import csv
import datetime as dt
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from market_engine import KNOWN_ISINS

DB_NAME = 'nse_eod_immutable.sqlite3'
BAR_COLUMNS = ['date','symbol','isin','open','high','low','close','volume','series','exchange','source_type',
               'origin_confirmed','source_url','source_file_sha256','adjusted','corporate_actions_checked',
               'synthetic','session','source_date']

SCHEMA = '''
CREATE TABLE IF NOT EXISTS archive_receipts(
 trade_date TEXT PRIMARY KEY, sha256 TEXT NOT NULL, origin_provenance TEXT NOT NULL,
 origin_confirmed INTEGER NOT NULL CHECK(origin_confirmed IN (0,1)), source_url TEXT NOT NULL,
 rows_read INTEGER NOT NULL, matched_symbols INTEGER NOT NULL, missing_symbols_json TEXT NOT NULL,
 imported_at_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bars(
 trade_date TEXT NOT NULL, symbol TEXT NOT NULL, isin TEXT NOT NULL,
 open REAL NOT NULL CHECK(open>0),high REAL NOT NULL CHECK(high>0),
 low REAL NOT NULL CHECK(low>0),close REAL NOT NULL CHECK(close>0),
 volume INTEGER NOT NULL CHECK(volume>=0), source_sha256 TEXT NOT NULL,
 source_url TEXT NOT NULL, provenance TEXT NOT NULL, origin_confirmed INTEGER NOT NULL,
 PRIMARY KEY(trade_date,symbol),
 FOREIGN KEY(trade_date) REFERENCES archive_receipts(trade_date),
 CHECK(low <= open AND open <= high AND low <= close AND close <= high)
);
CREATE INDEX IF NOT EXISTS bars_by_symbol_date ON bars(symbol,trade_date);
'''


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path); db_path.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(db_path, timeout=20, isolation_level=None)
    cx.execute('PRAGMA foreign_keys=ON')
    cx.execute('PRAGMA busy_timeout=20000')
    cx.executescript(SCHEMA)
    return cx


@contextmanager
def managed_connection(db_path:Path):
    cx=connect(db_path)
    try: yield cx
    finally: cx.close()


def import_archive(data:dict, *, db_path:Path)->dict:
    """Import parsed NSE UDiFF record set atomically; idempotent identical SHA.

    Different SHA for an already saved date fails even if prices are identical;
    this is deliberate to avoid silently accepting revised/archive-tampered data.
    """
    date = data['date']; sha = data['source_sha256']; rows = data['bars']
    if not rows: raise ValueError('Archive contains no eligible holdings')
    if any(k != v['symbol'] or v['date'] != date or v['source_file_sha256'] != sha or
           KNOWN_ISINS.get(k) != v['isin'] for k,v in rows.items()):
        raise ValueError('Inconsistent parsed instrument identity, date or archive SHA')
    with managed_connection(Path(db_path)) as cx:
        try:
            cx.execute('BEGIN IMMEDIATE')
            prev = cx.execute('SELECT sha256 FROM archive_receipts WHERE trade_date=?',(date,)).fetchone()
            if prev:
                if prev[0] != sha:
                    raise ValueError(f'Immutable archive conflict for {date}; old SHA={prev[0]}, incoming={sha}')
                existing = cx.execute('SELECT symbol,isin,open,high,low,close,volume FROM bars WHERE trade_date=?',(date,)).fetchall()
                bysym = {x[0]:x for x in existing}
                if set(bysym) != set(rows):raise ValueError('Idempotent import has changed symbol coverage')
                for sym,bar in rows.items():
                    old = bysym[sym]
                    if old[1]!=bar['isin'] or any(abs(old[j]-bar[k])>0.000001 for j,k in enumerate(('open','high','low','close'),2)) or old[6]!=bar['volume']:
                        raise ValueError('Idempotent record mismatch despite matching archive SHA')
                cx.execute('COMMIT')
                return {'status':'ALREADY_IMPORTED','date':date,'matched_symbols':len(rows),'source_sha256':sha,
                        'origin_confirmed':bool(data['origin_confirmed'])}
            cx.execute('''INSERT INTO archive_receipts VALUES(?,?,?,?,?,?,?,?,?)''',
                (date,sha,data['origin_provenance'],int(data['origin_confirmed']),data['source_url'],
                 int(data['rows_read']),len(rows),json.dumps(data['missing_symbols']),
                 dt.datetime.now(dt.timezone.utc).isoformat()))
            for sym,bar in rows.items():
                cx.execute('''INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (date,sym,bar['isin'],bar['open'],bar['high'],bar['low'],bar['close'],
                   bar['volume'],sha,bar['source_url'],data['origin_provenance'],int(data['origin_confirmed'])))
            cx.execute('COMMIT')
            return {'status':'IMPORTED_RAW_UNADJUSTED','date':date,'matched_symbols':len(rows),
                    'source_sha256':sha,'origin_confirmed':bool(data['origin_confirmed'])}
        except BaseException:
            if cx.in_transaction:cx.execute('ROLLBACK')
            raise


def export_symbol(db_path:Path, symbol:str, output:Path)->dict:
    """Regenerate identical research-compatible CSV from authoritative DB.

    Exports are raw/unadjusted. No date is inferred; no adjustment invented.
    """
    if symbol not in KNOWN_ISINS:raise ValueError('Unknown symbol')
    with managed_connection(db_path) as cx:
        rows=cx.execute('''SELECT b.trade_date,b.symbol,b.isin,b.open,b.high,b.low,b.close,b.volume,
                          b.provenance,b.origin_confirmed,b.source_url,b.source_sha256
                          FROM bars b WHERE b.symbol=? ORDER BY b.trade_date''',(symbol,)).fetchall()
    if not rows:return {'symbol':symbol,'rows_exported':0,'status':'NO_DATA'}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_name(output.name+'.partial')
    with tmp.open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=BAR_COLUMNS);writer.writeheader()
        for date,sym,isin,op,hi,lo,close,volume,provenance,confirmed,url,sha in rows:
            writer.writerow({'date':date,'symbol':sym,'isin':isin,'open':op,'high':hi,'low':lo,
                             'close':close,'volume':volume,'series':'EQ','exchange':'NSE',
                             'source_type':provenance,'origin_confirmed':str(bool(confirmed)),
                             'source_url':url,'source_file_sha256':sha,'adjusted':'False',
                             'corporate_actions_checked':'False','synthetic':'False',
                             'session':'EOD_FINAL','source_date':date})
    tmp.replace(output)
    return {'symbol':symbol,'rows_exported':len(rows),'status':'RAW_EXPORT_ONLY',
            'adjusted':False,'output':str(output)}


def audit_store(db_path:Path, *, expected_symbols:tuple[str,...]|None=None)->dict:
    with managed_connection(db_path) as cx:
        archive_rows=cx.execute('SELECT trade_date,sha256,origin_confirmed,matched_symbols,missing_symbols_json FROM archive_receipts ORDER BY trade_date').fetchall()
        bar_rows=cx.execute('SELECT symbol,COUNT(*),MIN(trade_date),MAX(trade_date) FROM bars GROUP BY symbol ORDER BY symbol').fetchall()
        invalid=cx.execute('''SELECT COUNT(*) FROM bars b LEFT JOIN archive_receipts r ON b.trade_date=r.trade_date
                              WHERE r.trade_date IS NULL OR b.source_sha256!=r.sha256 OR b.origin_confirmed!=r.origin_confirmed''').fetchone()[0]
    covered={r[0]:{'bars':r[1],'first':r[2],'last':r[3]} for r in bar_rows}
    symbols=expected_symbols or tuple(KNOWN_ISINS)
    return {'storage':'SQLITE_TRANSACTIONAL_IMMUTABLE_RAW', 'archive_count':len(archive_rows),
            'bars_total':sum(r[1] for r in bar_rows),'by_symbol':covered,
            'missing_entire_symbols':sorted(set(symbols)-set(covered)),
            'all_archive_provenance_confirmed':all(bool(x[2]) for x in archive_rows) if archive_rows else False,
            'inconsistent_rows':invalid,
            'latest_archive_date':archive_rows[-1][0] if archive_rows else None,
            'archive_dates':[r[0] for r in archive_rows],
            'adjusted':False,'backtest_ready':False,'live_quotes':False}
