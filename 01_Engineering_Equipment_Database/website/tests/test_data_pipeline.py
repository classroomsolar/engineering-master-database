"""Regression tests for lossless derived data and safe offline tooling."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))


def write_wrapper(path, prefix, payload, compressed=False):
    data = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    if compressed:
        data = json.dumps(base64.b64encode(gzip.compress(data.encode(), mtime=0)).decode())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prefix + data + (');\n' if compressed or 'Receive(' in prefix else ';\n'))
    return {'file': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(root):
    root.mkdir()
    headers = ['Record ID', 'Model', 'Voltage (V)', 'Verification Status']
    rows = [[1, headers, ['inlineStr'] * 4, [None] * 4, {}, list(range(4))],
            [2, ['A', 'Same name', '1.2300', 'UNVERIFIED'], ['inlineStr', 'inlineStr', None, 'inlineStr'],
             [None, None, '2', None], {'2': {'text': '1.2+0.03', 'attrs': {}}}, list(range(4))],
            [3, ['B', 'Same name', None, 'REVIEW_REQUIRED'], ['inlineStr', 'inlineStr', None, 'inlineStr'],
             [None] * 4, {}, [0, 1, 3]]]
    chunk = write_wrapper(root/'data/s1.js', 'window.DBReceive("s1",0,', {'rows': rows}, True)
    chunk['file'] = 'data/s1.js'
    sheet = dict(id='s1', name='EQUIPMENT', headers=headers, headerRow=1, rowCount=2,
                 colCount=4, cellCount=11, formulaCount=1, chunks=[chunk], dependencies=[])
    catalog = dict(source={'sha256': 'fixture'}, sheets=[sheet],
                   totals={'sheets': 1, 'cells': 11, 'formulas': 1, 'rowsExcludingTableHeaders': 2})
    write_wrapper(root/'data/catalog.js', 'window.DB_CATALOG=', catalog)
    profiles = []
    for ident, rn in [('A', 2), ('B', 3)]:
        profiles.append(['EQUIPMENT:'+ident, ident, '', 'Same name', 'Equipment',
                         ['', '', ''], ['', '', ''], 'UNVERIFIED', False, [],
                         [['s1', rn, 'primary', '', 0, '', '']], ['s1', rn], 0, 0, '', ''])
    desc = write_wrapper(root/'collections/items.js', 'window.CollectionReceive("items",', {'records': profiles}, True)
    desc['file'] = 'collections/items.js'
    search = write_wrapper(root/'collections/items.search.js', 'window.SearchReceive("items",', {'search':['a same name unverified', 'b same name review_required']}, True)
    desc.update(id='items', count=2, searchFile='collections/items.search.js', searchSha256=search['sha256'])
    write_wrapper(root/'collections/index.js', 'window.EQUIPMENT_CATALOG=', {'collections':[desc], 'catalogRecords':2})
    return rows


class PipelineTests(unittest.TestCase):
    def test_importing_tools_does_not_build_or_verify(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');(root/'tools').mkdir()
            for name in ['build_collections', 'verify_collections']:
                shutil.copy(TOOLS/(name+'.py'),root/'tools')
                result = subprocess.run([sys.executable, '-c', 'import '+name], cwd=root/'tools',
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, '')

    def test_builder_requires_an_explicit_new_output(self):
        with tempfile.TemporaryDirectory() as td:
            script=Path(td)/'tools/build_collections.py';script.parent.mkdir()
            shutil.copy(TOOLS/'build_collections.py',script);fixture(Path(td)/'dist')
            result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('--output-dir', result.stderr)

    def test_lossless_cells_and_distinct_ids_are_queryable(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); original = fixture(root/'dist'); target=root/'catalog.sqlite'
            summary=store.build_database(root/'dist', target)
            self.assertEqual(summary['profiles'], 2)
            with store.connect_readonly(target) as db:
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
                row=db.execute('SELECT lexical_value, formula_json, style_id FROM source_cells WHERE sheet_id=? AND row_number=2 AND column_index=2', ('s1',)).fetchone()
                self.assertEqual(row['lexical_value'], '1.2300')
                self.assertEqual(json.loads(row['formula_json']), original[1][4]['2'])
                self.assertEqual(row['style_id'], '2')
                self.assertEqual(len(store.search_profiles(db, 'Same name')), 2)
                self.assertEqual(store.profile_detail(db, 'EQUIPMENT:A')['sources'][0]['row_number'], 2)
                self.assertEqual(db.execute('SELECT count(*) FROM field_claims').fetchone()[0], 7)
            with self.assertRaises(FileExistsError):store.build_database(root/'dist', target)

    def test_corruption_and_missing_references_never_publish_database(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');target=root/'catalog.sqlite'
            chunk=root/'dist/data/s1.js';chunk.write_text(chunk.read_text()+'corrupt')
            with self.assertRaises(ValueError):store.build_database(root/'dist',target)
            self.assertFalse(target.exists())

    def test_builder_preserves_existing_output_and_publishes_no_failed_build(self):
        import build_collections as builder
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');existing=root/'existing';existing.mkdir()
            marker=existing/'important.txt';marker.write_text('keep')
            with self.assertRaises(FileExistsError):builder.build(root/'dist',existing)
            self.assertEqual(marker.read_text(),'keep')
            with self.assertRaises(KeyError):builder.build(root/'dist',root/'failed')
            self.assertFalse((root/'failed').exists())
            self.assertEqual(sorted(p.name for p in root.iterdir()),['dist','existing'])

    def test_missing_source_relationship_never_publishes_database(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');target=root/'catalog.sqlite'
            index=store.load_assignment(root/'dist/collections/index.js','EQUIPMENT_CATALOG')
            desc=index['collections'][0]
            payload=store.decode_payload(root/'dist',desc['file'],'window.CollectionReceive("items",')
            payload['records'][0][10][0][1]=999
            payload['records'][0][11][1]=999
            updated=write_wrapper(root/'dist/collections/items.js','window.CollectionReceive("items",',payload,True)
            desc['sha256']=updated['sha256'];desc['bytes']=updated['bytes']
            write_wrapper(root/'dist/collections/index.js','window.EQUIPMENT_CATALOG=',index)
            with self.assertRaisesRegex(ValueError,'constraint failed'):
                store.build_database(root/'dist',target)
            self.assertEqual(sorted(p.name for p in root.iterdir()),['dist'])

    def test_metric_binding_rejects_rehashed_inconsistent_claims(self):
        import catalog_store as store
        for metric in [['999', 'V', 'Voltage (V)'],
                       ['1.23', 'V', 'Voltage (V)'],
                       ['1.2300', 'V', 'Missing source header']]:
            with self.subTest(metric=metric), tempfile.TemporaryDirectory() as td:
                root=Path(td);fixture(root/'dist');target=root/'catalog.sqlite'
                index=store.load_assignment(root/'dist/collections/index.js','EQUIPMENT_CATALOG')
                desc=index['collections'][0]
                payload=store.decode_payload(root/'dist',desc['file'],'window.CollectionReceive("items",')
                payload['records'][0][6]=metric
                updated=write_wrapper(root/'dist/collections/items.js','window.CollectionReceive("items",',payload,True)
                desc['sha256']=updated['sha256'];desc['bytes']=updated['bytes']
                write_wrapper(root/'dist/collections/index.js','window.EQUIPMENT_CATALOG=',index)
                with self.assertRaisesRegex(ValueError,'Metric source'):
                    store.build_database(root/'dist',target)
                self.assertEqual(sorted(p.name for p in root.iterdir()),['dist'])

    def test_metric_binding_retains_exact_valid_source_lexical(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');target=root/'catalog.sqlite'
            index=store.load_assignment(root/'dist/collections/index.js','EQUIPMENT_CATALOG')
            desc=index['collections'][0]
            payload=store.decode_payload(root/'dist',desc['file'],'window.CollectionReceive("items",')
            payload['records'][0][6]=['1.2300','V','Voltage (V)']
            updated=write_wrapper(root/'dist/collections/items.js','window.CollectionReceive("items",',payload,True)
            desc['sha256']=updated['sha256'];desc['bytes']=updated['bytes']
            write_wrapper(root/'dist/collections/index.js','window.EQUIPMENT_CATALOG=',index)
            store.build_database(root/'dist',target)
            with store.connect_readonly(target) as db:
                self.assertEqual(db.execute("SELECT lexical_value FROM profile_metrics WHERE profile_id='EQUIPMENT:A' AND kind='voltage'").fetchone()[0],'1.2300')

    def test_registry_counts_reject_rehashed_inconsistent_relationships(self):
        import catalog_store as store
        for count_index in [12,13]:
            with self.subTest(count_index=count_index), tempfile.TemporaryDirectory() as td:
                root=Path(td);fixture(root/'dist');target=root/'catalog.sqlite'
                index=store.load_assignment(root/'dist/collections/index.js','EQUIPMENT_CATALOG')
                desc=index['collections'][0]
                payload=store.decode_payload(root/'dist',desc['file'],'window.CollectionReceive("items",')
                payload['records'][0][count_index]=1
                updated=write_wrapper(root/'dist/collections/items.js','window.CollectionReceive("items",',payload,True)
                desc['sha256']=updated['sha256'];desc['bytes']=updated['bytes']
                write_wrapper(root/'dist/collections/index.js','window.EQUIPMENT_CATALOG=',index)
                with self.assertRaisesRegex(ValueError,'listing count'):
                    store.build_database(root/'dist',target)
                self.assertEqual(sorted(p.name for p in root.iterdir()),['dist'])

    def test_source_schema_rejects_duplicate_rows(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rows=fixture(root/'dist')
            catalog=store.load_assignment(root/'dist/data/catalog.js','DB_CATALOG')
            rows.append(rows[1])
            write_wrapper(root/'dist/data/s1.js','window.DBReceive("s1",0,',{'rows':rows},True)
            with self.assertRaisesRegex(ValueError,'Duplicate/invalid source row'):
                list(store.source_rows(root/'dist',catalog['sheets'][0]))

    def test_sql_query_is_readonly_and_handles_literal_punctuation(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');store.build_database(root/'dist',root/'data.sqlite')
            with store.connect_readonly(root/'data.sqlite') as db:
                self.assertEqual(store.search_profiles(db, '" OR *'),[])
                self.assertEqual(store.search_profiles(db, 'same name',category='missing'),[])
                self.assertEqual(len(store.search_profiles(db, 'same name',limit=1,offset=1)),1)
                with self.assertRaises(sqlite3.OperationalError):db.execute('DELETE FROM profiles')

    def test_search_normalizes_embedded_nul_as_whitespace(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist');store.build_database(root/'dist',root/'data.sqlite')
            with store.connect_readonly(root/'data.sqlite') as db:
                expected=store.search_profiles(db,'Same name')
                self.assertEqual(store.search_profiles(db,'Same'+chr(0)+'name'),expected)
                self.assertEqual(len(store.search_profiles(db,chr(0))),2)

    def test_headerless_reference_sheet_retains_every_row(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist')
            catalog=store.load_assignment(root/'dist/data/catalog.js','DB_CATALOG')
            sheet=catalog['sheets'][0];sheet['headerRow']=None;sheet['rowCount']=3
            sheet['headers']=['A','B','C','D']
            self.assertEqual(len(list(store.source_rows(root/'dist',sheet))),3)

    def test_paths_cannot_escape_source_or_overwrite_inputs(self):
        import catalog_store as store
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixture(root/'dist')
            for path in ['../outside', '/etc/passwd', 'data/../../outside']:
                with self.assertRaises(ValueError):store.safe_path(root/'dist',path)
            with self.assertRaises(ValueError):store.build_database(root/'dist',root/'dist/derived.sqlite')


if __name__ == '__main__':unittest.main()
