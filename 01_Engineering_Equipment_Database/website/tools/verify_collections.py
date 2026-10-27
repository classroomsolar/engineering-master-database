"""Independent checks of unified equipment views against immutable original records."""
from pathlib import Path
from collections import defaultdict,Counter
import json,gzip,base64,hashlib,subprocess,re,sys

def verify(source_dist, collections_dist=None, source_workbook=None):
 D=Path(source_dist).resolve(); C=Path(collections_dist).resolve() if collections_dist else D
 from catalog_store import load_catalog, source_rows as validated_rows, safe_path, load_assignment, check_file, digest
 raw=load_catalog(D)
 new=load_assignment(C/"collections/index.js","EQUIPMENT_CATALOG")
 meta={m["id"]:m for m in raw["sheets"]};names={m["name"]:m for m in raw["sheets"]}
 report=json.loads((C/"verification/equipment_unification.json").read_text())
 checks=Counter();errors=[]
 def ck(v,k,detail=""):
  checks[k]+=1
  if not v:errors.append({"check":k,"detail":detail})
 def decode(path,prefix):
  t=safe_path(D if str(path).startswith("data/") else C,path).read_text();assert t.startswith(prefix) and t.endswith(");\n"),path
  v=json.loads(t[len(prefix):-3])
  return json.loads(gzip.decompress(base64.b64decode(v))) if isinstance(v,str) else v
 def source_rows(m):
  return list(validated_rows(D,m))
 all_profiles={};owners=defaultdict(set);metric_bindings=defaultdict(list);ref_checks=defaultdict(list);source_scope=[];by_category={};primary_uids={}
 for c in new["collections"]:
  ck("cec" not in c["label"].lower(),"no_origin_category",c["label"])
  ck(hashlib.sha256(safe_path(C,c["file"]).read_bytes()).hexdigest()==c["sha256"],"collection_hash",c["id"])
  rows=decode(c["file"],f"window.CollectionReceive({json.dumps(c['id'])},")["records"]
  texts=decode(c["searchFile"],f"window.SearchReceive({json.dumps(c['id'])},")["search"]
  ck(hashlib.sha256(safe_path(C,c["searchFile"]).read_bytes()).hexdigest()==c["searchSha256"],"search_hash",c["id"])
  ck(len(rows)==c["count"]==len(texts),"collection_and_search_count",c["id"])
  by_category[c["id"]]=set()
  for r,search in zip(rows,texts):
   uid=r[0];ck(uid not in all_profiles,"unique_equipment_identity",uid);all_profiles[uid]=r;by_category[c["id"]].add(uid)
   ck(r[14]=="","deferred_full_specification_search",uid)
   ck(r[1].lower() in search or r[1] in search,"search_record_identity",uid)
   ck(r[2].lower() in search if r[2] else True,"search_manufacturer",uid)
   ck(r[3].lower() in search if not r[3].startswith("Record ") else True,"search_model",uid)
   ck(tuple(r[11]) in {tuple(v[:2]) for v in r[10]},"primary_source_available",uid)
   for metric in [r[5],r[6]]:
    if metric[2]:metric_bindings[r[11][0]].append((r[11][1],metric,uid))
   refs=set()
   for v in r[10]:
    ck(len(v)==7,"source_reference_shape",uid)
    ck(v[0] in meta,"source_sheet_exists",uid)
    ck(tuple(v[:3]) not in refs,"no_repeated_source_reference",uid)
    refs.add(tuple(v[:3]));ref_checks[v[0]].append((v[1],uid))
    owners[(v[0],v[1])].add(uid)
    if v[4]:source_scope.append((v[4],v[5],v[6],uid))
    if v[2].startswith("candidate"):ck(r[8] or r[13]>0,"candidate_relationship_visible",uid)
    if v[2]=="primary":primary_uids.setdefault((v[0],v[1]),set()).add(uid)
   ck(r[12]==len({tuple(v[:2]) for v in r[10] if v[2] in {"confirmed","candidate","candidate configuration"}}),"native_source_count",uid)
   ck(r[13]==len({tuple(v[:2]) for v in r[10] if v[2] in {"candidate","candidate configuration"}}),"candidate_count",uid)
 ck(len(by_category)==29,"all_equipment_categories")
 ck(len(all_profiles)==new["catalogRecords"],"catalog_total")
 native=[
 "CEC_PV_ACTIVE","CEC_PV_ARCHIVE","CEC_SOLAR_INVERTERS","CEC_BATTERY_INVERTERS","CEC_INVERTER_ARCHIVE","CEC_BATTERIES","CEC_BATTERY_ARCHIVE","CEC_ENERGY_STORAGE","CEC_METERS","CEC_LEGACY_PCS","CEC_POWER_CONTROL","CEC_V2G"]
 native_map={};original_links={};expected_primary={};volt_context={}
 for sid,m in meta.items():
  rows=source_rows(m);rowmap={r[0]:r for r in rows}
  for rn,uid in ref_checks[sid]:ck(rn in rowmap,"original_row_exists",uid+" / "+m["name"]+" row "+str(rn))
  for rn,metric,uid in metric_bindings[sid]:
   ck(metric[2] in m["headers"],"metric_header_exists",uid+" / "+metric[2])
   if metric[2] in m["headers"] and rn in rowmap:ck(rowmap[rn][1][m["headers"].index(metric[2])]==metric[0],"metric_value_exact",uid+" / "+metric[2])
  if m["name"] in native:
   for r in rows:
    reg=r[1][0];native_map[reg]=(sid,r[0],m["name"]);ck(bool(owners[(sid,r[0])]),"every_native_listing_visible",reg)
    targets=owners[(sid,r[0])]
    if m["name"] in {"CEC_PV_ACTIVE","CEC_PV_ARCHIVE"}:ck(targets<=by_category["pv-modules"],"pv_sources_in_pv_list",reg)
    if m["name"] in {"CEC_SOLAR_INVERTERS","CEC_BATTERY_INVERTERS","CEC_INVERTER_ARCHIVE"}:ck(targets<=by_category["inverters"],"inverter_sources_in_inverters_list",reg)
    if m["name"] in {"CEC_BATTERIES","CEC_BATTERY_ARCHIVE","CEC_ENERGY_STORAGE"}:ck(targets<=by_category["energy-storage"],"storage_sources_in_storage_list",reg)
    if m["name"]=="CEC_METERS":ck(targets<=by_category["meters"],"meters_in_one_list",reg)
    if m["name"] in {"CEC_LEGACY_PCS","CEC_POWER_CONTROL"}:
     h=m["headers"];key="Type of Equipment2 | Inverter or ESS" if m["name"]=="CEC_LEGACY_PCS" else "End-product in which PCS is Integrated";typ=(r[1][h.index(key)] or "").strip().lower()
     if "inverter" in typ or typ=="acpv":ck(targets<=by_category["inverters"],"inverter_control_claims_co_located",reg)
     elif typ=="ess" or "energy storage" in typ:ck(targets<=by_category["energy-storage"],"storage_control_claims_co_located",reg)
     else:ck(targets<=by_category["controllers"],"gateway_controls_co_located",reg)
  if m["name"]=="CEC_LISTING_LINKS":original_links={r[1][0]:(r[0],r[1]) for r in rows};linkrows={r[0]:r[1] for r in rows}
  if m["name"] in {"PV_MODULES","IBR"}:
   idindex=m["headers"].index("Record ID")
   expected_primary[m["name"]]={m["name"]+":"+r[1][idindex] for r in rows}
 for name,ids in expected_primary.items():
  cid="pv-modules" if name=="PV_MODULES" else "inverters";ck(ids<=by_category[cid],"all_existing_primary_equipment_retained",name)
 ck(len(by_category["pv-modules"])==39400,"pv_not_duplicated_by_source_lists")
 def expand(uid,seen=None):
  if uid in all_profiles:return {uid}
  seen=set() if seen is None else seen
  if uid in seen:return set()
  seen.add(uid)
  return set().union(*(expand(x,seen.copy()) for x in report["identityRedirects"].get(uid,[])))
 for reg,(sid,rn,table) in native_map.items():
  _,link=original_links[reg]
  parents=[link[2]] if link[2] else [v.strip() for v in (link[3] or "").split(";") if v.strip()]
  expected=set()
  for rid in parents:expected|=expand(link[1]+":"+rid)
  ck(owners[(sid,rn)]==expected,"original_listing_identity_links_retained",reg)
 for linkrow,scope,basis,uid in source_scope:
  v=linkrows[linkrow]
  ck(scope==(v[6] or "") and basis==(v[5] or ""),"original_scope_and_identity_basis_exact",uid)
 for path,expected_digest in report["sourceBlobHashes"].items():
  ck(hashlib.sha256(safe_path(D,path).read_bytes()).hexdigest()==expected_digest,"original_source_bytes_exact",path)
 # Compare immutable bytes with the actual tracked release paths, including staged changes.
 git=subprocess.run(["git","rev-parse","--show-toplevel"],cwd=D,capture_output=True,text=True)
 if git.returncode==0:
  git_root=Path(git.stdout.strip())
  paths=[str((D/p).relative_to(git_root)) for p in ["data","spreadsheets"]]
  p=subprocess.run(["git","diff","--exit-code","HEAD","--",*paths],cwd=git_root,capture_output=True)
  ck(p.returncode==0,"original_data_and_excel_unchanged_from_release")
 if source_workbook:
  ck(digest(source_workbook)==raw["source"]["sha256"],"original_workbook_sha256",str(source_workbook))
 ck(len(native_map)==54741,"all_native_equipment_rows")
 ck(len(native_map)+names["CEC_PMRS"]["rowCount"]+names["CEC_PMRS_HISTORICAL"]["rowCount"]==55018,"all_55018_registry_memberships_preserved")
 html=(D/"index.html").read_text()
 ck("CEC registry" not in html,"no_separate_registry_navigation")
 ck("collections/index.js" in html,"equipment_index_is_main_navigation")
 result={"result":"PASS" if not errors else "FAIL","checks":dict(checks),"totalChecks":sum(checks.values()),"failureCount":len(errors),"failures":errors,"equipmentCategories":29,"catalogRecords":len(all_profiles),"originalPVRecords":len(expected_primary["PV_MODULES"]),"originalInverterRecords":len(expected_primary["IBR"]),"nativeEquipmentListingsLinked":len(native_map),"allRegistryMembershipsRetained":55018,"originalSourceAndExcelFilesUnchanged":len(report["sourceBlobHashes"])}

 return result


