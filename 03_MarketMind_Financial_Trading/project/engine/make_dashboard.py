"""Build a fully-offline, read-only report for the captured broker statement dates."""
import html
import json
from pathlib import Path
from market_engine import IST, read_json, portfolio_audit

ROOT=Path(__file__).resolve().parent


def build(out=None):
    out=Path(out or ROOT/'dashboard.html')
    p=read_json(ROOT/'data'/'portfolio_statement_snapshot.json')
    a=portfolio_audit(p)
    v=a['summary_statement_rupees']
    tr=[]
    for s in p['stocks']:
        pl=s['unrealized_pnl']; pct=pl/s['invested']*100
        tr.append(f"<tr><td><strong>{html.escape(s['symbol'])}</strong><small>{html.escape(s['name'])}</small></td><td>{s['quantity']:,}</td><td>₹{s['avg_buy']:,.2f}</td><td>₹{s['price_close']:,.2f}</td><td>₹{s['closing_value']:,.2f}</td><td class={'pos' if pl>=0 else 'neg'}>₹{pl:,.2f} ({pct:+.1f}%)</td><td><span class='hold'>WAIT · verify</span></td></tr>")
    mr=[]
    for f in p['mutual_funds']:
        pl=f['closing_value']-f['invested']
        mr.append(f"<tr><td>{html.escape(f['scheme_name'])}<small>{html.escape(f['position_key'])} · {html.escape(f['category'])}</small></td><td>{f['units']:,.3f}</td><td>₹{f['invested']:,.2f}</td><td>₹{f['closing_value']:,.2f}</td><td class={'pos' if pl>=0 else 'neg'}>₹{pl:,.2f}</td></tr>")
    # The NSE EOD module is optional. Show its last observed state separately
    # from the historical broker statement valuation; never mix as-of dates.
    nse_file=ROOT/'reports'/'nse_eod_pipeline_status.json'
    nse=read_json(nse_file) if nse_file.exists() else None
    nse_status='No NSE daily archive has been imported; as-of close data are unavailable.'
    if nse:
        if nse.get('success'):
            nse_status=(f"Raw NSE EOD archive imported for {html.escape(str(nse.get('ingested_asof_date')))} "
                        f"({int(nse.get('matched_symbols',0))} of 6 holdings). "
                        'Transactionally recorded RAW/UNADJUSTED EOD research only; not a live quote or adjusted backtest feed.')
        else:
            nse_status=('No verified NSE EOD archive available in the latest daily job. '
                        'Saved Groww valuations remain unchanged; download/import was not completed.')
    nse_section=('<section><h2>NSE end-of-day data pipeline</h2>'
                 f'<p class="muted">{nse_status}</p>'
                 '<p class="muted">Source: <a href="https://www.nseindia.com/all-reports">NSE official Bhavcopy reports</a>. '
                 'End-of-day reports are not adjusted for all corporate actions and are not real-time trade quotes. '
                 'CSV identity/date/source checks are separate from fundamental verification.</p></section>')
    s='''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Indian Market Intelligence · Snapshot</title><style>
    *{box-sizing:border-box}body{font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#f5f7fa;color:#152337;margin:0}
    header{background:#142640;color:white;padding:28px max(20px,calc((100vw - 1180px)/2));box-shadow:0 4px 25px #07142422}
    h1{font-size:24px;margin:2px 0 5px;letter-spacing:-.6px}h2{font-size:17px;margin:0 0 13px}header p{margin:0;color:#bbcadc}
    main{max-width:1180px;margin:auto;padding:24px 20px 60px}.notice{border-left:4px solid #be832a;background:#fffaf0;padding:12px 17px;border-radius:6px;margin:0 0 20px;color:#67450b}
    .kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:0 0 24px}.kpi{background:#fff;padding:20px;border:1px solid #e5eaf0;border-radius:10px;box-shadow:0 3px 12px #13213a09}.kpi .t{font-size:12px;color:#5f6e81;text-transform:uppercase;letter-spacing:.5px}.kpi b{display:block;font-size:22px;margin:5px 0}.kpi small{color:#758299}
    section{background:white;border:1px solid #e5eaf0;border-radius:10px;padding:19px;margin-bottom:18px;box-shadow:0 3px 12px #13213a08}.split{display:grid;grid-template-columns:1fr 1fr;gap:16px}.bar{height:13px;background:#e7edf2;border-radius:9px;overflow:hidden;margin:9px 0 4px}.bar>div{height:100%;border-radius:9px}.warn{background:#bb7b32}.neutral{background:#5682b8}span.big{font-size:18px;font-weight:750}p.muted{color:#607086;font-size:13px}
    .scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:right;color:#596b80;font-size:12px;background:#f5f7fa;padding:11px;border-bottom:1px solid #dee5ed;white-space:nowrap}td{text-align:right;padding:11px;border-bottom:1px solid #edf0f3;white-space:nowrap}th:first-child,td:first-child{text-align:left}td small{display:block;color:#8794a3}tr:hover{background:#fafbfc}.neg{color:#b12836}.pos{color:#128258}.hold{background:#eff2f7;color:#405979;padding:3px 7px;border-radius:5px}
    .controls{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}label{display:flex;flex-direction:column;color:#5a6a7b;font-size:12px;font-weight:600}input{padding:10px;border:1px solid #ccd6e0;border-radius:7px;font-size:14px;margin-top:5px}button{background:#213c61;color:#fff;border:0;border-radius:7px;padding:12px 16px;margin-top:14px;cursor:pointer}#result{background:#f0f5fc;margin-top:16px;border-radius:8px;padding:12px 16px;min-height:46px}footer{color:#798493;font-size:12px}
    @media(max-width:950px){.kpis{grid-template-columns:1fr 1fr}.split{grid-template-columns:1fr}.controls{grid-template-columns:1fr 1fr}}@media(max-width:580px){.kpis,.controls{grid-template-columns:1fr}header{padding:24px 18px}}
    </style></head><body><header><h1>INDIAN MARKET INTELLIGENCE</h1><p>Groww statement snapshots · 21 Oct stocks / 22 Oct mutual funds · Research only</p></header><main>
    <div class="notice"><strong>Not a live quote feed.</strong> This dashboard contains private portfolio snapshots from two different dates. No orders are sent. Risk limits and examples are not personal investment advice.</div>
    <div class="kpis"><div class="kpi"><span class="t">Total holdings value</span><b>₹@@TOTAL@@</b><small>Stock + mutual funds</small></div><div class="kpi"><span class="t">Total unrealised P&amp;L</span><b>₹@@PNL@@</b><small>Broker statement totals</small></div><div class="kpi"><span class="t">Stocks value</span><b>₹@@STOCKS@@</b><small>As of 21 Oct</small></div><div class="kpi"><span class="t">Mutual funds value</span><b>₹@@MFS@@</b><small>As of 22 Oct</small></div></div>
    <div class="split"><section><h2>TCI Express concentration <span class="big">75.67%</span></h2><div class="bar"><div class="warn" style="width:75.67%"></div></div><p class="muted">Share of the stock-only portfolio. Treat averaging down as a research decision, never an automatic rule.</p></section><section><h2>Gold + silver funds <span class="big">46.12%</span></h2><div class="bar"><div class="neutral" style="width:46.12%"></div></div><p class="muted">Share of the combined two-date portfolio. Commodity concentration needs review.</p></section></div>
    @@NSE_SECTION@@
    <section><h2>Stock holdings · statement close</h2><div class="scroll"><table><thead><tr><th>Company</th><th>Shares</th><th>Avg cost</th><th>Statement price</th><th>Market value</th><th>Unrealised P&amp;L</th><th>Research status</th></tr></thead><tbody>@@STOCK_ROWS@@</tbody></table></div></section>
    <section><h2>Mutual fund positions · folio-level, identifiers masked</h2><div class="scroll"><table><thead><tr><th>Scheme</th><th>Units</th><th>Invested</th><th>Market value</th><th>Unrealised P&amp;L</th></tr></thead><tbody>@@MF_ROWS@@</tbody></table></div></section>
    <section><h2>Risk-budget sizing calculator <small>Example planning tool, not BUY instruction</small></h2><p class="muted">Enter proposed entry and review-exit prices and the cash available after one-month reserves. Review level is not a guaranteed fill. This calculator cannot read prices, verify fundamentals or approve an order.</p>
      <div class="controls"><label>Available cash ₹<input id="cash" type="number" min="0" step="100" placeholder="Must enter"></label><label>Reserved within one month ₹<input id="reserve" type="number" min="0" step="100" placeholder="Must enter"></label><label>Entry price ₹<input id="entry" type="number" min="0.01" step="0.01" placeholder="Proposed, not fetched"></label><label>Review exit ₹<input id="exit" type="number" min="0.01" step="0.01" placeholder="Below entry"></label><label>Max trade / free cash (%)<input id="cap" type="number" value="10" min="0.1" max="100" step="0.5"></label><label>Risk budget / free cash (%)<input id="risk" type="number" value="1" min="0.1" max="100" step="0.1"></label></div><button id="calc">Calculate candidate quantity</button><div id="result" aria-live="polite">No purchase quantity without complete inputs.</div>
    </section><footer>Reconciliation exceptions: ₹4.35 invested-stocks difference and ₹0.02 mutual-fund closing value difference between displayed rows and broker summary. Repeated fund names are distinct folio positions, not accidental duplicated rows. No actual trade or research sign-off performed.</footer></main><script>
    document.getElementById('calc').addEventListener('click',()=>{const g=(k)=>{const e=document.getElementById(k);return e.value.trim()===''?NaN:Number(e.value)};const c=g('cash'),r=g('reserve'),e=g('entry'),x=g('exit'),cap=g('cap')/100,risk=g('risk')/100;const out=document.getElementById('result');
    if(![c,r,e,x,cap,risk].every(Number.isFinite)||c<0||r<0||e<=0||x<=0||x>=e||cap<=0||cap>1||risk<=0||risk>1){out.textContent='WAIT — enter a valid cash balance, reserve, entry above review-exit, and risk limits.';return}
    const free=Math.max(0,c-r),q=Math.max(0,Math.floor(Math.min(free/e,free*cap/e,free*risk/(e-x))));
    const rupees=(v)=>'₹'+v.toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});
    out.innerHTML='<strong>Candidate shares: '+q+'</strong> · Proposed capital '+rupees(q*e)+' · Planned review-exit downside '+rupees(q*(e-x))+' · If price gaps 15% below the review level: '+rupees(q*(e-0.85*x))+'<br><small>Research candidate only. Real orders require independently verified price, company/filing research and separate human authorization.</small>';
    });</script></body></html>'''
    for k,val in {'@@TOTAL@@':f"{v['market_value']:,.2f}",'@@PNL@@':f"{v['unrealized_pnl']:+,.2f}",'@@STOCKS@@':f"{p['stock_statement_totals']['value']:,.2f}",'@@MFS@@':f"{p['mutual_fund_statement_totals']['value']:,.2f}",'@@STOCK_ROWS@@':'\n'.join(tr),'@@MF_ROWS@@':'\n'.join(mr),'@@NSE_SECTION@@':nse_section}.items():s=s.replace(k,val)
    out.write_text(s,encoding='utf-8')
    return out

if __name__=='__main__':print('Built',build())
