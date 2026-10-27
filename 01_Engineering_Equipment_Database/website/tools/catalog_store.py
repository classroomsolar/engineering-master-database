"""Lossless, disposable SQLite read model over the released equipment catalog.

The release JS and XLSX files remain authoritative. No engineering values are
calculated, units converted, formulas evaluated, or identities merged here.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

DEFAULT_DIST = Path(__file__).resolve().parents[1] / 'dist'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    path = (root / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(root):
        raise ValueError(f'Path escapes source directory: {relative}')
    return path


def new_output_path(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('Output must be outside the source directory and its ancestors')
    if output.exists():
        raise FileExistsError(f'Refusing to replace existing output: {output}')
    if not output.parent.is_dir():
        raise ValueError(f'Output parent does not exist: {output.parent}')
    return output


def load_assignment(path, variable):
    text = Path(path).read_text(encoding='utf-8')
    prefix = 'window.' + variable + '='
    if not text.startswith(prefix) or not text.rstrip().endswith(';'):
        raise ValueError(f'Invalid assignment wrapper: {path}')
    return json.loads(text[len(prefix):].strip()[:-1])


def decode_payload(root, relative, prefix):
    path = safe_path(root, relative)
    text = path.read_text(encoding='utf-8')
    if not text.startswith(prefix) or not text.endswith(');\n'):
        raise ValueError(f'Invalid payload wrapper: {relative}')
    data = json.loads(text[len(prefix):-3])
    if isinstance(data, str):
        data = json.loads(gzip.decompress(base64.b64decode(data, validate=True)))
    if not isinstance(data, dict):
        raise ValueError(f'Invalid payload object: {relative}')
    return data


def check_file(root, descriptor, file_key='file', hash_key='sha256', bytes_key='bytes'):
    path = safe_path(root, descriptor[file_key])
    if digest(path) != descriptor[hash_key]:
        raise ValueError(f'File hash mismatch: {descriptor[file_key]}')
    if bytes_key in descriptor and path.stat().st_size != descriptor[bytes_key]:
        raise ValueError(f'File size mismatch: {descriptor[file_key]}')
    return path


def load_catalog(source):
    catalog = load_assignment(Path(source)/'data/catalog.js', 'DB_CATALOG')
    ids, names = set(), set()
    for sheet in catalog['sheets']:
        if sheet['id'] in ids or sheet['name'] in names:
            raise ValueError('Duplicate source sheet identity')
        ids.add(sheet['id']); names.add(sheet['name'])
        if len(sheet['headers']) != sheet['colCount']:
            raise ValueError(f'Header count mismatch: {sheet["name"]}')
        for chunk in sheet['chunks']:
            check_file(source, chunk)
        if 'file' in sheet:
            check_file(source, sheet)
    for sheet in catalog['sheets']:
        for dep in sheet.get('dependencies', []):
            if isinstance(dep, str) and dep not in names and dep not in ids:
                raise ValueError(f'Unknown source dependency: {dep}')
    return catalog


def source_rows(source, sheet, include_header=False):
    seen=set(); count=cells=formulas=0; header_seen=sheet['headerRow'] is None
    for index, chunk in enumerate(sheet['chunks']):
        payload=decode_payload(source,chunk['file'],f'window.DBReceive({json.dumps(sheet["id"])},{index},')
        for row in payload['rows']:
            if not isinstance(row,list) or len(row)!=6:
                raise ValueError(f'Invalid source row shape: {sheet["name"]}')
            rn, values, types, styles, formula_map, stored = row
            if not isinstance(rn,int) or rn<1 or rn in seen:
                raise ValueError(f'Duplicate/invalid source row: {sheet["name"]}:{rn}')
            seen.add(rn)
            if not (len(values)==len(types)==len(styles)==sheet['colCount']):
                raise ValueError(f'Invalid source column count: {sheet["name"]}:{rn}')
            if len(stored)!=len(set(stored)) or any(not isinstance(c,int) or not 0<=c<len(values) for c in stored):
                raise ValueError(f'Invalid stored-cell indices: {sheet["name"]}:{rn}')
            if any(not str(c).isdigit() or int(c) not in stored for c in formula_map):
                raise ValueError(f'Formula without stored cell: {sheet["name"]}:{rn}')
            cells+=len(stored);formulas+=len(formula_map)
            if rn==sheet['headerRow']:
                header_seen=True
                if values != sheet['headers']:
                    raise ValueError(f'Source headers differ from catalog: {sheet["name"]}')
            else:count+=1
            if include_header or rn!=sheet['headerRow']:yield row
    if not header_seen or count!=sheet['rowCount'] or cells!=sheet['cellCount'] or formulas!=sheet['formulaCount']:
        raise ValueError(f'Source counts mismatch: {sheet["name"]}')


SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE source_files(path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, kind TEXT NOT NULL);
CREATE TABLE source_sheets(id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, metadata_json TEXT NOT NULL);
CREATE TABLE source_fields(sheet_id TEXT NOT NULL REFERENCES source_sheets(id), column_index INTEGER NOT NULL, header TEXT NOT NULL,
 PRIMARY KEY(sheet_id,column_index)) WITHOUT ROWID;
CREATE TABLE source_rows(sheet_id TEXT NOT NULL REFERENCES source_sheets(id), row_number INTEGER NOT NULL, is_header INTEGER NOT NULL,
 PRIMARY KEY(sheet_id,row_number)) WITHOUT ROWID;
CREATE TABLE source_cells(sheet_id TEXT NOT NULL, row_number INTEGER NOT NULL, column_index INTEGER NOT NULL,
 lexical_value TEXT, value_json TEXT NOT NULL, cell_type TEXT, style_id TEXT, formula_json TEXT,
 PRIMARY KEY(sheet_id,row_number,column_index),
 FOREIGN KEY(sheet_id,row_number) REFERENCES source_rows(sheet_id,row_number),
 FOREIGN KEY(sheet_id,column_index) REFERENCES source_fields(sheet_id,column_index)) WITHOUT ROWID;
CREATE TABLE categories(id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL);
CREATE TABLE profiles(id TEXT PRIMARY KEY, category_id TEXT NOT NULL REFERENCES categories(id), record_id TEXT NOT NULL,
 manufacturer TEXT NOT NULL, model TEXT NOT NULL, equipment_type TEXT NOT NULL, quality TEXT NOT NULL, review_required INTEGER NOT NULL,
 primary_sheet_id TEXT NOT NULL, primary_row_number INTEGER NOT NULL, profile_json TEXT NOT NULL,
 FOREIGN KEY(primary_sheet_id,primary_row_number) REFERENCES source_rows(sheet_id,row_number));
CREATE INDEX profiles_category ON profiles(category_id,manufacturer,model,id);
CREATE INDEX profiles_model ON profiles(manufacturer,model);
CREATE TABLE profile_sources(profile_id TEXT NOT NULL REFERENCES profiles(id), sheet_id TEXT NOT NULL, row_number INTEGER NOT NULL,
 relationship TEXT NOT NULL, relationship_state TEXT, link_row INTEGER, scope TEXT, identity_basis TEXT,
 PRIMARY KEY(profile_id,sheet_id,row_number,relationship),
 FOREIGN KEY(sheet_id,row_number) REFERENCES source_rows(sheet_id,row_number)) WITHOUT ROWID;
CREATE INDEX profile_sources_row ON profile_sources(sheet_id,row_number,profile_id);
CREATE TABLE profile_metrics(profile_id TEXT NOT NULL REFERENCES profiles(id), kind TEXT NOT NULL, lexical_value TEXT NOT NULL,
 unit TEXT NOT NULL, source_header TEXT NOT NULL, PRIMARY KEY(profile_id,kind)) WITHOUT ROWID;
CREATE TABLE profile_search(profile_id TEXT PRIMARY KEY REFERENCES profiles(id), text TEXT NOT NULL);
CREATE VIEW field_claims AS SELECT ps.profile_id, ps.relationship, ps.relationship_state, ps.scope, ps.identity_basis,
 sc.sheet_id, ss.name AS sheet_name, sc.row_number, sc.column_index, sf.header,
 sc.lexical_value, sc.value_json, sc.cell_type, sc.style_id, sc.formula_json
 FROM profile_sources ps JOIN source_cells sc ON sc.sheet_id=ps.sheet_id AND sc.row_number=ps.row_number
 JOIN source_fields sf ON sf.sheet_id=sc.sheet_id AND sf.column_index=sc.column_index
 JOIN source_sheets ss ON ss.id=sc.sheet_id;
'''


def build_database(source, output, collections_dir=None):
    source=Path(source).resolve(); output=new_output_path(source,output)
    collection_root=Path(collections_dir).resolve() if collections_dir else source
    if collection_root!=source and output.is_relative_to(collection_root):
        raise ValueError('Output must not overwrite collection inputs')
    catalog=load_catalog(source)
    sheet_headers={sheet['id']:sheet['headers'] for sheet in catalog['sheets']}
    index=load_assignment(collection_root/'collections/index.js','EQUIPMENT_CATALOG')
    fd,temporary=tempfile.mkstemp(prefix='.'+output.name+'.',suffix='.tmp',dir=output.parent);os.close(fd)
    db=None
    try:
        db=sqlite3.connect(temporary)
        db.executescript(SCHEMA)
        db.execute('INSERT INTO metadata VALUES (?,?)',('source',json.dumps(catalog['source'])))
        db.execute('INSERT INTO metadata VALUES (?,?)',('schema_version','1'))
        paths={'data/catalog.js': 'catalog'}
        totals=dict(sheets=0,rows=0,cells=0,formulas=0,profiles=0,sources=0)
        for sheet in catalog['sheets']:
            sid=sheet['id'];totals['sheets']+=1
            db.execute('INSERT INTO source_sheets VALUES (?,?,?)',(sid,sheet['name'],json.dumps(sheet,ensure_ascii=False)))
            db.executemany('INSERT INTO source_fields VALUES (?,?,?)',((sid,i,h) for i,h in enumerate(sheet['headers'])))
            for chunk in sheet['chunks']:paths[chunk['file']]='raw'
            if 'file' in sheet:paths[sheet['file']]='spreadsheet'
            for rn,values,types,styles,formula_map,stored in source_rows(source,sheet,True):
                is_header=rn==sheet['headerRow'];totals['rows']+=not is_header
                db.execute('INSERT INTO source_rows VALUES (?,?,?)',(sid,rn,int(is_header)))
                db.executemany('INSERT INTO source_cells VALUES (?,?,?,?,?,?,?,?)',
                    ((sid,rn,c,values[c] if isinstance(values[c],str) or values[c] is None else str(values[c]),
                      json.dumps(values[c],ensure_ascii=False),types[c],styles[c],
                      json.dumps(formula_map[str(c)],ensure_ascii=False) if str(c) in formula_map else None) for c in stored))
                totals['cells']+=len(stored);totals['formulas']+=len(formula_map)
        for relative,kind in paths.items():
            path=safe_path(source,relative)
            db.execute('INSERT INTO source_files VALUES (?,?,?,?)',(relative,digest(path),path.stat().st_size,kind))
        for key,value in [('sheets',totals['sheets']),('cells',totals['cells']),('formulas',totals['formulas']),('rowsExcludingTableHeaders',totals['rows'])]:
            if catalog['totals'][key]!=value:raise ValueError(f'Catalog total mismatch: {key}')
        try:
            db.execute('CREATE VIRTUAL TABLE profiles_fts USING fts5(profile_id UNINDEXED, text, tokenize="unicode61")')
            fts=True
        except sqlite3.OperationalError:
            fts=False
        for category in index['collections']:
            cid=category['id'];check_file(collection_root,category)
            check_file(collection_root,category,'searchFile','searchSha256','searchBytes')
            records=decode_payload(collection_root,category['file'],f'window.CollectionReceive({json.dumps(cid)},')['records']
            texts=decode_payload(collection_root,category['searchFile'],f'window.SearchReceive({json.dumps(cid)},')['search']
            if len(records)!=category['count'] or len(texts)!=len(records):raise ValueError(f'Collection count mismatch: {cid}')
            db.execute('INSERT INTO categories VALUES (?,?)',(cid,json.dumps(category,ensure_ascii=False)))
            for p,text in zip(records,texts):
                if len(p)!=16 or len(p[11])!=2:raise ValueError(f'Invalid profile shape: {cid}')
                if tuple(p[11]) not in {tuple(r[:2]) for r in p[10]}:raise ValueError(f'Missing primary source: {p[0]}')
                db.execute('INSERT INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?,?)',(p[0],cid,p[1],p[2],p[3],p[4],p[7],int(p[8]),*p[11],json.dumps(p,ensure_ascii=False)))
                for ref in p[10]:
                    if len(ref)!=7:raise ValueError(f'Invalid reference shape: {p[0]}')
                    db.execute('INSERT INTO profile_sources VALUES (?,?,?,?,?,?,?,?)',(p[0],*ref))
                    totals['sources']+=1
                native_sources={tuple(ref[:2]) for ref in p[10] if ref[2] in {'confirmed','candidate','candidate configuration'}}
                candidate_sources={tuple(ref[:2]) for ref in p[10] if ref[2] in {'candidate','candidate configuration'}}
                if p[12]!=len(native_sources) or p[13]!=len(candidate_sources):
                    raise ValueError(f'Invalid registry/candidate listing count: {p[0]}')
                for kind,metric in [('rating',p[5]),('voltage',p[6])]:
                    if len(metric)!=3:raise ValueError(f'Invalid metric shape: {p[0]}')
                    if metric[2]:
                        headers=sheet_headers[p[11][0]]
                        if metric[2] not in headers:
                            raise ValueError(f'Metric source header missing: {p[0]} / {metric[2]}')
                        # Use the first exact header occurrence, matching the released reader.
                        # Compare the original JSON value without numeric coercion/rounding.
                        cell=db.execute('SELECT value_json FROM source_cells WHERE sheet_id=? AND row_number=? AND column_index=?',
                                        (*p[11],headers.index(metric[2]))).fetchone()
                        if cell is None or json.loads(cell[0])!=metric[0]:
                            raise ValueError(f'Metric source value mismatch: {p[0]} / {metric[2]}')
                    db.execute('INSERT INTO profile_metrics VALUES (?,?,?,?,?)',(p[0],kind,*metric))
                db.execute('INSERT INTO profile_search VALUES (?,?)',(p[0],text))
                if fts:db.execute('INSERT INTO profiles_fts VALUES (?,?)',(p[0],text))
                totals['profiles']+=1
        if totals['profiles']!=index['catalogRecords']:raise ValueError('Profile total mismatch')
        if db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Foreign key check failed')
        totals['fts5']=fts
        db.execute('INSERT INTO metadata VALUES (?,?)',('counts',json.dumps(totals)))
        db.commit()
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity check failed')
        db.close();db=None
        # Atomic no-clobber publication. Existing output can never be replaced.
        os.link(temporary,output)
        return totals
    except sqlite3.IntegrityError as exc:
        raise ValueError(f'Data relationship/schema constraint failed: {exc}') from exc
    finally:
        if db is not None:db.close()
        Path(temporary).unlink(missing_ok=True)


def connect_readonly(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def search_profiles(db, query='', category=None, limit=50, offset=0):
    # FTS treats NUL as a terminator even inside quoted literal text.
    query=query.replace(chr(0),' ')
    limit=max(1,min(int(limit),500));offset=max(0,int(offset))
    where=[];params=[];join=''
    if category:where.append('p.category_id=?');params.append(category)
    if query.strip():
        has_fts=db.execute("SELECT 1 FROM sqlite_master WHERE name='profiles_fts'").fetchone()
        if has_fts:
            # Literal terms protect users from FTS syntax and punctuation errors.
            terms=query.split();match=' AND '.join('"'+word.replace('"','""')+'"' for word in terms)
            where.append('p.id IN (SELECT profile_id FROM profiles_fts WHERE profiles_fts MATCH ?)');params.append(match)
        else:
            join=' JOIN profile_search s ON s.profile_id=p.id'
            for word in query.casefold().split():
                where.append("instr(lower(s.text),?)>0");params.append(word)
    sql='SELECT p.id,p.record_id,p.category_id,p.manufacturer,p.model,p.equipment_type,p.quality,p.review_required FROM profiles p'+join
    if where:sql+=' WHERE '+' AND '.join(where)
    sql+=' ORDER BY p.category_id,p.manufacturer,p.model,p.id LIMIT ? OFFSET ?'
    return [dict(row) for row in db.execute(sql,(*params,limit,offset))]


def profile_detail(db, profile_id):
    row=db.execute('SELECT * FROM profiles WHERE id=?',(profile_id,)).fetchone()
    if row is None:return None
    result=dict(row);result['profile']=json.loads(result.pop('profile_json'))
    result['sources']=[dict(r) for r in db.execute('SELECT ps.*,ss.name AS sheet_name FROM profile_sources ps JOIN source_sheets ss ON ss.id=ps.sheet_id WHERE profile_id=? ORDER BY sheet_id,row_number,relationship',(profile_id,))]
    result['metrics']=[dict(r) for r in db.execute('SELECT * FROM profile_metrics WHERE profile_id=? ORDER BY kind',(profile_id,))]
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('build');build.add_argument('--source-dist',type=Path,default=DEFAULT_DIST);build.add_argument('--collections-dist',type=Path);build.add_argument('--output',type=Path,required=True)
    search=sub.add_parser('search');search.add_argument('--database',type=Path,required=True);search.add_argument('--query',default='');search.add_argument('--category');search.add_argument('--limit',type=int,default=50);search.add_argument('--offset',type=int,default=0)
    detail=sub.add_parser('profile');detail.add_argument('--database',type=Path,required=True);detail.add_argument('id')
    args=parser.parse_args(argv)
    try:
        if args.command=='build':result=build_database(args.source_dist,args.output,args.collections_dist)
        else:
            with connect_readonly(args.database) as db:
                result=search_profiles(db,args.query,args.category,args.limit,args.offset) if args.command=='search' else profile_detail(db,args.id)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,sqlite3.Error) as exc:
        parser.exit(1,f'{exc}\n')


if __name__=='__main__':raise SystemExit(main())
