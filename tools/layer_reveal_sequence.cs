// cliff_house_02 — Layer Reveal Sequence
// Full execution script (C# via RhinoMCP rhinoceros_operator)
// Includes: Python reset + Phases 1-3 (Phase 4 / deck+pool folded into Phase 3 end)
//
// USAGE: Paste entire block into rhinoceros_operator script parameter.
// DEPENDENCIES: hide_layers.py written to logs folder and run via RunPythonScript.
// RE-AUDIT: Run layer audit script before running if layers have changed.
//
// Layer index as of 2026-05-25 (cliff_house_02, 221 layers):
//   Massing:    17-25
//   Structure:  26-53  (h2_structure parent + all sublayers incl deck_flush_swap 38-50)
//   Finish:     54-140 (House_02_finish + H02_finishes, pool 85-97, deck_pool_swap 98,108-109,213-221)

// ============================================================
// STEP 0 — Write + run Python reset
// ============================================================

string pyScript =
"# -*- coding: utf-8 -*-\n" +
"import rhinoscriptsyntax as rs\n" +
"import scriptcontext as sc\n" +
"# House_01_massing all off (180-186)\n" +
"for i in [180,181,182,183,184,185,186]:\n" +
"    rs.LayerVisible(sc.doc.Layers[i].Id, False)\n" +
"# House_02_massing all off (17-25, plus L1 sublayers 222-225)\n" +
"for i in [17,18,19,20,21,22,23,24,25,222,223,224,225]:\n" +
"    rs.LayerVisible(sc.doc.Layers[i].Id, False)\n" +
"# h2_structure all off (26-53, incl deck_flush_swap 38-50)\n" +
"for i in [26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,\n" +
"          41,42,43,44,45,46,47,48,49,50,51,52,53]:\n" +
"    rs.LayerVisible(sc.doc.Layers[i].Id, False)\n" +
"# House_02_finish / H02_finishes all off (54-140, pool 85-97, deck_pool_swap 98,108-109,213-221)\n" +
"for i in [\n" +
"    54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,\n" +
"    71,72,73,74,75,76,77,78,79,80,81,82,83,84,\n" +
"    85,86,87,88,89,90,91,92,93,94,95,96,97,\n" +
"    98,108,109,\n" +
"    110,111,112,113,114,115,116,117,118,119,120,\n" +
"    121,122,123,124,125,126,127,128,129,130,131,\n" +
"    132,133,134,135,136,137,138,139,140,\n" +
"    213,214,215,216,217,218,219,220,221]:\n" +
"    rs.LayerVisible(sc.doc.Layers[i].Id, False)\n" +
"sc.doc.Views.Redraw()\n";

System.IO.File.WriteAllText(
    @"C:\Users\swags\Documents\2026_aec_cptx_demo\aa_demo_versions\cliff_house_02\logs\hide_layers.py",
    pyScript);

RhinoApp.RunScript(
    "-_RunPythonScript \"C:\\Users\\swags\\Documents\\2026_aec_cptx_demo\\aa_demo_versions\\cliff_house_02\\logs\\hide_layers.py\"",
    false);

var waitEnd = System.DateTime.Now.AddSeconds(2);
while (System.DateTime.Now < waitEnd) { RhinoApp.Wait(); }

// ============================================================
// HELPERS
// ============================================================

var d = Rhino.RhinoDoc.ActiveDoc;

Action<string, bool> sv = (path, vis) => {
    int idx = d.Layers.FindByFullPath(path, -1);
    if (idx < 0) return;
    var l = d.Layers[idx]; l.IsVisible = vis; l.CommitChanges();
};

// tick: 2s delay with message pumping (RhinoApp.Wait keeps UI responsive)
Action tick = () => {
    d.Views.Redraw();
    var e = System.DateTime.Now.AddSeconds(2);
    while (System.DateTime.Now < e) RhinoApp.Wait();
};

// pause: 3s hold at end of phase
Action pause = () => {
    d.Views.Redraw();
    var e = System.DateTime.Now.AddSeconds(3);
    while (System.DateTime.Now < e) RhinoApp.Wait();
};

