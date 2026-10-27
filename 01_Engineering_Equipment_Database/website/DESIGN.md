# Master equipment catalog

Continue the original Site and preserve its identity, access policy, original 117 data blobs and original 117 XLSX downloads.

## Reference and observed design

Primary visual reference: https://jimo.ai/product/ai
Additional user-supplied inspiration directory: https://www.awwwards.com/websites/ui-design/

The Jimo page was inspected in a live browser during this edit. Its observed opening uses a black canvas, a subdued orbital/star background, centered two-line typography, a luminous light call-to-action, restrained top navigation and dark rounded product panels.

Read-only computed style inspection found a DM Sans h1 at 81.78px and weight 300, with text color rgb(244, 246, 251); h2 text was 52.8px and weight 300. Its product examples use Inter and DM Sans. The top navigation also uses GT Walsheim Pro. This implementation uses the openly available DM Sans Google Fonts stylesheet with system fallbacks. It does not include the proprietary font or Jimo branding.

Implementation colors and orbital geometry are adaptations, not exact extracted CSS. The application uses its own copy, brand, icons and code.

## Equipment organization

Main navigation has one category per equipment family, with type and manufacturer filters. There is no separate CEC equipment section. Original registry fields appear as source claims inside equipment records, alongside the original primary fields and review notes.

The data pipeline retains existing equipment IDs and existing listing links. Literal manufacturer/model/voltage matches attach approval configurations; unknown or ambiguous relationships remain explicit candidate links. Control parameter variants retain every original parameter set. Equipment counts describe catalog records/configurations, not installed hardware quantities.

Full original source data remains immutable. The equipment browsing index and the full source-field search index are separate compressed assets so opening a category does not load the full search corpus. Original field inspection loads one source table at a time.

## Interaction

Equipment list, manufacturer filter, equipment-type filter, full-source keyword search, source-unit-aware rating sort, pagination, original field inspection, formula inspection, source applicability notes, full-record JSON export, catalog-index export, engineering references and integrity reports are functional.

Supporting reference data is grouped by engineering purpose. Source field maps, listing relationships and historical worksheets remain available as supporting information.

The existing private audience is preserved.

## Keyboard navigation correction

Filtering categories keeps one visible category reachable with Tab even when the selected category is outside the results. Activating a category retains focus after the tab list refreshes. Empty search, cleared search and arrow navigation were checked in the live browser preview. Original data and equipment indexes are unchanged.
