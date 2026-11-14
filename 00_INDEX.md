# Calculator prompt files — index

One file per calculator. Each file is the only document that calculator needs; give it to the AI together with Master Prompt V5.0 (`00_MASTER_PROMPT_V5.0.txt`). Every file has the same sections:

0 About this file · 1 What the calculator does · 2 Requirements (V5.0 requirements verbatim + requirements from the earlier documents + method/verification + connections) · 3 Work already done · 4 Functions still to be added · 5 Earlier work still to be completed · 6 Checks and audits still to be done · 7 Process to follow · 8 Final result · 9 Plugins and tools · 10 First task

**Existing calculators**

| File | Calculator | V5.0 group |
|---|---|---|
| Fault_Current_Studio_prompt.md | Fault current, protection, arc flash, load flow, harmonics | 14 |
| Production_Calculator_prompt.md | Site, resource, shading, tracker, bifacial, plant sizing, energy yield | 1, 16 |
| Cable_Thermal_Calculator_prompt.md | Trench, underground cable, duct bank thermal | 8 |
| Grounding_Calculator_prompt.md | Grounding and bonding | 9 |
| Cable_Tray_Calculator_prompt.md | Conduit, raceway, cable tray, routing, cable pulling | 7 |
| Vault_Calculator_prompt.md | Boxes, enclosures, handholes, vaults | 6 |

**New calculators**

| File | Calculator | V5.0 group |
|---|---|---|
| PV_String_MPPT_Calculator_prompt.md | PV module, string and MPPT design | 2 |
| DC_Protection_Combiner_Calculator_prompt.md | DC protection, fuses, combiner/junction boxes | 3 |
| DC_Cable_Connector_Calculator_prompt.md | DC cables and connectors | 4 |
| Inverter_LV_AC_Calculator_prompt.md | Inverter and LV AC design | 5 |
| Lightning_Surge_Protection_Calculator_prompt.md | Lightning and surge protection | 10 |
| LV_Interconnection_Metering_Calculator_prompt.md | LV interconnection, export control, metering | 11 |
| MV_Electrical_Design_Calculator_prompt.md | Medium-voltage design | 12 |
| Transformer_POI_Calculator_prompt.md | Transformers and POI | 13 |
| Interconnection_Architecture_Calculator_prompt.md | Interconnection architectures | 15 |
| Documentation_Schedules_QA_Calculator_prompt.md | Schedules, BOM, reports, design QA | 17 |

**Shared (used by every calculator)**

| File | Role |
|---|---|
| Engineering_Master_Database_prompt.md | The single equipment database |
| Platform_Website_prompt.md | The website itself: pages, projects, network model, shared engines, security, deployment |

All 428 Master Prompt requirement IDs are covered, each in exactly one file.

**Suggested order:** Engineering_Master_Database → Platform_Website → Fault_Current_Studio → Production_Calculator → Grounding, Cable_Thermal, Cable_Tray, Vault → PV_String_MPPT → DC_Protection_Combiner → DC_Cable_Connector → Inverter_LV_AC → Transformer_POI → MV_Electrical_Design → LV_Interconnection_Metering → Lightning_Surge_Protection → Interconnection_Architecture → Documentation_Schedules_QA.
