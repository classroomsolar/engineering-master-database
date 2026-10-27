"""NSE UDiFF cash-market EOD archive: guarded retrieval, strict ingestion and audit.

No broker execution, no scraped credentials, no assumption that raw OHLCV is adjusted.
NSE archive access may be restricted; manual authenticated exports are also accepted.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from market_engine import KNOWN_ISINS, save_json

ORIGIN = 'https://nsearchives.nseindia.com/content/cm/'
MAX_ARCHIVE_SIZE=15*1024*1024
MAX_CSV_SIZE=75*1024*1024
HEADERS = {'User-Agent':'Mozilla/5.0 (compatible; research archive download)', 'Accept':'application/zip,application/octet-stream,*/*', 'Referer':'https://www.nseindia.com/'}
ALIASES={
 'symbol': ['TckrSymb','SYMBOL','Symbol','TICKER','Ticker'],
 'series': ['SctySrs','SERIES','Series'],
 'isin': ['ISIN','ISINCode','ISIN_CD','Isin'],
 'date': ['TradDt','TRADE_DATE','DATE','BizDt'],
 'open': ['OpnPric','OPEN','OPEN_PRICE'],
 'high': ['HghPric','HIGH','HIGH_PRICE'],
 'low': ['LwPric','LOW','LOW_PRICE'],
 'close': ['ClsPric','CLOSE','CLOSE_PRICE'],
 'volume': ['TtlTradgVol','TOTTRDQTY','TOTTRDVOL','TOTAL_TRADING_VOLUME'],
}


def archive_name(day:dt.date)->str:
    return f'BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip'


def archive_url(day:dt.date)->str:
    return ORIGIN+archive_name(day)


def download_udiff(day:dt.date, output:Path)->dict:
    """Best effort: only official NSE archive domain, no fallback to third-party mirrors."""
    if day>dt.date.today(): raise ValueError('Future trading date rejected')
    url=archive_url(day)
    req=urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req,timeout=25) as res:
            if not res.geturl().startswith(ORIGIN):raise PermissionError('Unexpected download redirect')
            content=res.read(MAX_ARCHIVE_SIZE+1)
            if len(content)>MAX_ARCHIVE_SIZE:raise ValueError('Unexpectedly large NSE ZIP')
    except (urllib.error.URLError,TimeoutError) as ex:
        raise ConnectionError(f'Could not obtain official NSE archive; check NSE site or manually export {archive_name(day)}: {ex}') from ex
    if content[:4]!=b'PK\x03\x04':raise ValueError('Official source response was not a ZIP (possibly blocked / unavailable)')
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_name(output.name+'.partial')
    temp.write_bytes(content)
    temp.replace(output)
    receipt={'archive_date':day.isoformat(),'sha256':hashlib.sha256(content).hexdigest(),'download_url':url,'saved_to':str(output),'bytes':len(content),'provenance':'OFFICIAL_HTTPS_FETCH'}
    save_json(Path(str(output)+'.receipt.json'),receipt)
    return receipt


def parse_day(x:str)->dt.date:
    x=x.strip()
    for fmt in ('%Y-%m-%d','%d-%b-%Y','%d-%m-%Y','%d/%m/%Y','%Y%m%d'):
        try:return dt.datetime.strptime(x,fmt).date()
        except ValueError:pass
    raise ValueError(f'Unsupported trading-date format: {x!r}')


def pick_header(headers:list[str],key:str, *, optional=False)->str|None:
    choices={h.strip().casefold():h for h in headers if h}
    for alias in ALIASES[key]:
        if alias.casefold() in choices:return choices[alias.casefold()]
    if optional:return None
    raise ValueError(f'Missing NSE {key} column; found {headers}')


def extract_csv(path:Path)->tuple[bytes,str]:
    data=path.read_bytes()
    if path.suffix.lower()=='.zip':
        if len(data)>MAX_ARCHIVE_SIZE:raise ValueError('Archive too large')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members=[v for v in z.infolist() if v.filename.lower().endswith('.csv')]
            if len(members)!=1:raise ValueError('Expected exactly one CSV inside NSE UDiFF ZIP')
            info=members[0]
            if info.file_size>MAX_CSV_SIZE or info.compress_size>MAX_ARCHIVE_SIZE:raise ValueError('ZIP bomb guard: oversized CSV')
            if '/' in info.filename or '\\' in info.filename:raise ValueError('ZIP path traversal guard')
            with z.open(info) as stream:
                content=stream.read(MAX_CSV_SIZE+1)
            if len(content)>MAX_CSV_SIZE:raise ValueError('ZIP decompression limit exceeded')
            return content,hashlib.sha256(data).hexdigest()
    elif path.suffix.lower()=='.csv':
        if len(data)>MAX_CSV_SIZE:raise ValueError('CSV too large')
        return data,hashlib.sha256(data).hexdigest()
    else:raise ValueError('Only official NSE UDiFF CSV or ZIP accepted')


def ingest_udiff(source:Path, *, expected_day:dt.date, symbols:dict[str,str]|None=None)->dict:
    """Convert a single official NSE UDiFF archive to verified-date, RAW/UNADJUSTED bars.
    Date and symbol+ISIN matches are checked; close values never advertised live.
    """
    symbols=symbols or KNOWN_ISINS
    binary,sha=extract_csv(source)
    receipt_path=Path(str(source)+'.receipt.json')
    origin_confirmed=False
    provenance='USER_SUPPLIED_UNVERIFIED_ORIGIN'
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
        if receipt.get('sha256')!=sha or receipt.get('archive_date')!=expected_day.isoformat() or receipt.get('download_url')!=archive_url(expected_day):
            raise ValueError('File receipt mismatch: date, origin URL or checksum')
        if receipt.get('provenance') not in ('OFFICIAL_HTTPS_FETCH','MANUAL_OFFICIAL_EXPORT_ATTESTED'):
            raise ValueError('Unknown provenance receipt')
        origin_confirmed=True
        provenance=receipt['provenance']
    try:content=binary.decode('utf-8-sig')
    except UnicodeDecodeError:content=binary.decode('cp1252')
    rd=csv.DictReader(io.StringIO(content))
    if not rd.fieldnames:raise ValueError('CSV has no header')
    keys={k:pick_header(rd.fieldnames,k) for k in ALIASES}
    if keys['isin'] is None:raise ValueError('NSE ISIN column required for verified identity')
    records={}; count=0; distinct=set(); unknown=[]
    for row in rd:
        count+=1
        sym=(row.get(keys['symbol']) or '').strip().upper()
        if not sym:continue
        distinct.add(sym)
        if sym not in symbols:continue
        if (row.get(keys['series']) or '').strip().upper()!='EQ':continue
        isin=(row.get(keys['isin']) or '').strip().upper()
        if isin!=symbols[sym]:raise ValueError(f'Identity mismatch: {sym} ISIN {isin!r} vs approved {symbols[sym]}')
        day=parse_day(row[keys['date']]) if row.get(keys['date']) else (_ for _ in ()).throw(ValueError('Trading date missing from NSE row'))
        if day!=expected_day:raise ValueError(f'Unexpected date for {sym}: {day} != {expected_day}')
        try:
            px={k:float(str(row[keys[k]]).replace(',','').strip()) for k in ('open','high','low','close')}
            vol_float=float(str(row[keys['volume']]).replace(',','').strip())
            if not math.isfinite(vol_float) or not vol_float.is_integer():raise ValueError('Fractional/nonfinite traded volume')
            vol=int(vol_float)
        except (ValueError,TypeError) as e: raise ValueError(f'Invalid numeric fields for {sym}') from e
        if (not all(math.isfinite(v) and v>0 for v in px.values()) or vol<0
            or not px['low']<=min(px['open'],px['close'])<=max(px['open'],px['close'])<=px['high']):
            raise ValueError(f'Malformed price/volume for {sym}')
        if sym in records:raise ValueError(f'Duplicate EQ row for {sym} (possible ambiguous instruments)')
        records[sym]={'date':day.isoformat(),'symbol':sym,'isin':isin,**px,'volume':vol,
            'series':'EQ','exchange':'NSE','source_type':provenance,'origin_confirmed':origin_confirmed,
            'source_url':archive_url(day),'source_file_sha256':sha,'adjusted':False,
            'corporate_actions_checked':False,'synthetic':False,'session':'EOD_FINAL','source_date':day.isoformat()}
    if not count:raise ValueError('NSE file contains no rows')
    if not records:raise ValueError('None of the approved holdings was found in NSE EQ data')
    return {'date':expected_day.isoformat(),'source_path':str(source),'source_sha256':sha,
            'source_url':archive_url(expected_day),'origin_confirmed':origin_confirmed,'origin_provenance':provenance,'rows_read':count,'symbols_seen':len(distinct),
            'matched_symbols':len(records),'missing_symbols':sorted(set(symbols)-set(records)),
            'price_basis':'RAW/UNADJUSTED NSE EOD FINAL (NOT LIVE, NOT BACKTEST READY)',
            'bars':records}


def archive_import(path:Path,*,date:dt.date,store:Path)->dict:
    """Atomic multi-stock ingest to immutable SQLite, then regenerate raw CSV exports.

    SQLite commit precedes CSV export. If interrupted after commit, running again
    with identical archive SHA repairs missing materialized CSVs idempotently.
    """
    from market_store import DB_NAME,import_archive,export_symbol,audit_store
    data=ingest_udiff(path,expected_day=date)
    store.mkdir(parents=True,exist_ok=True)
    status=import_archive(data,db_path=store/DB_NAME)
    exports=[]
    for symbol in sorted(data['bars']):
        exports.append(export_symbol(store/DB_NAME,symbol,store/f'{symbol}.csv'))
    result={k:v for k,v in data.items() if k!='bars'}
    result.update({'raw_history_dir':str(store),'authoritative_db':str(store/DB_NAME),
                   'commit_status':status['status'],'csv_exports':exports,
                   'audit':audit_store(store/DB_NAME)})
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description='Official NSE UDiFF ingest (raw/unadjusted EOD only, no orders)')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('download');a.add_argument('--date',required=True);a.add_argument('--out',required=True)
    a=sub.add_parser('import');a.add_argument('--file',required=True);a.add_argument('--date',required=True);a.add_argument('--store',required=True)
    a=sub.add_parser('attest');a.add_argument('--file',required=True);a.add_argument('--date',required=True);a.add_argument('--reviewed-by',required=True);a.add_argument('--source-url',required=True)
    args=p.parse_args(argv)
    if args.command=='download':result=download_udiff(parse_day(args.date),Path(args.out))
    elif args.command=='import':result=archive_import(Path(args.file),date=parse_day(args.date),store=Path(args.store))
    else:
        day=parse_day(args.date)
        if args.source_url != archive_url(day):raise ValueError('Attested source must exactly match NSE official archive URL')
        if not args.reviewed_by.strip():raise ValueError('Human reviewer required')
        path=Path(args.file);_,sha=extract_csv(path)
        result={'archive_date':day.isoformat(),'sha256':sha,'download_url':args.source_url,'saved_to':str(path),'bytes':path.stat().st_size,'provenance':'MANUAL_OFFICIAL_EXPORT_ATTESTED','reviewed_by':args.reviewed_by,'reviewed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
        save_json(Path(str(path)+'.receipt.json'),result)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result
if __name__=='__main__': main()
