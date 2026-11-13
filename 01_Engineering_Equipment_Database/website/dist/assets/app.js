(() => {
"use strict";
const C=window.EQUIPMENT_CATALOG, RAW=window.DB_CATALOG, $=id=>document.getElementById(id);
if(!C||!RAW){$("loadingState").textContent="The catalog could not load. Please reload this page.";return;}
const fmt=n=>n.toLocaleString("en-US");
const metas=new Map(RAW.sheets.map(m=>[m.id,m]));
const byName=new Map(RAW.sheets.map(m=>[m.name,m]));
const I={id:0,rid:1,maker:2,model:3,type:4,rating:5,voltage:6,quality:7,review:8,states:9,refs:10,primary:11,registry:12,candidate:13,search:14,gate:15};
const S={meta:null,records:null,filtered:[],page:1,pageSize:50,query:"",maker:"",type:"",sort:null,dir:1,sequence:0,detailIndex:-1,view:"overview",detailToken:0,snapshot:null,focus:null,sourcePage:0,searchReady:false};
const RS={meta:null,rows:[],filtered:[],page:1,sequence:0};
const requests=new Map(),collectionRequests=new Map(),searchRequests=new Map(),searchInFlight=new Map();
let currentCollection=null,rawCache=null,rawWanted="",toastTimer,searchTimer;
const ICONS={
 solar:'<rect x="4" y="4" width="16" height="13" rx="1"/><path d="M9 4v13m6-13v13M4 10h16m-8 7v4m-4 0h8"/>',
 inverter:'<rect x="4" y="3" width="16" height="18" rx="3"/><path d="m13 6-4 7h5l-3 5M8 21v2m8-2v2"/>',
 battery:'<rect x="3" y="6" width="17" height="13" rx="2"/><path d="M20 10h2v5h-2M7 10v5m-2-3h4m4 0h4"/>',
 cable:'<path d="M5 3v5a7 7 0 0 0 14 0V3M3 3h4m10 0h4M12 15v7"/>',
 conductor:'<path d="M3 5h18M3 12h18M3 19h18"/><circle cx="8" cy="5" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="8" cy="19" r="2"/>',
 transformer:'<path d="M5 3v3m0 12v3m14-18v3m0 12v3M10 3v18m4-18v18M5 6c-5 0-5 4 0 4-5 0-5 4 0 4-5 0-5 4 0 4m14-12c5 0 5 4 0 4 5 0 5 4 0 4 5 0 5 4 0 4"/>',
 motor:'<circle cx="12" cy="12" r="8"/><path d="M2 12h2m16 0h2M9 15V9l3 4 3-4v6"/>',
 breaker:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="m9 15 6-6M9 3V1m6 20v2"/><circle cx="9" cy="15" r="1"/><circle cx="15" cy="9" r="1"/>',
 fuse:'<path d="M12 1v5m0 12v5"/><rect x="7" y="6" width="10" height="12" rx="1"/><path d="M12 6v12"/>',
 relay:'<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M7 6V3m5 3V3m5 3V3M7 19v3m5-3v3m5-3v3M8 13l3-3 4 5 2-2"/>',
 ground:'<path d="M12 2v11m-9 0h18M6 17h12m-8 4h4"/>',
 surge:'<path d="m13 2-8 12h6l-1 8 9-13h-7l1-7Z"/>',
 tray:'<path d="M3 4v14h18V4M7 18v-5m5 5v-5m5 5v-5M3 9h18"/>',
 cleat:'<path d="M4 20V8a8 8 0 0 1 16 0v12M2 20h20"/><circle cx="12" cy="9" r="4"/>',
 enclosure:'<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M15 3v18m-3-11v4"/>',
 meter:'<circle cx="12" cy="12" r="9"/><path d="M6 15a6 6 0 0 1 12 0m-6-3 4-4M9 18h6"/>',
 charging:'<rect x="4" y="2" width="12" height="19" rx="2"/><path d="M16 8h2l3 3v7a2 2 0 0 1-4 0v-5M7 5h6v5H7m1 5h4"/>',
 optimizer:'<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M7 9h4m-2-2v4m5 3h4M6 19v3m12-3v3"/>',
 parts:'<path d="m12 2 9 5v10l-9 5-9-5V7l9-5ZM3 7l9 5 9-5m-9 5v10"/>',
 default:'<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 8h8M8 12h8M8 16h5"/>'
};
function icon(name,size=18){return '<svg aria-hidden="true" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">'+(ICONS[name]||ICONS.default)+'</svg>';}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined&&text!==null)n.textContent=String(text);return n;}
function metric(a){return a&&a[0]?[a[0],a[1]].filter(Boolean).join(" "):"";}
function columnName(i){let n=i+1,s="";while(n){const k=(n-1)%26;s=String.fromCharCode(65+k)+s;n=Math.floor((n-1)/26);}return s;}
function toast(text){clearTimeout(toastTimer);$("toast").textContent=text;$("toast").hidden=false;toastTimer=setTimeout(()=>$("toast").hidden=true,3200);}
async function unpack(payload){if(typeof payload!=="string")return payload;if(typeof DecompressionStream==="undefined")throw new Error("Use a current browser to open the compressed catalog.");const bytes=Uint8Array.from(atob(payload),c=>c.charCodeAt(0));return JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).text());}
window.DBReceive=(id,i,data)=>{const key=id+":"+i,task=requests.get(key);if(task){requests.delete(key);task.resolve(data);}};
window.CollectionReceive=(id,data)=>{const task=collectionRequests.get(id);if(task){collectionRequests.delete(id);task.resolve(data);}};
window.SearchReceive=(id,data)=>{const task=searchRequests.get(id);if(task){searchRequests.delete(id);task.resolve(data);}};
function loadScript(file,key,registry){
 const old=registry.get(key);if(old)return old.promise;
 let resolve,reject;const promise=new Promise((r,j)=>{resolve=r;reject=j;});registry.set(key,{promise,resolve,reject});
 const script=document.createElement("script");script.src=file;script.async=true;
 script.onerror=()=>{registry.delete(key);reject(new Error("The data file could not be opened. Reload to try again."));script.remove();};
 script.onload=()=>{if(registry.has(key)){registry.delete(key);reject(new Error("The data file did not initialize."));}script.remove();};
 document.head.appendChild(script);return promise;
}
async function collectionData(meta){if(currentCollection?.id===meta.id)return currentCollection.records;currentCollection=null;const v=await unpack(await loadScript(meta.file,meta.id,collectionRequests));if(v.records.length!==meta.count)throw new Error("The equipment record count does not match its source index.");if(S.meta?.id===meta.id)currentCollection={id:meta.id,records:v.records};return v.records;}
async function searchData(meta){if(searchInFlight.has(meta.id))return searchInFlight.get(meta.id);const task=(async()=>{const p=await unpack(await loadScript(meta.searchFile,meta.id,searchRequests));if(p.search.length!==meta.count)throw new Error("The source search index could not be verified.");return p.search;})();searchInFlight.set(meta.id,task);try{return await task;}finally{searchInFlight.delete(meta.id);}}
const rawInFlight=new Map();
async function rawData(sid){
 if(rawCache?.id===sid)return rawCache;
 if(rawInFlight.has(sid))return rawInFlight.get(sid);
 const m=metas.get(sid);if(!m)throw new Error("Original source data is unavailable.");rawWanted=sid;rawCache=null;
 const task=(async()=>{const all=[];for(let i=0;i<m.chunks.length;i++){const v=await unpack(await loadScript(m.chunks[i].file,sid+":"+i,requests));all.push(...v.rows);}const rows=new Map(all.map(r=>[r[0],r]));const result={id:sid,meta:m,rows,allRows:all.filter(r=>r[0]!==m.headerRow)};if(rawWanted===sid)rawCache=result;return result;})();
 rawInFlight.set(sid,task);try{return await task;}finally{rawInFlight.delete(sid);}
}
async function snapshot(ref){const d=await rawData(ref[0]),r=d.rows.get(ref[1]);if(!r)throw new Error("The original source row could not be found.");return {meta:d.meta,row:r,ref};}
function getCurrent(){return S.detailIndex>=0?S.records?.[S.filtered[S.detailIndex]]:null;}
function loading(text,on=true){const box=$("loadingState");box.replaceChildren();box.hidden=false;if(on)box.append(el("span","loading-orbit"));box.append(el("span","",text));}
function renderCategories(){
 const q=$("categorySearch").value.trim().toLowerCase(),tabs=$("categoryTabs"),focusedId=tabs.contains(document.activeElement)?document.activeElement.id:null;tabs.replaceChildren();let group="";
 const families=["Solar & storage","Power & distribution","Protection & control","Installation & hardware"];
 const entries=C.collections.filter(m=>!q||(m.label+" "+m.family+" "+m.description).toLowerCase().includes(q)).sort((a,b)=>families.indexOf(a.family)-families.indexOf(b.family));
 const tabStop=(entries.find(m=>m.id===S.meta?.id)||entries[0])?.id;
 $("sideCount").textContent=entries.length;
 entries.forEach((m,index)=>{
  if(m.family!==group){group=m.family;tabs.append(el("div","category-group",group));}
  const b=el("button","category-tab");b.id="category-"+m.id;b.setAttribute("role","tab");b.setAttribute("aria-selected",String(S.meta?.id===m.id));b.setAttribute("aria-controls","equipmentPanel");b.tabIndex=m.id===tabStop?0:-1;b.title=m.label+" · "+fmt(m.count)+" catalog records";
  const ico=el("span","category-icon");ico.innerHTML=icon(m.icon,17);
  b.append(ico,el("span","category-label",m.label),el("span","category-number",fmt(m.count)));b.onclick=()=>selectCollection(m);
  b.onkeydown=e=>{if(!["ArrowDown","ArrowUp","Home","End"].includes(e.key))return;e.preventDefault();let j=e.key==="Home"?0:e.key==="End"?entries.length-1:Math.max(0,Math.min(entries.length-1,index+(e.key==="ArrowDown"?1:-1)));selectCollection(entries[j]);$("category-"+entries[j].id)?.focus();};tabs.append(b);
 });
 if(!entries.length)tabs.append(el("p","overview-note","No equipment categories match."));
 if(focusedId)$(focusedId)?.focus();
 $("equipmentPanel").setAttribute("aria-labelledby",$("category-"+S.meta?.id)?"category-"+S.meta.id:"collectionTitle");
}
async function selectCollection(meta,changeHash=true){
 if(!meta)return;closeRecord(false);const seq=++S.sequence;S.meta=meta;S.records=null;S.filtered=[];S.query="";S.maker="";S.type="";S.sort=null;S.dir=1;S.page=1;S.searchReady=false;
 $("equipmentSearch").value="";$("manufacturerFilter").replaceChildren(new Option("All manufacturers",""));$("typeFilter").replaceChildren(new Option("All types",""));
 $("stripCategory").textContent=meta.label;$("collectionFamily").textContent=meta.family;
 $("collectionTitle").replaceChildren(document.createTextNode(meta.label),el("span","title-dot","."));
 $("collectionDescription").textContent=meta.description;$("collectionCount").textContent=fmt(meta.count)+" records";$("allRecordsBadge").textContent=fmt(meta.count);$("resultsCount").textContent="Opening the equipment list…";
 $("equipmentBody").replaceChildren();$("pageSummary").textContent="";$("pageTotal").textContent="";$("pageNumber").value=1;
 for(const id of ["firstPage","previousPage","nextPage","lastPage"])$(id).disabled=true;
 loading("Opening "+meta.label.toLowerCase()+"…");renderCategories();$("tableScroll").scrollTop=0;
 if(changeHash)history.replaceState(null,"","#"+meta.id);
 try{const rows=await collectionData(meta);if(seq!==S.sequence)return;S.records=rows;S.searchReady=!!currentCollection?.searchReady;const makers=[...new Set(rows.map(r=>r[I.maker]).filter(Boolean))].sort((a,b)=>a.localeCompare(b));makers.forEach(m=>$("manufacturerFilter").add(new Option(m,m)));meta.types.forEach(t=>$("typeFilter").add(new Option(t,t)));applyFilters();}
 catch(err){if(seq===S.sequence){loading(err.message,false);$("resultsCount").textContent="The equipment list could not load.";}console.error(err);}
}
const collator=new Intl.Collator("en",{numeric:true,sensitivity:"base"});
async function applyFilters(){
 if(!S.records)return;const words=S.query.trim().toLowerCase().split(/\s+/).filter(Boolean);S.filtered=[];
 if(words.length&&!S.searchReady){const seq=S.sequence;loading("Searching all original source specifications…");$("resultsCount").textContent="Searching all source fields…";try{const texts=await searchData(S.meta);if(seq!==S.sequence)return;S.records.forEach((r,i)=>r[I.search]=texts[i]);S.searchReady=true;if(currentCollection?.id===S.meta.id)currentCollection.searchReady=true;return applyFilters();}catch(err){if(seq===S.sequence){loading(err.message,false);$("resultsCount").textContent="Search could not load. Reset the filters to browse all records.";}console.error(err);return;}}
 S.records.forEach((r,i)=>{if(S.maker&&r[I.maker]!==S.maker)return;if(S.type&&r[I.type]!==S.type)return;if(words.length&&!words.every(w=>r[I.search].includes(w)||r[I.rid].toLowerCase().includes(w)))return;S.filtered.push(i);});
 sortRecords();S.page=1;renderRows();
}
function sortRecords(){
 if(!S.records||!S.sort)return;const key={model:I.model,manufacturer:I.maker,type:I.type,rating:I.rating}[S.sort],dir=S.dir;
 S.filtered.sort((a,b)=>{const ra=S.records[a],rb=S.records[b],va=S.sort==="rating"?metric(ra[key]):ra[key],vb=S.sort==="rating"?metric(rb[key]):rb[key];if(!va&&vb)return 1;if(va&&!vb)return -1;if(S.sort==="rating"){const units=collator.compare(ra[key][1]||"",rb[key][1]||"");if(units)return units*dir;const na=Number(ra[key][0]),nb=Number(rb[key][0]);if(Number.isFinite(na)&&Number.isFinite(nb)&&na!==nb)return(na<nb?-1:1)*dir;}return collator.compare(va||"",vb||"")*dir||a-b;});
}
function renderRows(){
 if(!S.records)return;const n=S.filtered.length,pages=Math.max(1,Math.ceil(n/S.pageSize));S.page=Math.max(1,Math.min(S.page,pages));const start=(S.page-1)*S.pageSize,end=Math.min(start+S.pageSize,n),body=$("equipmentBody");body.replaceChildren();
 for(let pos=start;pos<end;pos++){
  const r=S.records[S.filtered[pos]],row=el("tr");row.tabIndex=0;row.setAttribute("aria-label","Open "+(r[I.model]||"equipment record")+" · "+r[I.rid]);row.dataset.recordId=r[I.rid];
  const model=el("td"),wrap=el("div","model-cell"),ico=el("span","row-icon");ico.innerHTML=icon(S.meta.icon,17);
  const text=el("div","model-content");text.append(el("span","model-name",r[I.model]),el("span","model-code",r[I.rid]));wrap.append(ico,text);model.append(wrap);model.title=r[I.model];
  const manufacturer=el("td");manufacturer.append(el("span","manufacturer-text",r[I.maker]||"—"));manufacturer.title=r[I.maker]||"Manufacturer not stated";
  const typ=el("td");typ.append(el("span","type-tag",r[I.type]));
  const rate=el("td"),vol=el("td");rate.append(el("span",metric(r[I.rating])?"rating-text":"empty-value",metric(r[I.rating])||"—"));vol.append(el("span",metric(r[I.voltage])?"voltage-text":"empty-value",metric(r[I.voltage])||"—"));rate.title=r[I.rating][2]||"Rating not stated";vol.title=r[I.voltage][2]||"Voltage not stated";
  const source=el("td"),si=el("span","source-indicator");const sym=el("span");sym.innerHTML=icon("parts",11);si.append(sym,document.createTextNode(fmt(r[I.refs].length)));source.append(si);source.title=r[I.refs].length+" original source records";
  if(r[I.review]||r[I.candidate])source.append(el("span","review-indicator","Review noted"));
  const arrow=el("td");arrow.append(el("span","row-arrow","↗"));row.append(model,manufacturer,typ,rate,vol,source,arrow);
  row.onclick=()=>openRecord(pos,row);row.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();openRecord(pos,row);}};body.append(row);
 }
 $("resultsCount").textContent=fmt(n)+(n===1?" record":" records")+(n!==S.meta.count?" matching · "+fmt(S.meta.count)+" total":" in one equipment list");
 $("pageSummary").textContent=n?fmt(start+1)+"–"+fmt(end)+" of "+fmt(n)+" records":"No matching records";
 $("pageNumber").value=S.page;$("pageNumber").max=pages;$("pageTotal").textContent="of "+fmt(pages);$("firstPage").disabled=$("previousPage").disabled=S.page===1;$("nextPage").disabled=$("lastPage").disabled=S.page>=pages;
 document.querySelectorAll("[data-sort]").forEach(b=>{b.classList.toggle("sort-active",S.sort===b.dataset.sort);b.lastElementChild.textContent=S.sort===b.dataset.sort?(S.dir===1?"↑":"↓"):"↕";b.parentElement.setAttribute("aria-sort",S.sort===b.dataset.sort?(S.dir===1?"ascending":"descending"):"none");});
 if(n)$("loadingState").hidden=true;else loading("No records match these filters. Try a different model, manufacturer or equipment type.",false);
}
function resetFilters(){$("equipmentSearch").value="";$("manufacturerFilter").value="";$("typeFilter").value="";S.query=S.maker=S.type="";applyFilters();}
function goPage(p){S.page=p;renderRows();$("tableScroll").scrollTop=0;}
function openRecord(pos,trigger){
 if(!S.records||pos<0||pos>=S.filtered.length)return;
 if(trigger)S.focus=trigger;S.detailIndex=pos;S.detailToken++;S.snapshot=null;S.sourcePage=0;
 const r=getCurrent();$("recordCategory").textContent=S.meta.label;$("recordId").textContent=r[I.rid];$("recordManufacturer").textContent=r[I.maker]||"Manufacturer not stated";$("recordTitle").textContent=r[I.model]||r[I.rid];$("recordType").textContent=r[I.type];$("recordIcon").innerHTML=icon(S.meta.icon,29);$("sourceCount").textContent=r[I.refs].length;$("recordPosition").textContent=fmt(pos+1)+" of "+fmt(S.filtered.length);
 $("previousRecord").disabled=pos===0;$("nextRecord").disabled=pos>=S.filtered.length-1;$("recordDrawer").hidden=false;$("recordBackdrop").hidden=false;document.body.style.overflow="";document.body.style.overflow="hidden";setRecordView("overview");$("closeRecord").focus();
}
function closeRecord(focus=true){if($("recordDrawer").hidden)return;$("recordDrawer").hidden=true;$("recordBackdrop").hidden=true;document.body.style.overflow="";S.detailToken++;S.detailIndex=-1;S.snapshot=null;if(focus&&S.focus?.isConnected)S.focus.focus();S.focus=null;}
function recordLine(label,value,cls=""){const div=el("div","detail-line");div.append(el("span","",label),el("strong",cls,value||"—"));return div;}
function setRecordView(view){
 S.view=view;S.detailToken++;$("recordContent").setAttribute("aria-labelledby",view+"Tab");$("recordContent").scrollTop=0;document.querySelectorAll(".record-tabs [role=tab]").forEach(b=>{b.setAttribute("aria-selected",String(b.dataset.view===view));b.tabIndex=b.dataset.view===view?0:-1;});
 if(view==="overview")renderOverview();else if(view==="specifications")renderSpecifications();else renderSources();
}
function renderOverview(){
 const r=getCurrent();if(!r)return;const box=$("recordContent");box.replaceChildren();
 box.append(el("p","overview-note","Specifications and source records for this equipment, together. Original parameter sets and qualification notes remain separate within the record."));
 const metrics=el("div","overview-metrics");
 [["Rating",r[I.rating]],["Voltage",r[I.voltage]]].forEach(([label,a])=>{const b=el("div","overview-metric");b.append(el("span","",a[2]||label));const s=el("strong","",a[0]||"—");if(a[1])s.append(el("small","",a[1]));b.append(s);metrics.append(b);});box.append(metrics);
 const cap=el("div","record-section-label");cap.append(el("span","","EQUIPMENT DETAILS"),el("span","","ORIGINAL RECORD"));box.append(cap,recordLine("Manufacturer",r[I.maker]),recordLine("Model",r[I.model]),recordLine("Equipment type",r[I.type]),recordLine("Record ID",r[I.rid]),recordLine("Listing states",r[I.states].filter(Boolean).join(" · ")),recordLine("Source records",fmt(r[I.refs].length)));
 if(r[I.quality]||r[I.review]||r[I.gate]){
  const q=el("div","quality-card"+(r[I.review]||r[I.candidate]?"":" neutral"));q.append(el("strong","",r[I.review]||r[I.candidate]?"Review notes remain applicable":"Original data status"));if(r[I.candidate])q.append(el("div","",fmt(r[I.candidate])+" source listing or configuration relationship"+(r[I.candidate]===1?" requires":"s require")+" identity review. Candidate links do not establish an approved equipment match."));
  if(r[I.quality])q.append(el("pre","",r[I.quality]));if(r[I.gate])q.append(el("pre","",r[I.gate]));box.append(q);
 }
 const actions=el("div","primary-actions"),spec=el("button","button button-secondary","View specifications ↗"),sources=el("button","button button-secondary","Explore sources ↗");spec.onclick=()=>setRecordView("specifications");sources.onclick=()=>setRecordView("sources");actions.append(spec,sources);box.append(actions);
 const sc=el("div","record-section-label");sc.append(el("span","","CONNECTED SOURCE DATA"),el("span","",r[I.refs].length+" RECORDS"));box.append(sc);
 r[I.refs].slice(0,3).forEach(ref=>{const b=el("button","source-card-button");const ic=el("span","source-card-icon","▤"),txt=el("span","source-card-title");txt.append(el("strong","",sourceLabel(ref)),el("small","",sourceSubtitle(ref)));b.append(ic,txt,el("span","source-card-arrow","↗"));b.onclick=()=>{setRecordView("sources");};const card=el("div","source-card");card.append(b);box.append(card);});
}
function sourceLabel(ref){
 const m=metas.get(ref[0]);if(ref[2]==="review")return m.name==="PV_UNIT_REVIEW"?"Units & qualification review":"Equipment review notes";if(ref[2]==="normalization")return "Cable normalization";if(ref[2]==="performance")return "Performance data point";
 if(m.name==="CEC_MODEL_GROUPS")return "Original configuration identity";
 if(m.name.startsWith("CEC_"))return "California Energy Commission";
 if(ref[2]==="primary")return "Master equipment record";
 return "Catalog source record";
}
function sourceSubtitle(ref){
 const m=metas.get(ref[0]);const kind=ref[2].startsWith("candidate")?"Candidate identity / configuration":ref[2]==="confirmed"?"Linked source listing":ref[2]==="performance"?"Original performance point":"Original specifications";
 const variant=m.name.includes("ARCHIVE")?" · Archived":m.name==="CEC_LEGACY_PCS"?" · Legacy control configuration":"";
 return kind+variant+" · Workbook row "+ref[1];
}
function safeValue(container,value){
 if(value!==null&&/^https?:\/\/\S+$/i.test(value)){
  try{const u=new URL(value);if(["http:","https:"].includes(u.protocol)){const a=el("a","",value);a.href=value;a.target="_blank";a.rel="noopener noreferrer";container.append(a);return;}}catch{}
 }
 container.textContent=value===null?"":value;
}
function nativeFields(snap,query=""){
 const frag=document.createDocumentFragment(),r=snap.row,m=snap.meta,q=query.trim().toLowerCase();
 m.headers.forEach((header,i)=>{
  const v=r[1][i],f=r[4][String(i)];if(q&&!((header||"")+" "+(v||"")+" "+(f?.text||"")).toLowerCase().includes(q))return;
  const block=el("section","spec-field"),label=el("div","spec-label");label.append(el("span","",header||"(blank header)"),el("code","",columnName(i)+r[0]));block.append(label);
  const pre=el("pre","spec-value");const present=r[5].includes(i);
  if(v===null||v===""){pre.classList.add("blank");pre.textContent=!present?"No cell stored":v===""?"Empty string":"No stored value";}else safeValue(pre,v);
  const rawType=r[2][i];pre.title="Original cell type: "+(RAW.typeLabels[rawType]||(!present?"Absent":v===null?"Blank":"Number"));block.append(pre);
  if(f){const d=el("details","formula-box"),s=el("summary","","Original formula · saved value shown"),code=el("pre","",f.text===null?"Shared formula attributes: "+JSON.stringify(f.attrs):"="+f.text);d.append(s,code);block.append(d);}
  frag.append(block);
 });return frag;
}
async function renderSpecifications(){
 const r=getCurrent();if(!r)return;const token=S.detailToken,box=$("recordContent");box.replaceChildren();const load=el("div","drawer-loading");load.append(el("span","loading-orbit"),el("span","","Opening original specifications…"));box.append(load);
 try{const snap=await snapshot(r[I.primary]);if(token!==S.detailToken||!getCurrent())return;S.snapshot=snap;box.replaceChildren();
  const head=el("div","specification-header");head.append(el("span","",snap.meta.headers.length+" original fields"));const a=el("a","","Original Excel ↗");a.href=snap.meta.file;a.download=snap.meta.name+".xlsx";head.append(a);box.append(head);
  const label=el("label","spec-search"),i=document.createElement("input");i.type="search";i.placeholder="Find a field or value…";i.setAttribute("aria-label","Find a specification field");const si=el("span","search-icon");label.append(si,i);box.append(label);
  const fields=el("div");fields.id="specificationFields";fields.append(nativeFields(snap));box.append(fields);i.oninput=()=>{fields.replaceChildren(nativeFields(snap,i.value));if(!fields.children.length)fields.append(el("p","overview-note","No original fields match this search."));};
 }catch(err){if(token===S.detailToken)box.replaceChildren(el("p","overview-note",err.message));console.error(err);}
}
function renderSources(){
 const r=getCurrent();if(!r)return;const box=$("recordContent");box.replaceChildren();const refs=r[I.refs],per=15,pages=Math.max(1,Math.ceil(refs.length/per));S.sourcePage=Math.min(S.sourcePage,pages-1);
 box.append(el("p","source-summary","Every source below belongs to this equipment record or carries an explicit candidate relationship. Open a source to see its complete original fields and qualification context."));
 const controls=el("div","source-page-controls");controls.append(el("span","",fmt(refs.length)+" original source records"));const n=el("div"),prev=el("button","","←"),next=el("button","","→");prev.setAttribute("aria-label","Previous source records");next.setAttribute("aria-label","Next source records");prev.disabled=S.sourcePage===0;next.disabled=S.sourcePage===pages-1;prev.onclick=()=>{S.sourcePage--;renderSources();};next.onclick=()=>{S.sourcePage++;renderSources();};n.append(prev,el("span","",String(S.sourcePage+1)+" / "+pages),next);controls.append(n);box.append(controls);
 refs.slice(S.sourcePage*per,(S.sourcePage+1)*per).forEach((ref,j)=>{
  const card=el("section","source-card"),b=el("button","source-card-button"),t=el("span","source-card-title"),ico=el("span","source-card-icon","▤"),small=el("small",ref[2].startsWith("candidate")?"candidate-label":"",sourceSubtitle(ref));t.append(el("strong","",sourceLabel(ref)),small);b.append(ico,t,el("span","source-card-arrow","⌄"));b.setAttribute("aria-expanded","false");const details=el("div","source-extra");details.hidden=true;card.append(b,details);box.append(card);
  let opened=false;
  b.onclick=async()=>{
   const show=details.hidden;details.hidden=!show;b.setAttribute("aria-expanded",String(show));b.lastElementChild.textContent=show?"⌃":"⌄";if(!show||opened)return;opened=true;details.append(el("p","overview-note","Opening the original source record…"));const token=S.detailToken;
   try{const snap=await snapshot(ref);if(token!==S.detailToken||!getCurrent())return;details.replaceChildren();
    if(ref[2].startsWith("candidate"))details.append(el("div","quality-card","Candidate relationship: identity or configuration review remains required. This source is retained without replacing the master specification."));
    if(ref[3])details.append(el("pre","source-scope","Original link disposition: "+ref[3]));
    if(ref[5]&&ref[5]!=="[]")details.append(el("pre","source-scope","Original applicability / publication scope:\n"+ref[5]));
    if(ref[6])details.append(el("pre","source-scope","Original identity basis:\n"+ref[6]));
    const a=el("a","source-link","Download the original source sheet ↗");a.href=snap.meta.file;a.download=snap.meta.name+".xlsx";details.append(a,el("p","native-field-count",snap.meta.headers.length+" original fields · "+snap.meta.name+" · row "+snap.row[0]));
    const table=document.createElement("table"),body=document.createElement("tbody");snap.meta.headers.forEach((h,i)=>{const tr=document.createElement("tr"),th=el("th","",h||"(blank header)"),td=document.createElement("td"),v=snap.row[1][i];if(v===null||v==="")td.textContent=v===""?"Empty string":snap.row[5].includes(i)?"No stored value":"No cell stored";else safeValue(td,v);const f=snap.row[4][String(i)];if(f){const d=el("details","formula-box");d.append(el("summary","","Original formula"),el("pre","",f.text===null?JSON.stringify(f.attrs):"="+f.text));td.append(d);}tr.append(th,td);body.append(tr);});table.append(body);details.append(table);
   }catch(err){if(token===S.detailToken){opened=false;details.replaceChildren(el("p","overview-note",err.message));}console.error(err);}
  };
 });
}
function metricObject(a){return a[2]?{storedValue:a[0],unit:a[1],originalField:a[2]}:{storedValue:null,unit:a[1],originalField:null,displayNote:a[0]||null};}
function recordObject(record){return {recordId:record[I.rid],equipmentCategory:S.meta.label,manufacturer:record[I.maker],model:record[I.model],equipmentType:record[I.type],rating:metricObject(record[I.rating]),voltage:metricObject(record[I.voltage]),originalDataStatus:record[I.quality],identityReviewNoted:record[I.review],originalSelectionGate:record[I.gate],listingStates:record[I.states],sources:record[I.refs].map(ref=>({sourceSheet:metas.get(ref[0]).name,sourceRow:ref[1],relationship:ref[2],originalDisposition:ref[3],originalLinkRow:ref[4],originalScope:ref[5]||"",originalIdentityBasis:ref[6]||"",originalExcel:metas.get(ref[0]).file}))};}
function downloadJson(data,name){const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);}
function exportIndex(){if(!S.records)return;downloadJson({purpose:"Catalog index. Full original fields remain in the source records and original Excel files.",category:S.meta.label,originalWorkbook:C.original,records:S.filtered.map(i=>recordObject(S.records[i]))},S.meta.id+"_catalog_index.json");toast("Catalog index saved with original values and source links.");}
async function exportRecord(){
 const r=getCurrent();if(!r)return;const b=$("exportRecord");b.disabled=true;b.textContent="Preparing original source records…";
 try{const out=recordObject(r);out.originalSourceRecords=[];for(const ref of r[I.refs]){const snap=await snapshot(ref);out.originalSourceRecords.push({sheet:snap.meta.name,row:snap.row[0],relationship:ref[2],fields:snap.meta.headers.map((name,i)=>({field:name,address:columnName(i)+snap.row[0],storedValue:snap.row[1][i],cellType:snap.row[2][i],styleIndex:snap.row[3][i],cellPresent:snap.row[5].includes(i),formula:snap.row[4][String(i)]||null}))});}downloadJson(out,(r[I.rid]||"equipment_record").replace(/[^A-Za-z0-9_-]/g,"_")+".json");toast("Full record saved with every attached original source row.");}
 catch(err){toast(err.message);console.error(err);}finally{b.disabled=false;b.textContent="Save full record ↓";}
}
function browse(){closeRecord(false);$("catalog").scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"});}
function showIntegrity(){if(!$("referencesDialog").open)$("integrityDialog").showModal();}
function openReferences(){closeRecord(false);$("referencesDialog").showModal();renderReferenceList();if(!RS.meta)selectReference(C.references[0]);}
function renderReferenceList(){
 const q=$("referenceSearch").value.trim().toLowerCase(),box=$("referenceList");box.replaceChildren();let group="";
 C.references.filter(m=>!q||(m.label+" "+m.group).toLowerCase().includes(q)).forEach(m=>{if(m.group!==group){group=m.group;box.append(el("div","reference-group",group));}const b=el("button","reference-button"+(RS.meta?.id===m.id?" active":""),m.label);b.append(el("span","",fmt(m.rows)));b.onclick=()=>selectReference(m);box.append(b);});
}
async function selectReference(meta){
 const seq=++RS.sequence;RS.meta=meta;RS.rows=[];RS.filtered=[];RS.page=1;$("referenceRecordSearch").value="";$("referenceGroup").textContent=meta.group;$("referenceTitle").textContent=meta.label;$("referenceCount").textContent="Opening original source data…";$("referenceStatus").hidden=false;$("referenceStatus").textContent="Loading…";$("referenceTable").querySelector("thead").replaceChildren();$("referenceTable").querySelector("tbody").replaceChildren();renderReferenceList();
 const original=metas.get(meta.id),a=$("referenceDownload");a.hidden=false;a.href=original.file;a.download=original.name+".xlsx";
 try{const r=await rawData(meta.id);if(seq!==RS.sequence)return;RS.rows=r.allRows;RS.filtered=RS.rows.map((_,i)=>i);$("referenceCount").textContent=fmt(RS.rows.length)+" original data rows · "+r.meta.headers.length+" fields";renderReferenceTable();}
 catch(err){if(seq===RS.sequence)$("referenceStatus").textContent=err.message;console.error(err);}
}
function filterReference(){if(!RS.meta)return;const q=$("referenceRecordSearch").value.trim().toLowerCase();RS.filtered=[];RS.rows.forEach((r,i)=>{if(!q||r[1].some(v=>v!==null&&v.toLowerCase().includes(q)))RS.filtered.push(i);});RS.page=1;renderReferenceTable();}
function renderReferenceTable(){
 const m=metas.get(RS.meta.id),t=$("referenceTable"),h=t.querySelector("thead"),b=t.querySelector("tbody");h.replaceChildren();b.replaceChildren();const tr=document.createElement("tr");tr.append(el("th","","Row"));m.headers.forEach(v=>tr.append(el("th","",v)));h.append(tr);t.style.minWidth=(100+m.headers.length*170)+"px";
 const n=RS.filtered.length,pages=Math.max(1,Math.ceil(n/50));RS.page=Math.max(1,Math.min(pages,RS.page));const from=(RS.page-1)*50,to=Math.min(from+50,n);
 for(let i=from;i<to;i++){const r=RS.rows[RS.filtered[i]],row=document.createElement("tr");const num=el("td");num.append(el("div","",r[0]));row.append(num);m.headers.forEach((_,j)=>{const td=el("td"),v=el("div","",r[1][j]===null?"":r[1][j]);td.title=columnName(j)+r[0];td.append(v);row.append(td);});b.append(row);}
 $("referenceStatus").hidden=n>0;if(!n)$("referenceStatus").textContent="No rows match this search.";$("referencePageSummary").textContent=n?fmt(from+1)+"–"+fmt(to)+" of "+fmt(n):"0 rows";$("referencePrevious").disabled=RS.page===1;$("referenceNext").disabled=RS.page>=pages;
}
$("categorySearch").oninput=renderCategories;
$("equipmentSearch").oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{S.query=$("equipmentSearch").value;applyFilters();},140);};
$("manufacturerFilter").onchange=()=>{S.maker=$("manufacturerFilter").value;applyFilters();};$("typeFilter").onchange=()=>{S.type=$("typeFilter").value;applyFilters();};$("resetFilters").onclick=resetFilters;$("allEquipmentTab").onclick=resetFilters;
document.querySelectorAll("[data-sort]").forEach(b=>b.onclick=()=>{if(S.sort===b.dataset.sort)S.dir*=-1;else{S.sort=b.dataset.sort;S.dir=1;}sortRecords();S.page=1;renderRows();});
$("firstPage").onclick=()=>goPage(1);$("previousPage").onclick=()=>goPage(S.page-1);$("nextPage").onclick=()=>goPage(S.page+1);$("lastPage").onclick=()=>goPage(Math.ceil(S.filtered.length/50));$("pageNumber").onchange=()=>goPage(Number($("pageNumber").value)||1);
$("closeRecord").onclick=()=>closeRecord();$("recordBackdrop").onclick=()=>closeRecord();$("previousRecord").onclick=()=>openRecord(S.detailIndex-1);$("nextRecord").onclick=()=>openRecord(S.detailIndex+1);
document.querySelectorAll(".record-tabs [data-view]").forEach(b=>{b.onclick=()=>setRecordView(b.dataset.view);b.onkeydown=e=>{if(!["ArrowLeft","ArrowRight"].includes(e.key))return;e.preventDefault();const views=["overview","specifications","sources"],i=views.indexOf(S.view),n=views[(i+(e.key==="ArrowRight"?1:2))%3];setRecordView(n);$(n+"Tab").focus();};});
$("exportIndex").onclick=exportIndex;$("exportRecord").onclick=exportRecord;
["navEquipment","headerBrowse","heroBrowse"].forEach(id=>$(id).onclick=browse);
["homeLink","footerHome"].forEach(id=>$(id).onclick=e=>{e.preventDefault();closeRecord(false);$("categorySearch").value="";selectCollection(C.collections.find(m=>m.id==="pv-modules"));window.scrollTo({top:0,behavior:"smooth"});});
["navReferences","sidebarReferences","footerReferences"].forEach(id=>$(id).onclick=openReferences);
["navIntegrity","sidebarIntegrity","collectionAbout","closingIntegrity","footerIntegrity"].forEach(id=>$(id).onclick=showIntegrity);
$("closeIntegrity").onclick=()=>$("integrityDialog").close();$("closeReferences").onclick=()=>$("referencesDialog").close();
$("referenceSearch").oninput=renderReferenceList;$("referenceRecordSearch").oninput=filterReference;$("referencePrevious").onclick=()=>{RS.page--;renderReferenceTable();};$("referenceNext").onclick=()=>{RS.page++;renderReferenceTable();};
document.addEventListener("keydown",e=>{
 if(e.key==="Escape")closeRecord();
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();browse();$("categorySearch").focus();}
 if(e.key==="/"&&!["INPUT","TEXTAREA","SELECT"].includes(document.activeElement.tagName)&&$("recordDrawer").hidden&&!$("referencesDialog").open&&!$("integrityDialog").open){e.preventDefault();browse();$("equipmentSearch").focus();}
 if(e.key==="Tab"&&!$("recordDrawer").hidden){const focus=[...$("recordDrawer").querySelectorAll("button:not(:disabled),input,a[href],summary")].filter(n=>n.getClientRects().length),first=focus[0],last=focus.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
});
window.addEventListener("hashchange",()=>{const id=decodeURIComponent(location.hash.slice(1));const m=C.collections.find(m=>m.id===id);if(m&&m.id!==S.meta?.id)selectCollection(m,false);});
$("categoryCount").textContent=C.collections.length;$("recordCount").textContent=fmt(C.catalogRecords);$("integrityCells").textContent=fmt(C.storedCells);$("integrityFormulas").textContent=fmt(C.originalFormulas);$("originalIdentity").textContent="Workbook: "+C.original.name+"\nVersion: "+C.original.version+"\nSHA-256: "+C.original.sha256;
const legacy={"PV_MODULES":"pv-modules","IBR":"inverters","BATTERIES":"energy-storage","CABLES":"cables","CEC_PV_ACTIVE":"pv-modules","CEC_PV_ARCHIVE":"pv-modules","CEC_SOLAR_INVERTERS":"inverters","CEC_BATTERY_INVERTERS":"inverters","CEC_INVERTER_ARCHIVE":"inverters","CEC_BATTERIES":"energy-storage","CEC_ENERGY_STORAGE":"energy-storage","CEC_METERS":"meters"};
const initial=decodeURIComponent(location.hash.slice(1));selectCollection(C.collections.find(m=>m.id===(legacy[initial]||initial))||C.collections[0]);
})();