def main(argv=None):
 import argparse,os,tempfile
 from catalog_store import new_output_path
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source-dist',type=Path,default=ROOT/'dist')
 parser.add_argument('--collections-dist',type=Path,help='Isolated build root containing collections/ and verification/')
 parser.add_argument('--source-workbook',type=Path,help='Original master workbook for SHA-256 verification')
 parser.add_argument('--report',type=Path,help='Optional NEW report path outside source; otherwise prints summary only')
 args=parser.parse_args(argv)
 try:
  output=new_output_path(args.source_dist,args.report) if args.report else None
  if output and args.collections_dist and output.is_relative_to(args.collections_dist.resolve()):
   raise ValueError('Report must be outside collection inputs')
  result=verify(args.source_dist,args.collections_dist,args.source_workbook)
  if output:
   fd,temp=tempfile.mkstemp(prefix='.'+output.name+'.',dir=output.parent)
   try:
    with os.fdopen(fd,'w') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    os.link(temp,output)
   finally:Path(temp).unlink(missing_ok=True)
 except (ValueError,OSError,AssertionError,KeyError) as exc:
  parser.exit(1,str(exc)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in {'checks','failures'}}))
 if result['failures']:print(json.dumps(result['failures'][:15],ensure_ascii=False))
 return 1 if result['failureCount'] else 0


ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':raise SystemExit(main())