// ============================================================
// PHASE 00 — House_01 massing buildup (leaf-first, bottom → up)
// ============================================================

sv("House_01::House_01_massing",             true);
sv("House_01::House_01_massing::L1_solids",  true); tick(); // 1
sv("House_01::House_01_massing::L2_solids",  true); tick(); // 2
sv("House_01::House_01_massing::L2_roof",    true); tick(); // 3
sv("House_01::House_01_massing::l3_balcony", true); tick(); // 4
sv("House_01::House_01_massing::L3_solids",  true); tick(); // 5
sv("House_01::House_01_massing::L3_roof",    true); tick(); // 6
pause();

// ============================================================
// PHASE 0 — Site visible, then reveal massing bottom → up
// ============================================================

// Show site first
foreach (var p in new[]{
    "Site::building_site_fixed",
    "Site::building_site_fixed::combined_pad",
    "Site::building_site_fixed::curtain_wall",
    "Site::building_site_fixed::driveway",
    "Site::building_site_fixed::patio_retaining_walls",
    "Site::building_site_fixed::patio_slab",
}) sv(p, true);

d.Views.Redraw();
pause(); // hold on site alone before massing appears

// Reveal massing bottom → up (lowest in panel first)
sv("House_02_massing",                                           true); // parent on, enables children
sv("House_02_massing::h2_L1_solids",                            true);
sv("House_02_massing::h2_L1_solids::L1_garage",                 true);
sv("House_02_massing::h2_L1_solids::L1_main",                   true); tick(); // 1 — L1 bundle
sv("House_02_massing::H2_L2_solid",                             true);
sv("House_02_massing::H2_L2_solid::h2_l2_solids",               true); tick(); // 2 — L2 body
sv("House_02_massing::H2_L2_solid::h2_l2_balcony_solids",       true); tick(); // 3 — L2 balcony
sv("House_02_massing::H2_L2_solid::h2_L2_roof_sollids",         true); tick(); // 4 — L2 roof
sv("House_02_massing::H2_L3_solid",                             true);
sv("House_02_massing::H2_L3_solid::h2_l3_solids",               true); tick(); // 5 — L3 body
sv("House_02_massing::H2_L3_solid::h2_l3_balcony_solids",       true); tick(); // 6 — L3 balcony
pause(); // hold on full massing before deconstruct begins

// ============================================================
// STEP 1 — (massing already fully visible from Phase 0)
// ============================================================

d.Views.Redraw();
tick();

// ============================================================
// PHASE 1 — Deconstruct massing (top → down)
// ============================================================

sv("House_02_massing::H2_L3_solid::h2_l3_balcony_solids", false); tick();
sv("House_02_massing::H2_L3_solid::h2_l3_solids",         false); tick();
sv("House_02_massing::H2_L3_solid",                        false); tick();
sv("House_02_massing::H2_L2_solid::h2_L2_roof_sollids",   false); tick();
sv("House_02_massing::H2_L2_solid::h2_l2_balcony_solids", false); tick();
sv("House_02_massing::H2_L2_solid::h2_l2_solids",         false); tick();
sv("House_02_massing::H2_L2_solid",                        false); tick();
sv("House_02_massing::h2_L1_solids",                       false); tick();
sv("House_02_massing",                                      false);
pause();

// ============================================================
// PHASE 2 — Build structure (bottom → up)
// deck_flush_swap is #3 item shown
// ============================================================

