"""Public catalog regressions. Run: python -m unittest discover -s website/tests.

Uses system Chromium and a local HTTP server; no external fonts or network needed.
"""
import importlib.util
import json
import os
import shutil
import threading
import unittest
from pathlib import Path

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    if os.environ.get("REQUIRE_BROWSER_TESTS") == "1":
        raise
    sync_playwright = None


DIST = Path(__file__).resolve().parents[1] / "dist"


@unittest.skipIf(sync_playwright is None, "Install Playwright to run browser regressions")
class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("catalog_public_server", DIST.parent / "tools" / "serve.py")
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)
        server_module.CatalogHandler.log_message = lambda self, *args: None
        cls.server = server_module.make_server(bind="127.0.0.1", port=0, directory=DIST)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/"
        cls.pw = sync_playwright().start()
        executable = os.environ.get("CHROMIUM_EXECUTABLE") or shutil.which("chromium") or shutil.which("chromium-browser")
        cls.browser = cls.pw.chromium.launch(executable_path=executable, args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        self.context.route("https://**/*", lambda route: route.abort())
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()

    def open(self, fragment="pv-modules"):
        self.page.goto(self.base + "#" + fragment)
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible(timeout=15000)

    def test_fractional_and_invalid_page_numbers_are_clamped(self):
        self.open()
        self.page.locator("#pageNumber").fill("1.5")
        self.page.locator("#pageNumber").press("Tab")
        expect(self.page.locator("#equipmentBody tr")).to_have_count(50)
        expect(self.page.locator("#pageNumber")).to_have_value("1")
        self.assertEqual(self.errors, [])

    def test_malformed_hash_does_not_break_initialization(self):
        self.open("%")
        self.assertEqual(self.errors, [])

    def test_reset_wins_over_a_late_failed_search(self):
        self.open()
        pending = []
        self.page.route("**/pv-modules.search.js", lambda route: pending.append(route))
        self.page.locator("#equipmentSearch").fill("unknown")
        expect(self.page.locator("#resultsCount")).to_contain_text("Searching")
        self.page.locator("#resetFilters").click()
        expect(self.page.locator("#resultsCount")).to_contain_text("39,400")
        self.assertEqual(len(pending), 1)
        pending[0].abort()
        self.page.wait_for_timeout(200)
        expect(self.page.locator("#loadingState")).to_be_hidden()
        expect(self.page.locator("#resultsCount")).to_contain_text("39,400")

    def test_loading_and_failure_disable_stale_list_actions_and_retry(self):
        self.open()
        pending = []
        self.page.route("**/pv-modules.search.js", lambda route: pending.append(route))
        self.page.locator("#equipmentSearch").fill("EHS3-228")
        expect(self.page.locator("#resultsCount")).to_contain_text("Searching")
        expect(self.page.locator("#nextPage")).to_be_disabled()
        expect(self.page.locator("#exportIndex")).to_be_disabled()
        expect(self.page.locator("#equipmentBody tr")).to_have_count(0)
        pending[0].abort()
        expect(self.page.locator("#loadingState")).to_contain_text("could not")
        self.page.unroute("**/pv-modules.search.js")
        self.page.get_by_role("button", name="Retry search", exact=True).click()
        expect(self.page.locator("#loadingState")).to_be_hidden(timeout=20000)
        expect(self.page.locator("#equipmentBody tr").first).to_contain_text("EHS3-228")

    def test_record_links_reload_and_background_is_inert(self):
        self.open()
        self.page.locator("#equipmentBody tr").first.click()
        rid = self.page.locator("#recordId").inner_text()
        self.assertIn("/" + rid, self.page.url)
        self.assertTrue(self.page.locator("main").evaluate("e => e.inert"))
        self.page.reload()
        expect(self.page.locator("#recordId")).to_have_text(rid)
        expect(self.page.locator("#recordDrawer")).to_be_visible()
        self.page.keyboard.press("Escape")
        expect(self.page.locator("#recordDrawer")).to_be_hidden()
        self.assertFalse(self.page.locator("main").evaluate("e => e.inert"))
        self.assertTrue(self.page.url.endswith("#pv-modules"))

    def test_status_filters_match_original_record_claims(self):
        self.open()
        self.page.locator("#listingStateFilter").select_option("ACTIVE")
        self.page.locator("#qualityFilter").select_option("review")
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible()
        self.page.locator("#equipmentBody tr").first.click()
        expect(self.page.locator("#recordContent")).to_contain_text("ACTIVE")
        expect(self.page.locator("#recordContent .quality-card")).to_contain_text("Review notes")

    def test_reference_search_entered_during_loading_is_retained(self):
        self.open()
        pending = []
        self.page.route("**/data/s002.js", lambda route: pending.append(route))
        self.page.locator("#footerReferences").click()
        expect(self.page.locator("#referenceStatus")).to_have_text("Loading…")
        self.page.locator("#referenceRecordSearch").fill("impossible-reference-value-xyz")
        self.assertEqual(len(pending), 1)
        pending[0].continue_()
        expect(self.page.locator("#referenceCount")).to_contain_text("original data rows", timeout=15000)
        expect(self.page.locator("#referenceStatus")).to_have_text("No rows match this search.", timeout=15000)
        expect(self.page.locator("#referenceTable tbody tr")).to_have_count(0)

    def test_all_categories_and_original_navigation_controls(self):
        self.open()
        categories = self.page.evaluate("EQUIPMENT_CATALOG.collections.map(m => ({id:m.id,count:m.count}))")
        self.assertEqual(len(categories), 29)
        for meta in categories:
            self.page.locator("#category-" + meta["id"]).click()
            expect(self.page.locator("#equipmentPanel")).to_have_attribute("aria-busy", "false", timeout=15000)
            expect(self.page.locator("#equipmentBody tr")).to_have_count(min(meta["count"], 50))
            expect(self.page.locator("#collectionCount")).to_have_text(f'{meta["count"]:,} records')
        for button in ["navEquipment", "headerBrowse", "heroBrowse"]:
            self.page.locator("#" + button).click()
        for button in ["sidebarIntegrity", "collectionAbout", "closingIntegrity", "footerIntegrity", "navIntegrity"]:
            self.page.locator("#" + button).click()
            expect(self.page.locator("#integrityDialog")).to_be_visible()
            self.page.locator("#originalIdentity").locator("..").locator("summary").click()
            expect(self.page.locator("#originalIdentity")).to_contain_text("SHA-256:")
            self.page.locator("#closeIntegrity").click()
        for button in ["navReferences", "sidebarReferences", "footerReferences"]:
            self.page.locator("#" + button).click()
            expect(self.page.locator("#referencesDialog")).to_be_visible()
            self.page.locator("#closeReferences").click()
        for button in ["footerHome", "homeLink"]:
            self.page.locator("#" + button).click()
            expect(self.page.locator("#collectionTitle")).to_have_text("PV modules.")
        self.assertEqual(self.errors, [])

    def test_filters_paging_sorting_and_index_export(self):
        self.open("energy-storage")
        self.page.locator("#manufacturerFilter").select_option(index=1)
        maker = self.page.locator("#manufacturerFilter").input_value()
        self.assertTrue(all(m == maker for m in self.page.locator(".manufacturer-text").all_text_contents()))
        self.page.locator("#resetFilters").click()
        self.page.locator("#typeFilter").select_option(index=1)
        typ = self.page.locator("#typeFilter").input_value()
        self.assertTrue(all(t == typ for t in self.page.locator(".type-tag").all_text_contents()))
        self.page.locator("#allEquipmentTab").click()
        for sort in ["model", "manufacturer", "type", "rating"]:
            control = self.page.locator(f'[data-sort="{sort}"]')
            for direction in ["ascending", "descending"]:
                control.click()
                expect(control.locator("..")).to_have_attribute("aria-sort", direction)
                with self.page.expect_download() as info:
                    self.page.locator("#exportIndex").click()
                records = json.loads(Path(info.value.path()).read_text())["records"]
                self.assertEqual(len(records), 8799)
                self.assertEqual([r["recordId"] for r in records[:50]], self.page.locator("#equipmentBody tr").evaluate_all("rs => rs.map(r=>r.dataset.recordId)"))
                if sort == "rating":
                    grouped = {}
                    for record in records:
                        rating = record["rating"]
                        if rating["storedValue"] is not None:
                            try:
                                grouped.setdefault(rating["unit"], []).append(float(rating["storedValue"]))
                            except ValueError:
                                pass
                    for values in grouped.values():
                        self.assertEqual(values, sorted(values, reverse=direction == "descending"))
        self.page.locator("#nextPage").click()
        expect(self.page.locator("#pageNumber")).to_have_value("2")
        self.page.locator("#previousPage").click()
        expect(self.page.locator("#pageNumber")).to_have_value("1")
        self.page.locator("#lastPage").click()
        expect(self.page.locator("#nextPage")).to_be_disabled()
        self.page.locator("#firstPage").click()
        self.page.locator("#pageNumber").fill("999999")
        self.page.locator("#pageNumber").press("Tab")
        expect(self.page.locator("#nextPage")).to_be_disabled()
        self.assertEqual(self.errors, [])

    def test_original_record_fields_sources_and_full_export(self):
        self.open()
        trigger = self.page.locator("#equipmentBody tr").first
        trigger.press("Enter")
        rid = self.page.locator("#recordId").inner_text()
        self.page.locator("#recordContent").get_by_role("button", name="View specifications").click()
        expect(self.page.locator("#specificationFields .spec-field").first).to_be_visible(timeout=15000)
        expect(self.page.locator(".specification-header a")).to_have_attribute("download", "PV_MODULES.xlsx")
        self.page.get_by_role("searchbox", name="Find a specification field").fill("no-field-xyz")
        expect(self.page.locator("#specificationFields")).to_have_text("No original fields match this search.")
        self.page.locator("#sourcesTab").click()
        card = self.page.locator("#recordContent .source-card").first
        card.locator("button").click()
        expect(card.locator(".source-extra table")).to_be_visible(timeout=15000)
        self.assertGreater(card.locator(".source-extra table tr").count(), 20)
        card.locator("button").click()
        expect(card.locator(".source-extra")).to_be_hidden()
        with self.page.expect_download() as info:
            self.page.locator("#exportRecord").click()
        data = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(data["recordId"], rid)
        self.assertEqual(len(data["originalSourceRecords"]), len(data["sources"]))
        self.assertIn("cellPresent", data["originalSourceRecords"][0]["fields"][0])
        self.page.locator("#nextRecord").click()
        self.assertNotEqual(self.page.locator("#recordId").inner_text(), rid)
        self.page.locator("#previousRecord").click()
        expect(self.page.locator("#recordId")).to_have_text(rid)
        self.page.locator("#closeRecord").click()
        expect(trigger).to_be_focused()
        self.assertEqual(self.errors, [])

    def test_category_load_and_detail_load_races_keep_latest_selection(self):
        self.open()
        pending = []
        self.page.route("**/collections/cables.js", lambda route: pending.append(route))
        self.page.locator("#category-cables").click()
        expect(self.page.locator("#collectionTitle")).to_have_text("Cables.")
        self.page.locator("#category-inverters").click()
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible(timeout=15000)
        pending[0].continue_()
        self.page.wait_for_timeout(150)
        expect(self.page.locator("#collectionTitle")).to_have_text("Inverters.")
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible()
        self.page.locator("#category-pv-modules").click()
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible(timeout=15000)
        self.page.route("**/data/s004.js", lambda route: pending.append(route))
        self.page.locator("#equipmentBody tr").first.click()
        self.page.locator("#specificationsTab").click()
        expect(self.page.locator("#recordContent")).to_contain_text("Opening original specifications")
        self.page.locator("#nextRecord").click()
        pending[-1].continue_()
        self.page.wait_for_timeout(150)
        expect(self.page.locator("#overviewTab")).to_have_attribute("aria-selected", "true")
        expect(self.page.locator("#recordContent")).to_contain_text("EHS3-233")
        self.assertEqual(self.errors, [])

    def test_reference_controls_search_paging_and_download(self):
        self.open()
        self.page.locator("#footerReferences").click()
        expect(self.page.locator("#referenceTable tbody tr")).to_have_count(50, timeout=15000)
        expect(self.page.locator("#referenceDownload")).to_have_attribute("download", "CABLE_TYPES.xlsx")
        self.page.locator("#referenceNext").click()
        expect(self.page.locator("#referencePageSummary")).to_contain_text("51–100")
        self.page.locator("#referencePrevious").click()
        self.page.locator("#referenceSearch").fill("conductor materials")
        expect(self.page.locator("#referenceList button")).to_have_count(1)
        self.page.locator("#referenceList button").click()
        expect(self.page.locator("#referenceTable tbody tr")).to_have_count(2)
        self.page.locator("#referenceSearch").fill("xyz-unknown")
        expect(self.page.locator("#referenceList")).to_contain_text("No references match")
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")  # Chromium clears focused search inputs on the first Escape.
        expect(self.page.locator("#referencesDialog")).to_be_hidden()
        self.assertEqual(self.errors, [])

    def test_keyboard_mobile_and_public_wording(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.open()
        self.assertNotIn("Private workspace", self.page.locator("body").inner_text())
        self.page.keyboard.press("Control+k")
        expect(self.page.locator("#categorySearch")).to_be_focused()
        self.page.locator("#categorySearch").fill("inverter")
        self.page.keyboard.press("Tab")
        expect(self.page.locator("#category-inverters")).to_be_focused()
        self.page.keyboard.press("Enter")
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible(timeout=15000)
        self.page.keyboard.press("/")
        expect(self.page.locator("#equipmentSearch")).to_be_focused()
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 390)
        for ident in ["equipmentSearch", "manufacturerFilter", "typeFilter", "listingStateFilter", "qualityFilter", "resetFilters"]:
            bounds = self.page.locator("#" + ident).bounding_box()
            self.assertGreaterEqual(bounds["x"], 0)
            self.assertLessEqual(bounds["x"] + bounds["width"], 390)
        self.page.locator("#equipmentBody tr").first.click()
        self.page.keyboard.press("Shift+Tab")
        expect(self.page.locator("#nextRecord")).to_be_focused()
        self.page.keyboard.press("Tab")
        expect(self.page.locator("#closeRecord")).to_be_focused()
        self.page.keyboard.press("Escape")
        self.assertEqual(self.errors, [])

    def test_deep_link_changes_while_drawer_open_keep_the_target_url(self):
        self.open("pv-modules/PVM-000001")
        expect(self.page.locator("#recordId")).to_have_text("PVM-000001")
        self.page.evaluate("location.hash = 'pv-modules/PVM-000002'")
        expect(self.page.locator("#recordId")).to_have_text("PVM-000002")
        self.assertTrue(self.page.url.endswith("#pv-modules/PVM-000002"))

    def test_category_specification_and_reference_failures_have_working_retry(self):
        self.page.route("**/collections/optimizers.js", lambda route: route.abort())
        self.page.goto(self.base + "#optimizers")
        expect(self.page.locator("#loadingState")).to_contain_text("could not")
        self.page.unroute("**/collections/optimizers.js")
        self.page.get_by_role("button", name="Retry category", exact=True).click()
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible(timeout=15000)
        self.page.locator("#category-pv-modules").click()
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible(timeout=15000)
        self.page.route("**/data/s004.js", lambda route: route.abort())
        self.page.locator("#equipmentBody tr").first.click()
        self.page.locator("#specificationsTab").click()
        expect(self.page.get_by_role("button", name="Retry specifications", exact=True)).to_be_visible()
        self.page.unroute("**/data/s004.js")
        self.page.get_by_role("button", name="Retry specifications", exact=True).click()
        expect(self.page.locator("#specificationFields .spec-field").first).to_be_visible(timeout=15000)
        self.page.locator("#closeRecord").click()
        self.page.route("**/data/s002.js", lambda route: route.abort())
        self.page.locator("#footerReferences").click()
        expect(self.page.get_by_role("button", name="Retry reference", exact=True)).to_be_visible()
        self.page.unroute("**/data/s002.js")
        self.page.get_by_role("button", name="Retry reference", exact=True).click()
        expect(self.page.locator("#referenceTable tbody tr")).to_have_count(50, timeout=15000)

    def test_source_paging_empty_search_and_filter_resets(self):
        self.open("energy-storage/BAT-000236")
        self.page.locator("#sourcesTab").click()
        expect(self.page.locator("#recordContent .source-card")).to_have_count(15)
        self.page.get_by_role("button", name="Next source records", exact=True).click()
        expect(self.page.locator(".source-page-controls")).to_contain_text("2 / 7")
        self.page.get_by_role("button", name="Previous source records", exact=True).click()
        expect(self.page.locator(".source-page-controls")).to_contain_text("1 / 7")
        self.page.locator("#recordBackdrop").click(position={"x": 10, "y": 10})
        self.page.locator("#equipmentSearch").fill("xyz-absent-everywhere-987")
        expect(self.page.locator("#resultsCount")).to_contain_text("0 records", timeout=20000)
        expect(self.page.locator("#loadingState")).to_contain_text("No records match")
        self.page.get_by_role("button", name="Clear filters", exact=True).click()
        expect(self.page.locator("#equipmentBody tr")).to_have_count(50)
        self.page.locator("#category-pv-modules").click()
        expect(self.page.locator("#equipmentBody tr")).to_have_count(50, timeout=15000)
        self.page.locator("#qualityFilter").select_option("candidate")
        expect(self.page.locator("#equipmentBody tr").first).to_be_visible()
        self.page.locator("#equipmentBody tr").first.click()
        expect(self.page.locator("#recordContent")).to_contain_text("identity review")

    def test_bootstrap_failure_offers_reload(self):
        self.page.route("**/collections/index.js", lambda route: route.abort())
        self.page.goto(self.base)
        expect(self.page.get_by_role("button", name="Reload catalog", exact=True)).to_be_visible()
        self.page.unroute("**/collections/index.js")
        self.page.get_by_role("button", name="Reload catalog", exact=True).click()
        expect(self.page.locator("#equipmentBody tr")).to_have_count(50, timeout=15000)

    def test_skip_link_preserves_selected_category(self):
        self.open("inverters")
        self.page.locator(".skip-link").focus()
        self.page.keyboard.press("Enter")
        expect(self.page.locator("#equipmentPanel")).to_be_focused()
        expect(self.page.locator("#collectionTitle")).to_have_text("Inverters.")

    def test_direct_skip_link_initializes_catalog(self):
        self.open("equipmentPanel")
        expect(self.page.locator("#collectionTitle")).to_have_text("PV modules.")


if __name__ == "__main__":
    unittest.main()
