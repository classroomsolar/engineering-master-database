"""Build equipment-based views over the unchanged v13 source records."""
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal,InvalidOperation
import json,gzip,base64,hashlib,re,sys,copy

def _build(source_dist, output_dir):
 DIST=Path(source_dist).resolve();OUTPUT=Path(output_dir);OUT=OUTPUT/"collections";OUT.mkdir(parents=True)
 (OUTPUT/"verification").mkdir()
 from catalog_store import load_catalog, source_rows
 original_catalog=load_catalog(DIST)
 meta={m["name"]:m for m in original_catalog["sheets"]};by_sid={m["id"]:m for m in original_catalog["sheets"]}
 def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 original_hashes={str(p.relative_to(DIST)):digest(p) for base in [DIST/"data",DIST/"spreadsheets"] for p in base.glob("*") if p.is_file()}
 def data(name):
  return list(source_rows(DIST,meta[name]))
 def vals(name):return [(r[0],r[1]) for r in data(name)]
 def field(name,v,*headers):
  h=meta[name]["headers"]
  for key in headers:
   if key in h:
    x=v[h.index(key)]
    if x is not None and x!="":return x
  return ""
 def norm(x):return (x or "").strip()
 def numeric(x):
  try:return Decimal(str(x))
  except (InvalidOperation,ValueError,TypeError):return None
 def exact_model(m,k):return (norm(m),norm(k))
 def unit_value(v,u):return (v+" "+u).strip() if v else ""
 def pick_metric(n,v,choices):
  for header,unit in choices:
   x=field(n,v,header)
   if x:return [x,unit,header]
  return ["","",""]
 def make_id(n,v,row):
  x=field(n,v,"Record ID","Cable ID","IBR ID","Registry Record ID","Equipment ID","Material ID")
  return x or n+":"+str(row)
 collections={
  "pv-modules":("PV modules","solar","Solar & storage","PV modules from every source, in one list."),
  "inverters":("Inverters","inverter","Solar & storage","Solar, battery and hybrid inverter records together."),
  "energy-storage":("Batteries & storage","battery","Solar & storage","Battery modules, storage systems and their configurations."),
  "optimizers":("Power optimizers","optimizer","Solar & storage","Module-level power electronics and original ratings."),
  "meters":("Meters","meter","Solar & storage","Meter models and integrated-meter configurations."),
  "ev-charging":("EV charging","charging","Solar & storage","Bidirectional vehicle charging equipment."),
  "cables":("Cables","cable","Power & distribution","Cable records with their original specifications and normalization data."),
  "conductors":("Conductors","conductor","Power & distribution","Transmission conductor records and source dimensions."),
  "transformers":("Transformers","transformer","Power & distribution","Power and instrument transformers, grouped by type."),
  "motors":("Motors","motor","Power & distribution","Motor nameplates, performance models and overload protection."),
  "generators":("Generators","generator","Power & distribution","Generator model and family records."),
  "switchgear":("Switchgear","switchgear","Power & distribution","Switchgear ratings and original qualification notes."),
  "disconnects":("Disconnect switches","disconnect","Power & distribution","Manual and controlled disconnecting equipment."),
  "breakers":("Circuit breakers","breaker","Protection & control","HV, LV, trip-unit and lug records in one collection."),
  "fuses":("Fuses","fuse","Protection & control","Fuse families, ratings and source configurations."),
  "relays":("Relays","relay","Protection & control","Protection relays, functions and model records."),
  "reclosers":("Reclosers","recloser","Protection & control","Recloser equipment and catalog configurations."),
  "controllers":("Controllers","controller","Protection & control","Electronic controllers and standalone power-control gateways."),
  "controlled-switching":("Controlled switching","switching","Protection & control","Controlled-switching device records."),
  "surge-protection":("Surge arresters","surge","Protection & control","Surge arrester ratings and application qualifications."),
  "grounding":("Grounding equipment","ground","Protection & control","Ground electrodes and neutral grounding resistors."),
  "rectifiers":("Rectifiers","rectifier","Power & distribution","Rectifier model and rating records."),
  "cable-trays":("Cable trays","tray","Installation & hardware","Cable trays, fittings and tray equipment."),
  "cable-cleats":("Cable cleats","cleat","Installation & hardware","Cleat families, sizes and published test conditions."),
  "conduits":("Conduits","conduit","Installation & hardware","Conduit dimensions and source references."),
  "enclosures":("Enclosures & vaults","enclosure","Installation & hardware","Enclosure, vault and related structural records."),
  "terminations":("Cable terminations","termination","Installation & hardware","Terminations, connectors and cable accessories."),
  "fire-protection":("Fire protection","fire","Installation & hardware","Fire-protection materials and configurations."),
  "parts":("Parts & accessories","parts","Installation & hardware","General parts and catalog records.")
 }
 TABLES={
  "PV_MODULES":("pv-modules","PV module"),"IBR":("inverters","Inverter"),
  "BATTERIES":("energy-storage","Battery"),"PV_OPTIMIZERS":("optimizers","Power optimizer"),
  "CABLES":("cables","Power cable"),"TRANSMISSION_CONDUCTORS":("conductors","Transmission conductor"),
  "TRANSFORMERS":("transformers","Power transformer"),"INSTRUMENT_TRANSFORMERS":("transformers","Instrument transformer"),
  "MOTORS_NAMEPLATE":("motors","Motor"),"MOTOR_MODELS":("motors","Performance model"),"OVERLOAD_HEATERS":("motors","Overload heater"),
  "GENERATORS":("generators","Generator"),"SWITCHGEAR":("switchgear","Switchgear"),"DISCONNECTS":("disconnects","Disconnect switch"),
  "HV_BREAKERS":("breakers","HV breaker"),"HV_BREAKERS_EXTENDED":("breakers","HV catalog variant"),"LV_BREAKERS":("breakers","LV breaker"),"TRIP_DEVICES":("breakers","Trip unit"),"BREAKER_LUGS":("breakers","Breaker lug"),
  "FUSES":("fuses","Fuse"),"RELAYS":("relays","Relay"),"RECLOSERS":("reclosers","Recloser"),
  "ELECTRONIC_CONTROLLERS":("controllers","Electronic controller"),"CSD_DEVICES":("controlled-switching","Controlled-switching device"),
  "SURGE_ARRESTERS":("surge-protection","Surge arrester"),"GROUND_ELECTRODES":("grounding","Ground electrode"),"NEUTRAL_GROUNDING_RESISTORS":("grounding","Neutral grounding resistor"),
  "RECTIFIERS":("rectifiers","Rectifier"),"CABLE_TRAYS":("cable-trays","Cable tray"),"CABLE_TRAY_EQUIPMENT":("cable-trays","Tray component"),
  "CABLE_CLEATS":("cable-cleats","Cable cleat"),"CABLE_CLEAT_SIZES":("cable-cleats","Cleat size"),
  "CONDUITS":("conduits","Conduit"),"ENCLOSURES":("enclosures","Enclosure / vault"),
  "TERMINATIONS":("terminations","Termination / connector"),"FIRE_PROTECTION":("fire-protection","Fire-protection configuration"),"CONDUIT_FIRE_PROTECTION":("fire-protection","Fire-protection configuration"),
  "PARTS_CATALOG":("parts","Part / accessory")
 }
 profiles={};primary_lookup={};byrow={};coverage=defaultdict(set);sampled=[];alias_count=0;attach_count=0;link_context={}
 def add_ref(p,n,row,kind="source",state="",link_row=0):
  key=(meta[n]["id"],row,kind)
  if key not in p["_refs"]:
   p["_refs"].add(key);p["refs"].append([meta[n]["id"],row,kind,state,link_row,*link_context.get(link_row,["",""])]);coverage[n].add(row)
 def append_search(p,v):
  p["search"]+="\n"+" ".join(x for x in v if x is not None and x!="")
 def display_fields(n,v):
  maker=field(n,v,"Manufacturer","MANUFACTURER","Manufacturer Source","Manufacturer Or Group","Manufacturer / Provider")
  model=field(n,v,"Model","MODEL","Description / Model","Series Model","Series / Model","Model / Family","Model Or Curve","Catalog / Model","Catalog / Pattern","Catalog","Part Number","Part #","Series","Description","Manufacturer / Model","Code","Heater Record","Model Id","Conduit Key","Part Description")
  if not maker and n in {"CABLE_CLEATS","CABLE_CLEAT_SIZES"}:maker=field(n,v,"Family")
  if not model:model=field(n,v,"Family","Material","Configuration") or "Record "+make_id(n,v,0)
  rating=pick_metric(n,v,[
  ("Nameplate Size (W)","W"),("CEC Rated Power (W)","W"),("Rated I/P DC POWER (IN WATTS)","W"),
  ("Capacity (Ah)","Ah"),("Rated MVA","MVA"),("Kva","kVA"),("Rated Current (A)","A"),
  ("Frame Or Size (A)","A"),("Continuous A","A"),("Rated / Frame A (Source)","A"),
  ("Current (A)","A"),("Rated Current A","A"),("Resistance Ω","Ω"),("MCOV kV RMS","kV MCOV"),
  ("Width in","in wide"),("Length ft","ft"),("Trade Size (in)","in trade size"),("Rated kW / HP","kW / HP"),
  ("Ampacity (A)","A"),("Power Rating",field(n,v,"Power Unit")),("Maximum Rating",field(n,v,"Maximum Rating Unit")),
  ("Rating Or Variant",""),("Curve Or Rating",""),("Primary Rating",""),("Nom Size","")])
  voltage=pick_metric(n,v,[("Max System (Vdc)","Vdc"),("Terminal kV","kV"),("Primary (kV)","kV"),("Voltage (kV)","kV"),("Rated Max (kV)","kV"),("Rated kV","kV"),("Rated System kV","kV"),("Rated (kV)","kV"),("Rated (kV)","kV"),("Rated kV (Source)","kV"),("Rated V / kV","(source)"),("Max Rated Voltage Source","(source)"),("Voltage Class","(source)"),("Header (V/cell)","V/cell"),("MAX. I/P VOLTAGE (VOLTS)","Vdc"),("System Voltage Class kV","kV")])
  quality=field(n,v,"Verification State","Verification Status","Data Status","Verification","Record Status","Use Status","Verification Tier")
  return maker,model,rating,voltage,quality
 def add_profile(n,row,v,category,typ):
  rid=make_id(n,v,row);uid=n+":"+rid
  assert uid not in profiles,uid
  m,k,pwr,volt,q=display_fields(n,v)
  p={"id":uid,"recordId":rid,"category":category,"type":typ,"manufacturer":m,"model":k,"rating":pwr,"voltage":volt,"quality":q,"review":False,"listStates":[],"refs":[],"primary":[meta[n]["id"],row],"search":"","registry":0,"candidate":0,"_refs":set()}
  profiles[uid]=p;primary_lookup[(n,rid)]=uid;byrow[(n,row)]=uid
  add_ref(p,n,row,"primary");append_search(p,v)
  return p
 # Only exact, same-schema specification duplicates are combined across equipment tables.
 signatures={}
 for n,(catid,typ) in TABLES.items():
  h=meta[n]["headers"];ignored={"Record ID","Source Dataset","Source Row"}
  for row,v in vals(n):
   p=add_profile(n,row,v,catid,typ)
   signature=(catid,typ,tuple((key,v[i]) for i,key in enumerate(h) if key not in ignored))
   if signature in signatures:
    dest=profiles[signatures[signature]];dest["refs"].extend(p["refs"]);dest["_refs"]|=p["_refs"];append_search(dest,v)
    primary_lookup[(n,p["recordId"])]=dest["id"];byrow[(n,row)]=dest["id"];del profiles[p["id"]];alias_count+=1
   else:signatures[signature]=p["id"]
 # Registry group identities already distinguish batteries, systems, metering and approval configurations.
 groups={};group_by_registry={}
 for row,v in vals("CEC_MODEL_GROUPS"):
  gid=v[0];n=v[7];rid=v[6];cat=v[1]
  if cat=="CEC_PMRS":continue
  cid={"CEC_BAT_ACTIVE":"energy-storage","CEC_BAT_ARCHIVE":"energy-storage","CEC_ESS":"energy-storage","CEC_METERS":"meters","CEC_PCS_LEGACY":"controllers","CEC_PCS":"controllers","CEC_V2G":"ev-charging"}[cat]
  typ={"CEC_BAT_ACTIVE":"Battery","CEC_BAT_ARCHIVE":"Battery (archived)","CEC_ESS":"Energy storage system","CEC_METERS":"Meter","CEC_PCS_LEGACY":"Control configuration","CEC_PCS":"Control configuration","CEC_V2G":"Bidirectional EV charger"}[cat]
  p=add_profile("CEC_MODEL_GROUPS",row,v,cid,typ)
  p["recordId"]=gid;p["manufacturer"]=v[3] or "";p["model"]=v[4] or "";p["listStates"]=(v[5] or "").split(";")
  p["rating"]=["","",""];p["voltage"]=["","",""];p["quality"]="";p["_groupCategory"]=cat
  p["_groupPrimary"]=rid;p["_nativePrimaryTable"]=n
  groups[gid]=p["id"]
  for reg in re.split(r";\s*",v[8] or ""):
   if reg:group_by_registry[reg]=p["id"]
  primary_lookup[("CEC_MODEL_GROUPS",gid)]=p["id"]
 links={};link_rows={}
 for row,v in vals("CEC_LISTING_LINKS"):
  links[v[0]]=v;link_rows[v[0]]=row;link_context[row]=[v[6] or "",v[5] or ""]
 # Original native tables remain untouched; each listing is attached to an equipment identity.
 native_names=[n for n in meta if n.startswith("CEC_") and n not in {"CEC_FIELD_MAP","CEC_SOURCE_NOTES","CEC_IMPORT_INDEX","CEC_LISTING_LINKS","CEC_MODEL_GROUPS","CEC_ASSEMBLY_RELATIONS","CEC_FILE_RECONCILIATION"}]
 native_assignments={};unmatched=[]
 for n in native_names:
  if n in {"CEC_PMRS","CEC_PMRS_HISTORICAL"}:continue
  for row,v in vals(n):
   reg=v[0];link=links[reg];dest=[]
   if link[2]:
    uid=primary_lookup.get((link[1],link[2]))
    if uid:dest=[uid]
   else:
    candidates=[x.strip() for x in re.split(r";",link[3] or "") if x.strip()]
    dest=list(dict.fromkeys(primary_lookup[(link[1],x)] for x in candidates if (link[1],x) in primary_lookup))
   if not dest:unmatched.append([n,row,reg,link]);continue
   state="confirmed" if link[2] else "candidate"
   native_assignments[reg]=dest[:]
   for uid in dest:
    p=profiles[uid];add_ref(p,n,row,state,link[4],link_rows[reg]);append_search(p,v)
    p["registry"]+=1;p["candidate"]+=state=="candidate"
    if state=="candidate":p["review"]=True
    if v[1] and v[1] not in p["listStates"]:p["listStates"].append(v[1])
    if reg==p.get("_groupPrimary"):
     p["primary"]=[meta[n]["id"],row]
     p["manufacturer"]=field(n,v,"Manufacturer Name","Manufacturer") or p["manufacturer"]
     p["model"]=field(n,v,"Model Number","Model Number1","Model") or p["model"]
     p["rating"]=pick_metric(n,v,[("Nameplate Energy Capacity | (kWh)","kWh"),("Nameplate Power | (kW)","kW"),("Maximum Continuous Output Power at Unity Power Factor | (kW)","kW"),("Maximum Continuous Power | (kVA)","kVA"),("Maximum Continuous Operating Power Rating (Controlled) | (kW)","kW"),("Maximum Discharge Power | (KW)","kW")])
     p["voltage"]=pick_metric(n,v,[("Nominal Voltage | (Vac)","Vac"),("Output Voltage | (V)","V"),("Rated Operating Voltage(s) | (volts)","V"),("Nominal Voitage | (VAC)","Vac")])
     if n in {"CEC_LEGACY_PCS","CEC_POWER_CONTROL"}:
      product=field(n,v,"Type of Equipment2 | Inverter or ESS","End-product in which PCS is Integrated").strip().casefold()
      if "inverter" in product or product=="acpv":p["category"]="inverters";p["type"]="Inverter control configuration"
      elif product=="ess" or "energy storage" in product:p["category"]="energy-storage";p["type"]="Storage control configuration"
      else:p["category"]="controllers";p["type"]="Power-control gateway / configuration"
 assert not unmatched,unmatched[:5]
 # Link a control approval to its uniquely identified literal manufacturer/model and voltage.
 # Multiple control approvals for a model retain all original parameter sets.
 def volts(p):
  value,unit,_=p["voltage"];d=numeric(value)
  if d is None:return None
  if unit=="kV":return d*1000
  if unit in {"V","Vac","Vdc"}:return d
  return None
 base_models=defaultdict(list)
 for p in profiles.values():
  if p.get("_groupCategory") in {"CEC_PCS","CEC_PCS_LEGACY"}:continue
  if p["manufacturer"] and p["model"]:base_models[(p["category"],*exact_model(p["manufacturer"],p["model"]))].append(p["id"])
 redirects={};control_model_groups={}
 for p in list(profiles.values()):
  if p.get("_groupCategory") not in {"CEC_PCS","CEC_PCS_LEGACY"}:continue
  key=(p["category"],*exact_model(p["manufacturer"],p["model"]))
  cand=base_models.get(key,[])
  pv=volts(p)
  if pv is not None:cand=[u for u in cand if volts(profiles[u]) is None or volts(profiles[u])==pv]
  if len(cand)==1:
   dest=profiles[cand[0]];redirects[p["id"]]=[dest["id"]]
   voltage_confirmed=pv is not None and volts(dest) is not None and pv==volts(dest)
   for ref in p["refs"]:
    new=ref[:]
    if not voltage_confirmed:new[2]="candidate configuration"
    if tuple(new[:3]) not in dest["_refs"]:dest["refs"].append(new);dest["_refs"].add(tuple(new[:3]))
   dest["search"]+="\n"+p["search"];dest["registry"]+=p["registry"];dest["candidate"]+=p["candidate"]
   if not voltage_confirmed:dest["review"]=True
   dest["listStates"]=list(dict.fromkeys(dest["listStates"]+p["listStates"]));del profiles[p["id"]];attach_count+=1
  elif len(cand)>1:
   # Do not choose one storage/voltage variant without proof.
   redirects[p["id"]]=cand[:]
   for uid in cand:
    dest=profiles[uid]
    for ref in p["refs"]:
     new=ref[:];new[2]="candidate configuration"
     if tuple(new[:3]) not in dest["_refs"]:dest["refs"].append(new);dest["_refs"].add(tuple(new[:3]))
    dest["search"]+="\n"+p["search"];dest["candidate"]+=p["registry"];dest["review"]=True
   del profiles[p["id"]];attach_count+=1
  else:
   # Same literal product model/voltage: multiple approval configurations, one profile.
   ck=(key,str(pv) if pv is not None else repr(p["voltage"][:2]),p["type"])
   if ck in control_model_groups:
    dest=profiles[control_model_groups[ck]];redirects[p["id"]]=[dest["id"]]
    dest["refs"].extend(p["refs"]);dest["_refs"]|=p["_refs"];dest["search"]+="\n"+p["search"];dest["registry"]+=p["registry"]
    dest["listStates"]=list(dict.fromkeys(dest["listStates"]+p["listStates"]))
    if dest["rating"]!=p["rating"]:dest["rating"]=["Multiple source configurations","",""]
    del profiles[p["id"]];attach_count+=1
   else:control_model_groups[ck]=p["id"]
 # Auxiliary reviews and calculated data are available with their equipment record.
 aux_counts=Counter();unlinked_aux=Counter()
 for n,idcol,primary in [("PV_UNIT_REVIEW","Record ID","PV_MODULES"),("OPTIMIZER_REVIEW","Record ID","PV_OPTIMIZERS"),("RECORD_RECONCILIATION","Record ID",None)]:
  for row,v in vals(n):
   rid=field(n,v,idcol);table=primary or field(n,v,"Equipment Table")
   uid=primary_lookup.get((table,rid));uid=redirects.get(uid,[uid])[0] if uid else None
   if uid in profiles:
    p=profiles[uid];add_ref(p,n,row,"review");append_search(p,v);aux_counts[n]+=1
    if n=="PV_UNIT_REVIEW":
     p["quality"]=field(n,v,"Audit State");p["gate"]=field(n,v,"Selection Gate")
     if any(x in p["quality"] for x in ["REVIEW_REQUIRED","IDENTITY_REVIEW"]):p["review"]=True
   else:unlinked_aux[n]+=1
 for row,v in vals("CABLE_NORMALIZATION"):
  try:uid=byrow.get(("CABLES",int(field("CABLE_NORMALIZATION",v,"Source Row"))))
  except (TypeError,ValueError):uid=None
  if uid in profiles:
   p=profiles[uid];add_ref(p,"CABLE_NORMALIZATION",row,"normalization");append_search(p,v);aux_counts["CABLE_NORMALIZATION"]+=1
  else:unlinked_aux["CABLE_NORMALIZATION"]+=1
 # Battery performance keys describe the exact source battery configuration.
 battery_keys=defaultdict(list)
 for row,v in vals("BATTERIES"):
  key=tuple(field("BATTERIES",v,h) for h in ["Chemistry","Manufacturer","Model","Plate Or Unit Count","Capacity (Ah)"])
  uid=byrow[("BATTERIES",row)]
  if uid in profiles:battery_keys[key].append(uid)
 for row,v in vals("BATTERY_PERFORMANCE"):
  key=tuple(field("BATTERY_PERFORMANCE",v,h) for h in ["Chemistry","Manufacturer","Model","Plate Or Unit Count","Capacity (Ah)"])
  dest=battery_keys.get(key,[])
  for uid in dest:
   p=profiles[uid];add_ref(p,"BATTERY_PERFORMANCE",row,"performance");append_search(p,v);aux_counts["BATTERY_PERFORMANCE"]+=1
  if not dest:unlinked_aux["BATTERY_PERFORMANCE"]+=1
 motor_keys=defaultdict(list)
 for row,v in vals("MOTOR_MODELS"):
  motor_keys[(field("MOTOR_MODELS",v,"Design Class"),field("MOTOR_MODELS",v,"Model Id"))].append(byrow[("MOTOR_MODELS",row)])
 for row,v in vals("MOTOR_CHARACTERISTICS"):
  for uid in motor_keys.get((field("MOTOR_CHARACTERISTICS",v,"Design Class"),field("MOTOR_CHARACTERISTICS",v,"Model Id")),[]):
   p=profiles[uid];add_ref(p,"MOTOR_CHARACTERISTICS",row,"performance");append_search(p,v);aux_counts["MOTOR_CHARACTERISTICS"]+=1
 # Check and keep the original native registry rows, including unresolved identity candidates.
 def expand(uid):
  if uid in profiles:return [uid]
  return list(dict.fromkeys(x for z in redirects.get(uid,[]) for x in expand(z)))
 for reg,dest in native_assignments.items():
  expanded=list(dict.fromkeys(x for uid in dest for x in expand(uid)))
  assert expanded,(reg,dest)
  native_assignments[reg]=expanded
 # Every source sheet remains accessible as original supporting data, under functional headings.
 REF_GROUPS={
  "Cable engineering":["CABLE_TYPES","CONDUCTOR_MATERIALS","CONDUCTOR_SIZES","CABLE_SC_K_FACTORS","INSULATION_CLASSES","AMPACITY_ROUTES","AMPACITY_AMBIENT_FACTORS","AMPACITY_CCC_FACTORS","AMPACITY_PARAMETERS","NEC_AMPACITY_2020","NEC_AMPACITY_2023","CABLE_FAULT_CURRENT_REFERENCE","CABLE_PLANNING_DEFAULTS","CABLE_IMPEDANCE_DEFAULTS","CONDUCTOR_PROPERTIES","LEGACY_NEC_REFERENCE"],
  "Tray & grounding rules":["BOX_FILL","TRAY_EXPANSION_RULES","CABLE_CLEAT_SIZE_MAP","TRAY_ACCESSORY_RULES","NEC_TRAY_FILL","NEC_CHANNEL_TRAY_FILL","TRAY_ENGINEERING_DEFAULTS","TRAY_EGC_METAL_AREA","EGC_SIZE_BY_OCPD","EGC_SIZE_THRESHOLDS","TRAY_EGC_AREA_THRESHOLDS","TRAY_WIDTH_CODES","TRAY_BARRIER_COVER_CODES","TRAY_GROUNDING_ACCESSORIES"],
  "Performance & protection":["BATTERY_PERFORMANCE","MOTOR_CHARACTERISTICS","MOTOR_LOCKED_ROTOR_CODES","PROTECTION_CURVES","HARMONICS","RAILWAY_LOADS"],
  "Reliability & costs":["RELIABILITY","RELIABILITY_EXTENDED","INTERRUPTION_COST"],
  "Monitoring providers":["CEC_PMRS","CEC_PMRS_HISTORICAL"],
  "Sources & research":["SOURCE_REGISTER","RESEARCH_GUIDANCE","MODEL_REQUIREMENTS","PAPER_AUDIT"],
  "Data quality & history":["SHEET_MAP","FIELD_AUDIT","DATA_ISSUES","PLUGIN_LOG","CHANGE_LOG","AUDIT_README","DATABASE_TABLE_INDEX","CALCULATOR_KEY_AUDIT","NUMERIC_BENCHMARKS","REQUEST_AUDIT","EQUIPMENT_RECORD_HISTORY","RECORD_RECONCILIATION","CEC_FIELD_MAP","CEC_SOURCE_NOTES","CEC_IMPORT_INDEX","CEC_LISTING_LINKS","CEC_MODEL_GROUPS","CEC_ASSEMBLY_RELATIONS","CEC_FILE_RECONCILIATION","PV_UNIT_REVIEW","OPTIMIZER_REVIEW","CABLE_NORMALIZATION"]
 }
 ref_items=[]
 for group,names in REF_GROUPS.items():
  for n in names:
   if n in meta:
    ref_items.append({"id":meta[n]["id"],"group":group,"name":n,"label":n.replace("CEC_","").replace("_"," ").lower().capitalize(),"rows":meta[n]["rowCount"]})
 # Serialize compact browsable profiles. Raw values and source files are not rewritten.
 collection_meta=[]
 for cid,(label,icon,family,description) in collections.items():
  records=[p for p in profiles.values() if p["category"]==cid]
  assert records,cid
  packed=[];search_text=[]
  for p in records:
   p["refs"].sort(key=lambda r:(0 if r[:2]==p["primary"] else 1,r[0],r[1]))
   p["registry"]=len({(r[0],r[1]) for r in p["refs"] if r[2] in {"confirmed","candidate","candidate configuration"}})
   p["candidate"]=len({(r[0],r[1]) for r in p["refs"] if r[2] in {"candidate","candidate configuration"}})
   search_text.append(p["search"].lower())
   packed.append([p["id"],p["recordId"],p["manufacturer"],p["model"],p["type"],p["rating"],p["voltage"],p["quality"],p["review"],p["listStates"],p["refs"],p["primary"],p["registry"],p["candidate"],"",p.get("gate","")])
  payload=json.dumps({"records":packed},ensure_ascii=False,separators=(",",":")).encode()
  blob=base64.b64encode(gzip.compress(payload,compresslevel=6,mtime=0)).decode()
  f=OUT/(cid+".js");f.write_text("window.CollectionReceive("+json.dumps(cid)+","+json.dumps(blob)+");\n")
  sf=OUT/(cid+".search.js");sp=json.dumps({"search":search_text},ensure_ascii=False,separators=(",",":")).encode();sb=base64.b64encode(gzip.compress(sp,compresslevel=6,mtime=0)).decode();sf.write_text("window.SearchReceive("+json.dumps(cid)+","+json.dumps(sb)+");\n")
  collection_meta.append({"id":cid,"label":label,"icon":icon,"family":family,"description":description,"count":len(records),"manufacturers":len({r[2] for r in packed if r[2]}),"types":sorted({r[4] for r in packed}),"file":"collections/"+f.name,"bytes":f.stat().st_size,"sha256":digest(f),"sourceListings":len({(r[0],r[1]) for p in records for r in p["refs"] if r[2] in {"confirmed","candidate","candidate configuration"}})})
  collection_meta[-1].update({"searchFile":"collections/"+sf.name,"searchBytes":sf.stat().st_size,"searchSha256":digest(sf)})
 # Coverage: all raw source rows have a path through equipment records or supporting references.
 uncovered=[];reference_sids={r["id"] for r in ref_items}
 for n,m in meta.items():
  if m["id"] in reference_sids:continue
  rows={r[0] for r in data(n)}
  if not rows<=coverage[n]:uncovered.append({"table":n,"rows":sorted(rows-coverage[n])[:10]})
 assert not uncovered,uncovered
 for path,d in original_hashes.items():assert digest(DIST/path)==d,path
 index={"version":2,"collections":collection_meta,"references":ref_items,"original":original_catalog["source"],"sourceSheets":len(meta),"storedCells":original_catalog["totals"]["cells"],"originalFormulas":original_catalog["totals"]["formulas"],"catalogRecords":sum(c["count"] for c in collection_meta),"linkedNativeListings":len(native_assignments),"organization":"Equipment type, with original source claims attached to the equipment record.","recordSchema":["id","recordId","manufacturer","model","type","rating","voltage","quality","review","listStates","sources","primarySource","registryListingCount","candidateListingCount","searchText","selectionGate"]}
 (OUTPUT/"collections/index.js").write_text("window.EQUIPMENT_CATALOG="+json.dumps(index,ensure_ascii=False,separators=(",",":"))+";\n")
 report={"result":"PASS","source":original_catalog["source"],"collectionCount":len(collection_meta),"catalogRecords":index["catalogRecords"],"nativeEquipmentListingsLinked":len(native_assignments),"monitoringProviderListings":meta["CEC_PMRS"]["rowCount"]+meta["CEC_PMRS_HISTORICAL"]["rowCount"],"all55018RegistryMembershipsRetained":len(native_assignments)+meta["CEC_PMRS"]["rowCount"]+meta["CEC_PMRS_HISTORICAL"]["rowCount"]==55018,"primarySourcesUnchanged":len(original_hashes),"sourceBlobHashes":original_hashes,"exactSpecificationAliasesCombined":alias_count,"controlConfigurationProfilesAttachedOrGrouped":attach_count,"auxiliaryRowsLinked":dict(aux_counts),"auxiliaryRowsAvailableInReferences":dict(unlinked_aux),"unmatchedNativeEquipmentRows":unmatched,"uncoveredSourceRows":uncovered,"collections":[{k:c[k] for k in ["id","label","count","sourceListings","sha256"]} for c in collection_meta],"identityRules":["Original existing primary IDs and listing-link identities are retained.","Candidate manufacturer/variant links are attached with explicit review flags; they are not asserted as confirmed matches.","Standalone control configurations are grouped only by literal manufacturer/model/voltage and type. Original configuration values remain separately inspectable.","An approval configuration is attached to an equipment record only for a unique literal manufacturer/model identity with compatible declared voltage; multiple compatible variants retain candidate relationships.","Exact same-schema specification aliases retain all source rows.","Battery modules and integrated storage assemblies remain separate record types within the same storage collection.","All original 117 data blobs and all 117 XLSX downloads remain byte-for-byte unchanged."]}
 report["identityRedirects"]=redirects
 (OUTPUT/"verification/equipment_unification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
 return report


def build(source_dist, output_dir):
 from catalog_store import new_output_path
 import os,shutil,tempfile
 source_dist=Path(source_dist).resolve()
 output=new_output_path(source_dist,output_dir)
 staging=Path(tempfile.mkdtemp(prefix='.'+output.name+'.',dir=output.parent))
 try:
  report=_build(source_dist,staging/'release')
  # All writes and source validation finish before publication.
  # A nonempty existing directory cannot be overwritten by rename.
  if output.exists():raise FileExistsError(output)
  os.rename(staging/'release',output)
  return report
 finally:
  shutil.rmtree(staging)


def main(argv=None):
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source-dist',type=Path,default=ROOT/'dist')
 parser.add_argument('--output-dir',type=Path,required=True,help='New isolated directory; source dist is never rewritten')
 args=parser.parse_args(argv)
 try:
  report=build(args.source_dist,args.output_dir)
 except (ValueError,OSError,AssertionError,KeyError) as exc:
  parser.exit(1,str(exc)+'\n')
 print(json.dumps({k:report[k] for k in ['result','collectionCount','catalogRecords','nativeEquipmentListingsLinked','unmatchedNativeEquipmentRows','uncoveredSourceRows']}))
 return 0


ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':raise SystemExit(main())