tick();
sv("h2_structure",                                                                    true); tick(); // 1
sv("h2_structure::H2_L1_structure",                                                  true); tick(); // 2
// #3 — deck_flush_swap (flush deck reference + cladding under H2_L1_structure)
sv("h2_structure::H2_L1_structure::deck_flush_swap",                                                        true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding",                                         true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_cladding",                            true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_cladding_dark",                       true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_cladding_light",                      true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_veranda_cladding",                    true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::cladding_other",                         true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::flush_deck_cladding",                    true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::flush_deck_cladding::L1_cladding_dark",  true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::flush_deck_cladding::L1_cladding_light", true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_retaining_wall",                                   true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_retaining_wall::retaining_sides",                  true);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_flush",                                            true); tick(); // 3
sv("h2_structure::H2_L1_structure::L1_garage",                                       true); tick(); // 4
sv("h2_structure::H2_L1_structure::h2l1_walls",                                      true);
sv("h2_structure::H2_L1_structure::h2l1_walls::l1_west",                             true); tick(); // 5
sv("h2_structure::H2_L2_structure",                                                  true); tick();
sv("h2_structure::H2_L2_structure::h2_l2_floors",                                    true); tick();
sv("h2_structure::H2_L2_structure::h2l2_walls",                                      true); tick();
sv("h2_structure::H2_L2_structure::h2_l2_balc",                                      true); tick();
sv("h2_structure::H2_L3_structure",                                                  true); tick();
sv("h2_structure::H2_L3_structure::h2_l3_floors",                                    true); tick();
sv("h2_structure::H2_L3_structure::h2l3_walls",                                      true); tick();
sv("h2_structure::H2_L3_structure::h2_l3_balc",                                      true); tick();
sv("h2_structure::h2_L2_roof",                                                        true); tick();
sv("h2_structure::H2_L3_roof",                                                        true);
pause();

// ============================================================
// PHASE 3 — Swap structure → finish (bottom → up)
// deck_pool_swap = second to last; pool = last
// ============================================================

tick();
sv("House_02_finish",               true);
sv("House_02_finish::H02_finishes", true);

// --- L1 ---
sv("h2_structure::H2_L1_structure::h2l1_walls::l1_west",              false);
sv("h2_structure::H2_L1_structure::h2l1_walls",                        false);
sv("h2_structure::H2_L1_structure::L1_garage",                         false);
sv("House_02_finish::H02_finishes::L1_floors",                          true);
sv("House_02_finish::H02_finishes::L1_floors::L1_floors",               true); tick();
sv("House_02_finish::H02_finishes::L1_walls",                           true);
sv("House_02_finish::H02_finishes::L1_walls::entry",                    true);
sv("House_02_finish::H02_finishes::L1_walls::L1_walls",                 true);
sv("House_02_finish::H02_finishes::L1_door",                            true);
sv("House_02_finish::H02_finishes::L1_door::wood_door",                 true); tick();
sv("House_02_finish::H02_finishes::L1_entry_windows",                   true);
sv("House_02_finish::H02_finishes::L1_entry_windows::L1_frosted_glass", true); tick();
sv("House_02_finish::H02_finishes::L1_windows",                         true);
sv("House_02_finish::H02_finishes::L1_windows::glazing",                true); tick();
sv("House_02_finish::H02_finishes::L1_mullions",                        true);
sv("House_02_finish::H02_finishes::L1_mullions::mullions",              true); tick();
// H2_L1_structure parent NOT hidden here — deck_flush_swap lives under it and must stay
// visible through all of Phase 3 until the deck_pool_swap atomic swap at the end.
tick();

// --- L2 ---
sv("h2_structure::H2_L2_structure::h2_l2_floors",                       false);
sv("House_02_finish::H02_finishes::L2_floors",                          true); tick();
sv("h2_structure::H2_L2_structure::h2l2_walls",                         false);
sv("House_02_finish::H02_finishes::L2_finish",                          true);
sv("House_02_finish::H02_finishes::L2_finish::L2_walls",                true);
sv("House_02_finish::H02_finishes::L2_finish::L2_frosted_glass",        true); tick();
sv("House_02_finish::H02_finishes::L2_windows",                         true);
sv("House_02_finish::H02_finishes::L2_windows::glazing",                true);
sv("House_02_finish::H02_finishes::L2_windows::mullions",               true); tick();
sv("h2_structure::H2_L2_structure::h2_l2_balc",                         false);
sv("House_02_finish::H02_finishes::L2_balconies",                       true); tick();
sv("h2_structure::h2_L2_roof",                                          false);
sv("House_02_finish::H02_finishes::L2_roof",                            true); tick();
sv("h2_structure::H2_L2_structure",                                     false); tick();

// --- L3 ---
sv("h2_structure::H2_L3_structure::h2_l3_floors",                       false);
sv("House_02_finish::H02_finishes::L3_floors",                          true); tick();
sv("h2_structure::H2_L3_structure::h2l3_walls",                         false);
sv("House_02_finish::H02_finishes::L3_finish",                          true);
sv("House_02_finish::H02_finishes::L3_finish::L3_walls",                true);
sv("House_02_finish::H02_finishes::L3_finish::glazing",                 true);
sv("House_02_finish::H02_finishes::L3_finish::mullions",                true);
sv("House_02_finish::H02_finishes::L3_finish::garage_north_window",     true);
sv("House_02_finish::H02_finishes::L3_finish::L3_frosted_glass",        true); tick();
sv("h2_structure::H2_L3_structure::h2_l3_balc",                         false);
sv("House_02_finish::H02_finishes::L3_balconies",                       true); tick();
sv("h2_structure::H2_L3_roof",                                          false);
sv("House_02_finish::H02_finishes::L3_roof",                            true); tick();
sv("h2_structure::H2_L3_structure",                                     false);
// Hide remaining structure sublayers explicitly — do NOT hide h2_structure parent yet,
// as deck_flush_swap (under H2_L1_structure) must stay visible until deck_pool_swap swaps in.
sv("h2_structure::H2_L2_roof",                                          false);
sv("h2_structure::H2_L3_roof",                                          false); tick();

// --- deck_pool_swap — atomic swap with deck_flush_swap ---
// Hide deck_flush_swap and all sublayers, show deck_pool_swap in the same beat (no gap).
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::flush_deck_cladding::L1_cladding_dark",  false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::flush_deck_cladding::L1_cladding_light", false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::flush_deck_cladding",                    false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_cladding",                            false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_cladding_dark",                       false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_cladding_light",                      false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::L1_veranda_cladding",                    false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding::cladding_other",                         false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_cladding",                                         false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_retaining_wall::retaining_sides",                  false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_retaining_wall",                                   false);
sv("h2_structure::H2_L1_structure::deck_flush_swap::deck_flush",                                            false);
sv("h2_structure::H2_L1_structure::deck_flush_swap",                                                        false);
sv("h2_structure::H2_L1_structure",                                                    false);
sv("h2_structure",                                                                      false);
sv("House_02_finish::H02_finishes::deck_pool_swap",                                             true);
sv("House_02_finish::H02_finishes::deck_pool_swap::retaining_sides",                          true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_pool",                                true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool",                      true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::L1_cladding",         true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::L1_cladding_dark",    true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::L1_cladding_light",   true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::L1_veranda_cladding",                    true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::cladding_other",                          true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::flush_deck_cladding",                     true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::flush_deck_cladding::L1_cladding_dark",   true);
sv("House_02_finish::H02_finishes::deck_pool_swap::deck_cladding _pool::flush_deck_cladding::L1_cladding_light",  true); tick();

// --- pool (last) ---
sv("House_02_finish::H02_finishes::pool",                                                   true);
sv("House_02_finish::H02_finishes::pool::new_deck",                                         true);
sv("House_02_finish::H02_finishes::pool::pool_bottom",                                      true);
sv("House_02_finish::H02_finishes::pool::pool_sides",                                       true);
sv("House_02_finish::H02_finishes::pool::stone_rim",                                        true);
sv("House_02_finish::H02_finishes::pool::infinity_weir",                                    true);
sv("House_02_finish::H02_finishes::pool::pool_retaining_wall",                              true);
sv("House_02_finish::H02_finishes::pool::pool_retaining_wall::new_retaining_wall",          true);
sv("House_02_finish::H02_finishes::pool::pool_retaining_sides",                             true);
sv("House_02_finish::H02_finishes::pool::catch_basin_new",                                  true);
sv("House_02_finish::H02_finishes::pool::catch_basin_ends",                                 true);
sv("House_02_finish::H02_finishes::pool::waterfall",                                        true);
sv("House_02_finish::H02_finishes::pool::pool_water_surface",                               true);
d.Views.Redraw();
pause();
