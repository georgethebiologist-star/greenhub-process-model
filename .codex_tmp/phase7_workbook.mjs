import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(".");
const workbookPath = path.join(projectRoot, "Greenhub", "data", "greenhub_feed_inputs.xlsx");
const previewDir = path.join(projectRoot, ".codex_tmp", "workbook_after_phase7");
const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const darkGreen = "#145A4A";
const mediumGreen = "#2D7A68";
const paleGreen = "#E8F3EE";
const inputYellow = "#FFF2CC";
const paleBlue = "#DDEBF7";
const lightGray = "#F2F2F2";
const border = "#B7C9C1";
const placeholderComment =
  "Class-E structural placeholder. Replace with measured, experimental, literature, or vendor data before design, fertilizer-quality, economic, regulatory, or configuration-selection interpretation.";

const readme = workbook.worksheets.getItem("ReadMe");
readme.getRange("A1:B1").values = [["GreenHub Phase 7 Master Input Workbook", null]];
readme.getRange("A39:B45").values = [
  ["Phase7Parameters", "Consolidated NR0-NR7 controls for digestate separation, phosphorus recovery, ammonia recovery, ion exchange, potassium concentration, product finishing, utilities, and provenance."],
  ["Phase 7 scenarios", "NR0 no recovery; NR1 separation; NR2 struvite; NR3 stripping; NR4 struvite plus stripping; NR5 calcium phosphate; NR6 ion exchange; NR7 integrated cascade plus K concentration."],
  ["Process orders", "A separation-P-N-K; B separation-N-P-K; C whole-digestate P-separation-N; D separation only. NR0 and NR1 always use D."],
  ["Phase 7 warning", "All supplied Phase 7 values are quality-class E structural assumptions. They are not measured design data and cannot support TEA, LCA, fertilizer eligibility, water reuse, or configuration selection."],
  ["Utility limitation", "The current repository has no active CHP or plant-wide utility network. Available recovered heat and CHP electricity therefore default to zero."],
  ["Product limitation", "Nutrient streams are composition inventories, not certified fertilizers. Potassium concentration is non-selective and contaminants are co-reported."],
  ["Blank values", "Optional blanks remain missing. Required blanks raise an error outside structural-test mode and may data-gate the affected factory within structural-test mode."],
];
readme.getRange("A39:A45").format = { fill: darkGreen, font: { bold: true, color: "#FFFFFF" }, wrapText: true };
readme.getRange("B39:B45").format = { fill: paleGreen, wrapText: true };
readme.getRange("A39:B45").format.borders = { preset: "all", style: "thin", color: border };

const control = workbook.worksheets.getItem("ModelControl");
control.getRange("A27:C30").values = [
  ["selected_phase7_scenario", "NR4", "NR0 no recovery; NR1 separation; NR2 struvite; NR3 stripping; NR4 integrated baseline; NR5 calcium phosphate; NR6 ion exchange; NR7 full cascade."],
  ["selected_phase7_process_order", "A", "A P then N; B N then P; C whole-digestate P before separation; D separation only."],
  ["phase7_structural_test_mode", true, "TRUE permits visible class-E Phase 7 placeholders. Set FALSE only after replacing every required class-E input."],
  ["phase7_input_basis", "structural_test", "Visible warning: Phase 7 recovery, utility, product, and equipment values are not measured or validated design inputs."],
];
control.getRange("A27:A30").format = { fill: darkGreen, font: { bold: true, color: "#FFFFFF" }, wrapText: true };
control.getRange("B27:B30").format = { fill: inputYellow, font: { bold: true, color: "#1F1F1F" }, horizontalAlignment: "center" };
control.getRange("C27:C30").format = { fill: paleGreen, wrapText: true };
control.getRange("A27:C30").format.borders = { preset: "all", style: "thin", color: border };
control.getRange("B27").dataValidation = { rule: { type: "list", values: ["NR0", "NR1", "NR2", "NR3", "NR4", "NR5", "NR6", "NR7"] } };
control.getRange("B28").dataValidation = { rule: { type: "list", values: ["A", "B", "C", "D"] } };
control.getRange("B29").dataValidation = { rule: { type: "list", values: [true, false] } };

const headers = [
  "category", "name", "python_name", "value", "unit", "scenario", "month",
  "minimum", "maximum", "distribution", "required", "measurement_status",
  "source_class", "reference", "comment", "calculation_method",
  "measured_or_assumed", "priority", "active", "phase_introduced", "limitation_id",
];
const rows = [];
function add(category, name, pythonName, value, unit, minimum, maximum, limitationId, options = {}) {
  rows.push([
    category,
    name,
    pythonName,
    value,
    unit,
    options.scenario ?? "All",
    options.month ?? "All",
    minimum,
    maximum,
    options.distribution ?? "none",
    options.required ?? true,
    options.measurementStatus ?? "assumed",
    options.sourceClass ?? "E",
    options.reference ?? null,
    options.comment ?? placeholderComment,
    options.calculationMethod ?? null,
    options.measuredOrAssumed ?? "assumed",
    options.priority ?? 100,
    options.active ?? true,
    7,
    limitationId,
  ]);
}

add("control", "Default process order", "phase7_process_order", "A", "code", null, null, "LIM-P7-022");
add("common", "Digestate density", "phase7_digestate_density_kg_m3", 1000, "kg/m3", 500, 1500, "LIM-P7-002");
add("common", "Motor efficiency", "phase7_motor_efficiency", 0.9, "fraction", 0.01, 1, "LIM-P7-001");
add("common", "Pump efficiency", "phase7_pump_efficiency", 0.7, "fraction", 0.01, 1, "LIM-P7-012");
add("common", "Liquid heat capacity", "phase7_liquid_heat_capacity_kj_kg_k", 4.0, "kJ/kg/K", 0.1, 10, "LIM-P7-008");
add("common", "Sizing safety factor", "phase7_sizing_safety_factor", 1.2, "ratio", 1, 3, "LIM-P7-021");

add("equalization", "Equalization enabled", "digestate_equalization_enabled", true, "boolean", null, null, "LIM-P7-001");
add("equalization", "Residence time", "equalization_residence_time_h", 12, "h", 0, 240, "LIM-P7-001");
add("equalization", "Working fraction", "equalization_working_fraction", 0.85, "fraction", 0.01, 1, "LIM-P7-001");
add("equalization", "Mixing power density", "equalization_mixing_power_kw_m3", 0.01, "kW/m3", 0, 2, "LIM-P7-001");
add("equalization", "Tank height-to-diameter ratio", "equalization_height_to_diameter_ratio", 1.2, "ratio", 0.1, 10, "LIM-P7-001");
add("equalization", "Ambient design temperature", "equalization_ambient_temperature_c", 15, "degC", -30, 50, "LIM-P7-001");
add("equalization", "Overall heat-transfer coefficient", "equalization_heat_transfer_coefficient_w_m2_k", 1.1, "W/m2/K", 0, 20, "LIM-P7-001");
add("equalization", "Methane release", "equalization_methane_release_fraction", 0, "fraction", 0, 1, "LIM-P7-001");
add("equalization", "Carbon dioxide release", "equalization_co2_release_fraction", 0, "fraction", 0, 1, "LIM-P7-001");
add("equalization", "Ammonia release", "equalization_ammonia_release_fraction", 0, "fraction", 0, 1, "LIM-P7-001");
add("equalization", "Hydrogen sulphide release", "equalization_h2s_release_fraction", 0, "fraction", 0, 1, "LIM-P7-001");

add("separation", "Separator technology", "digestate_separator_technology", "screw_press", "code", null, null, "LIM-P7-002", { comment: "Allowed codes: screw_press, decanter_centrifuge, belt_filter. The current empirical parameters must be calibrated separately for the selected technology." });
add("separation", "Cake moisture", "digestate_cake_moisture_fraction", 0.8, "wet mass fraction", 0, 0.99, "LIM-P7-002");
add("separation", "General particulate capture", "digestate_particulate_capture_fraction", 0.85, "fraction to solids", 0, 1, "LIM-P7-002");
add("separation", "Microbial biomass capture", "digestate_biomass_capture_fraction", 0.9, "fraction to solids", 0, 1, "LIM-P7-002");
add("separation", "Particulate-P capture", "digestate_particulate_p_capture_fraction", 0.9, "fraction to solids", 0, 1, "LIM-P7-002");
add("separation", "Inert-solid capture", "digestate_inert_capture_fraction", 0.95, "fraction to solids", 0, 1, "LIM-P7-002");
add("separation", "Contaminant-pool capture", "digestate_contaminant_capture_fraction", 0.85, "fraction to solids", 0, 1, "LIM-P7-019");
add("separation", "Separator electricity", "digestate_separator_electricity_kwh_m3", 0.5, "kWh/m3 feed", 0, 20, "LIM-P7-002");

add("struvite", "Target pH", "struvite_target_pH", 8.5, "pH", 0, 14, "LIM-P7-003");
add("struvite", "Magnesium source", "struvite_magnesium_source", "MagnesiumChloride", "component ID", null, null, "LIM-P7-003");
add("struvite", "Magnesium solution fraction", "struvite_magnesium_solution_mass_fraction", 0.3, "mass fraction", 0.001, 1, "LIM-P7-003");
add("struvite", "Magnesium to phosphorus ratio", "struvite_magnesium_to_p_molar_ratio", 1.2, "mol Mg/mol P", 0.001, 10, "LIM-P7-003");
add("struvite", "Magnesium dissolution efficiency", "struvite_magnesium_dissolution_efficiency", 0.95, "fraction", 0, 1, "LIM-P7-003");
add("struvite", "Orthophosphate recovery", "struvite_phosphate_recovery_fraction", 0.85, "fraction", 0, 1, "LIM-P7-003");
add("struvite", "Ammonium availability", "struvite_ammonium_availability_fraction", "1.0", "fraction", 0, 1, "LIM-P7-003");
add("struvite", "Residence time", "struvite_residence_time_min", 60, "min", 0, 1440, "LIM-P7-004");
add("struvite", "Mixing power density", "struvite_mixing_power_kw_m3", 0.05, "kW/m3", 0, 5, "LIM-P7-004");
add("struvite", "Base type", "struvite_base_type", "SodiumHydroxide", "component ID", null, null, "LIM-P7-007");
add("struvite", "Base solution fraction", "struvite_base_solution_mass_fraction", 0.5, "mass fraction", 0.001, 1, "LIM-P7-007");
add("struvite", "Pure base dose", "struvite_base_dose_kg_m3", 0.1, "kg/m3 feed", 0, 100, "LIM-P7-007");
add("struvite", "Calcium-phosphate competition", "struvite_calcium_phosphate_competition_fraction", 0.05, "fraction residual PO4", 0, 1, "LIM-P7-003");
add("struvite", "Magnesium-hydroxide competition", "struvite_magnesium_hydroxide_fraction", 0.02, "fraction available Mg", 0, 1, "LIM-P7-003");
add("struvite", "Calcium-carbonate competition", "struvite_calcium_carbonate_fraction", 0.02, "fraction available Ca", 0, 1, "LIM-P7-003");
add("struvite", "Seed dose", "struvite_seed_kg_per_kg_p", 0, "kg seed/kg feed P", 0, 100, "LIM-P7-004");
add("struvite", "Crystal capture", "struvite_crystal_capture_fraction", 0.95, "fraction", 0, 1, "LIM-P7-006");
add("struvite", "Impurity capture", "struvite_impurity_capture_fraction", 0.5, "fraction", 0, 1, "LIM-P7-006");
add("struvite", "Wet-product moisture", "struvite_product_moisture_fraction", 0.25, "wet mass fraction", 0, 0.99, "LIM-P7-006");
add("struvite", "Crystal-separator electricity", "struvite_separator_electricity_kwh_kg", 0.02, "kWh/kg dry product", 0, 10, "LIM-P7-006");

add("calcium phosphate", "Target pH", "calcium_phosphate_target_pH", 9, "pH", 0, 14, "LIM-P7-005");
add("calcium phosphate", "Selected product formula", "calcium_phosphate_product_id", "CalciumPhosphate", "component ID", null, null, "LIM-P7-005");
add("calcium phosphate", "Calcium source", "calcium_phosphate_calcium_source", "CalciumChloride", "component ID", null, null, "LIM-P7-005");
add("calcium phosphate", "Calcium solution fraction", "calcium_phosphate_solution_mass_fraction", 0.3, "mass fraction", 0.001, 1, "LIM-P7-005");
add("calcium phosphate", "Calcium to phosphorus ratio", "calcium_phosphate_ca_to_p_molar_ratio", 1.7, "mol Ca/mol P", 0.001, 20, "LIM-P7-005");
add("calcium phosphate", "Calcium dissolution efficiency", "calcium_phosphate_dissolution_efficiency", 0.98, "fraction", 0, 1, "LIM-P7-005");
add("calcium phosphate", "Orthophosphate recovery", "calcium_phosphate_recovery_fraction", 0.8, "fraction", 0, 1, "LIM-P7-005");
add("calcium phosphate", "Residence time", "calcium_phosphate_residence_time_min", 60, "min", 0, 1440, "LIM-P7-005");
add("calcium phosphate", "Mixing power density", "calcium_phosphate_mixing_power_kw_m3", 0.05, "kW/m3", 0, 5, "LIM-P7-005");
add("calcium phosphate", "Base type", "calcium_phosphate_base_type", "SodiumHydroxide", "component ID", null, null, "LIM-P7-007");
add("calcium phosphate", "Base solution fraction", "calcium_phosphate_base_solution_mass_fraction", 0.5, "mass fraction", 0.001, 1, "LIM-P7-007");
add("calcium phosphate", "Pure base dose", "calcium_phosphate_base_dose_kg_m3", 0.1, "kg/m3 feed", 0, 100, "LIM-P7-007");
add("calcium phosphate", "Calcium-carbonate competition", "calcium_phosphate_carbonate_fraction", 0.05, "fraction available Ca", 0, 1, "LIM-P7-005");
add("calcium phosphate", "Crystal capture", "calcium_phosphate_crystal_capture_fraction", 0.95, "fraction", 0, 1, "LIM-P7-006");
add("calcium phosphate", "Impurity capture", "calcium_phosphate_impurity_capture_fraction", 0.5, "fraction", 0, 1, "LIM-P7-006");
add("calcium phosphate", "Wet-product moisture", "calcium_phosphate_product_moisture_fraction", 0.3, "wet mass fraction", 0, 0.99, "LIM-P7-006");
add("calcium phosphate", "Crystal-separator electricity", "calcium_phosphate_separator_electricity_kwh_kg", 0.02, "kWh/kg dry product", 0, 10, "LIM-P7-006");

add("ammonia stripping", "Target pH", "ammonia_stripper_pH", 10.5, "pH", 0, 14, "LIM-P7-009");
add("ammonia stripping", "Base type", "ammonia_base_type", "SodiumHydroxide", "component ID", null, null, "LIM-P7-007");
add("ammonia stripping", "Base solution fraction", "ammonia_base_solution_mass_fraction", 0.5, "mass fraction", 0.001, 1, "LIM-P7-007");
add("ammonia stripping", "Pure base dose", "ammonia_base_dose_kg_m3", 0.5, "kg/m3 feed", 0, 100, "LIM-P7-007");
add("ammonia stripping", "Conditioning mixing power", "ammonia_conditioning_mixing_power_kw_m3", 0.02, "kW/m3", 0, 5, "LIM-P7-007");
add("ammonia stripping", "Stripper temperature", "ammonia_stripper_temperature_c", 60, "degC", 0, 150, "LIM-P7-009");
add("ammonia stripping", "Stripper pressure", "ammonia_stripper_pressure_bar", "1.0", "bar", 0.01, 20, "LIM-P7-009");
add("ammonia stripping", "Stripping medium", "ammonia_stripping_medium", "air", "air/steam/vacuum", null, null, "LIM-P7-009");
add("ammonia stripping", "Gas-to-liquid ratio", "ammonia_gas_to_liquid_ratio_nm3_m3", 500, "Nm3/m3", 0, 10000, "LIM-P7-009");
add("ammonia stripping", "Steam ratio", "ammonia_steam_kg_kg_liquid", 0.1, "kg/kg liquid", 0, 10, "LIM-P7-009");
add("ammonia stripping", "Packing height", "ammonia_packing_height_m", 6, "m", 0, 50, "LIM-P7-009");
add("ammonia stripping", "Superficial gas velocity", "ammonia_superficial_velocity_m_s", 1.5, "m/s", 0.001, 20, "LIM-P7-009");
add("ammonia stripping", "Apparent transfer coefficient", "ammonia_transfer_coefficient", 4, "dimensionless", 0, 100, "LIM-P7-009");
add("ammonia stripping", "Stripper pressure drop", "ammonia_stripper_pressure_drop_pa", 3000, "Pa", 0, 1000000, "LIM-P7-009");
add("ammonia stripping", "Gas-mover efficiency", "ammonia_gas_mover_efficiency", 0.65, "fraction", 0.01, 1, "LIM-P7-009");
add("ammonia stripping", "Explicit CO2 removal", "ammonia_co2_removal_fraction", 0.5, "fraction", 0, 1, "LIM-P7-010");
add("ammonia stripping", "Liquid-water evaporation", "ammonia_water_evaporation_fraction", 0.005, "fraction", 0, 1, "LIM-P7-009");
add("ammonia stripping", "Steam latent heat", "ammonia_steam_latent_heat_kj_kg", 2257, "kJ/kg", 100, 5000, "LIM-P7-009");

add("acid absorption", "Absorber acid", "ammonia_absorber_acid_type", "SulfuricAcid", "component ID", null, null, "LIM-P7-011");
add("acid absorption", "Acid solution fraction", "ammonia_absorber_acid_solution_mass_fraction", 0.4, "mass fraction", 0.001, 1, "LIM-P7-011");
add("acid absorption", "Acid excess", "ammonia_absorber_acid_excess_fraction", 0.05, "fraction above stoichiometric", 0, 10, "LIM-P7-011");
add("acid absorption", "Ammonia capture efficiency", "ammonia_absorber_capture_efficiency", 0.99, "fraction", 0, 1, "LIM-P7-011");
add("acid absorption", "Absorber water makeup", "ammonia_absorber_water_kg_per_kg_nh3", 5, "kg/kg NH3", 0, 1000, "LIM-P7-011");
add("acid absorption", "CO2 absorption", "ammonia_absorber_co2_absorption_fraction", 0.01, "fraction", 0, 1, "LIM-P7-011");
add("acid absorption", "Neutralization heat", "ammonia_neutralization_heat_kj_mol", 52, "kJ/mol NH3", 0, 1000, "LIM-P7-011");
add("acid absorption", "Absorber pressure drop", "ammonia_absorber_pressure_drop_pa", 1500, "Pa", 0, 1000000, "LIM-P7-011");
add("acid absorption", "Ammonium-product storage", "ammonium_product_storage_time_h", 24, "h", 0, 1000, "LIM-P7-015");

add("ion exchange", "Ammonium recovery", "ion_exchange_ammonium_recovery_fraction", 0.8, "fraction", 0, 1, "LIM-P7-012");
add("ion exchange", "Working capacity", "ion_exchange_capacity_kg_nh4_kg_media", 0.02, "kg NH4/kg media", 0.000001, 1, "LIM-P7-012");
add("ion exchange", "Breakthrough fraction", "ion_exchange_breakthrough_fraction", 0.7, "fraction capacity", 0.000001, 1, "LIM-P7-012");
add("ion exchange", "Service time", "ion_exchange_service_time_h", 8, "h", 0.001, 1000, "LIM-P7-012");
add("ion exchange", "Bed bulk density", "ion_exchange_bed_density_kg_m3", 700, "kg/m3", 1, 5000, "LIM-P7-012");
add("ion exchange", "NaCl to exchanged NH4 ratio", "ion_exchange_nacl_molar_ratio", 1.2, "mol/mol", 0.001, 100, "LIM-P7-012");
add("ion exchange", "Regeneration-brine fraction", "ion_exchange_brine_mass_fraction", 0.1, "mass fraction NaCl", 0.001, 1, "LIM-P7-012");
add("ion exchange", "Rinse-water ratio", "ion_exchange_rinse_water_kg_kg_media", 0.05, "kg/kg site-equivalent media", 0, 100, "LIM-P7-012");
add("ion exchange", "Bed pressure drop", "ion_exchange_pressure_drop_pa", 10000, "Pa", 0, 1000000, "LIM-P7-012");

add("potassium concentration", "Concentration method", "potassium_concentration_method", "evaporation", "evaporation/membrane", null, null, "LIM-P7-013");
add("potassium concentration", "Evaporator water removal", "potassium_evaporation_water_removal_fraction", 0.65, "fraction feed water", 0, 0.99, "LIM-P7-013");
add("potassium concentration", "Evaporation temperature", "potassium_evaporation_temperature_c", 80, "degC", 0, 200, "LIM-P7-013");
add("potassium concentration", "Evaporation latent heat", "potassium_evaporation_latent_heat_kj_kg", 2300, "kJ/kg water", 100, 5000, "LIM-P7-013");
add("potassium concentration", "Evaporator thermal efficiency", "potassium_evaporation_thermal_efficiency", 0.75, "fraction", 0.001, 1, "LIM-P7-013");
add("potassium concentration", "Evaporator electricity", "potassium_evaporator_electricity_kwh_kg_water", 0.02, "kWh/kg water", 0, 10, "LIM-P7-013");
add("potassium concentration", "Membrane pressure", "potassium_membrane_pressure_bar", 20, "bar", 0.001, 200, "LIM-P7-014");
add("potassium concentration", "Membrane osmotic pressure", "potassium_membrane_osmotic_pressure_bar", 5, "bar", 0, 200, "LIM-P7-014");
add("potassium concentration", "Reference net pressure", "potassium_membrane_reference_net_pressure_bar", 15, "bar", 0.001, 200, "LIM-P7-014");
add("potassium concentration", "Reference water recovery", "potassium_membrane_reference_water_recovery_fraction", 0.6, "fraction", 0, 0.95, "LIM-P7-014");
add("potassium concentration", "Water flux", "potassium_membrane_water_flux_l_m2_hr", 20, "L/m2/h", 0.001, 1000, "LIM-P7-014");
add("potassium concentration", "Potassium rejection", "potassium_membrane_k_rejection_fraction", 0.95, "fraction", 0, 1, "LIM-P7-014");
add("potassium concentration", "Monovalent rejection", "potassium_membrane_monovalent_rejection_fraction", 0.85, "fraction", 0, 1, "LIM-P7-014");
add("potassium concentration", "Divalent rejection", "potassium_membrane_divalent_rejection_fraction", 0.98, "fraction", 0, 1, "LIM-P7-014");
add("potassium concentration", "Organic rejection", "potassium_membrane_organic_rejection_fraction", 0.9, "fraction", 0, 1, "LIM-P7-014");
add("potassium concentration", "Contaminant rejection", "potassium_membrane_contaminant_rejection_fraction", 0.95, "fraction", 0, 1, "LIM-P7-014");
add("potassium concentration", "Membrane electricity", "potassium_membrane_electricity_kwh_m3_permeate", 0.5, "kWh/m3 permeate", 0, 100, "LIM-P7-014");
add("potassium concentration", "Membrane cleaning water", "potassium_membrane_cleaning_water_kg_m2_hr", 0.01, "kg/m2/h", 0, 100, "LIM-P7-014");
add("potassium concentration", "K-product storage", "potassium_product_storage_time_h", 24, "h", 0, 1000, "LIM-P7-015");

add("product finishing", "Product washing enabled", "phase7_product_washing_enabled", false, "boolean", null, null, "LIM-P7-016");
add("product finishing", "Wash-water ratio", "phase7_wash_water_kg_per_kg_dry_product", "1.0", "kg/kg dry product", 0, 100, "LIM-P7-016");
add("product finishing", "Wash impurity removal", "phase7_wash_impurity_removal_fraction", 0.8, "fraction", 0, 1, "LIM-P7-016");
add("product finishing", "Wash product loss", "phase7_wash_product_loss_fraction", 0.02, "fraction", 0, 1, "LIM-P7-016");
add("product finishing", "Wash electricity", "phase7_wash_electricity_kwh_kg_product", 0.01, "kWh/kg dry product", 0, 10, "LIM-P7-016");
add("product finishing", "Product drying enabled", "phase7_product_drying_enabled", false, "boolean", null, null, "LIM-P7-016");
add("product finishing", "Finished-product moisture", "phase7_product_target_moisture_fraction", 0.1, "wet mass fraction", 0, 0.99, "LIM-P7-016");
add("product finishing", "Drying temperature", "phase7_product_drying_temperature_c", 40, "degC", 0, 200, "LIM-P7-016");
add("product finishing", "Configured stability limit", "phase7_product_stability_limit_c", 60, "degC", 0, 300, "LIM-P7-016");
add("product finishing", "Wet-product heat capacity", "phase7_product_heat_capacity_kj_kg_k", 3, "kJ/kg/K", 0.1, 10, "LIM-P7-016");
add("product finishing", "Dryer latent heat", "phase7_product_latent_heat_kj_kg", 2400, "kJ/kg water", 100, 5000, "LIM-P7-016");
add("product finishing", "Dryer thermal efficiency", "phase7_product_dryer_thermal_efficiency", 0.7, "fraction", 0.001, 1, "LIM-P7-016");
add("product finishing", "Dryer fan electricity", "phase7_product_fan_electricity_kwh_kg_water", 0.05, "kWh/kg water", 0, 10, "LIM-P7-016");

add("utilities", "Recovered heat available", "phase7_recovered_heat_available_kw", 0, "kW", 0, 1000000, "LIM-P7-018", { comment: "Set to zero because the current repository has no active CHP/plant heat network. Replace only with a real temperature-qualified upstream heat balance." });
add("utilities", "Recovered heat temperature", "phase7_recovered_heat_temperature_c", 80, "degC", 0, 500, "LIM-P7-018");
add("utilities", "Heat-recovery efficiency", "phase7_heat_recovery_efficiency", 0.8, "fraction", 0, 1, "LIM-P7-018");
add("utilities", "CHP electricity available", "phase7_chp_electricity_available_kw", 0, "kW", 0, 1000000, "LIM-P7-018", { comment: "Set to zero because BG1 and the electricity bus are inactive. Do not enter a credit without an implemented or externally verified supply balance." });

let phase7 = workbook.worksheets.items.find((sheet) => sheet.name === "Phase7Parameters");
if (!phase7) {
  phase7 = workbook.worksheets.add("Phase7Parameters");
} else {
  const used = phase7.getUsedRange();
  if (used) used.clear({ applyTo: "all" });
  phase7.tables.items.forEach((table) => table.delete());
}
phase7.showGridLines = false;
phase7.getRangeByIndexes(0, 0, 1, headers.length).values = [headers];
phase7.getRangeByIndexes(1, 0, rows.length, headers.length).values = rows;
const fullRange = phase7.getRangeByIndexes(0, 0, rows.length + 1, headers.length);
fullRange.format = { font: { name: "Aptos", size: 10 }, verticalAlignment: "top" };
fullRange.format.borders = { preset: "all", style: "thin", color: border };
phase7.getRange("A1:U1").format = {
  fill: darkGreen,
  font: { bold: true, color: "#FFFFFF", size: 10 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
};
phase7.getRange(`A2:C${rows.length + 1}`).format.fill = paleGreen;
phase7.getRange(`D2:D${rows.length + 1}`).format = { fill: inputYellow, font: { bold: true, color: "#1F1F1F" } };
phase7.getRange(`E2:J${rows.length + 1}`).format.fill = lightGray;
phase7.getRange(`K2:N${rows.length + 1}`).format.fill = paleBlue;
phase7.getRange(`O2:U${rows.length + 1}`).format.fill = "#F8FAF9";
phase7.getRange(`A2:U${rows.length + 1}`).format.wrapText = true;
phase7.getRange(`H2:I${rows.length + 1}`).setNumberFormat("0.######");
phase7.getRange("A:A").format.columnWidth = 22;
phase7.getRange("B:B").format.columnWidth = 31;
phase7.getRange("C:C").format.columnWidth = 43;
phase7.getRange("D:D").format.columnWidth = 18;
phase7.getRange("E:E").format.columnWidth = 22;
phase7.getRange("F:G").format.columnWidth = 12;
phase7.getRange("H:I").format.columnWidth = 13;
phase7.getRange("J:N").format.columnWidth = 17;
phase7.getRange("O:O").format.columnWidth = 62;
phase7.getRange("P:P").format.columnWidth = 34;
phase7.getRange("Q:U").format.columnWidth = 19;
phase7.freezePanes.freezeRows(1);
phase7.freezePanes.freezeColumns(3);
phase7.getRange(`F2:F${rows.length + 1}`).dataValidation = { rule: { type: "list", values: ["All", "NR0", "NR1", "NR2", "NR3", "NR4", "NR5", "NR6", "NR7"] } };
phase7.getRange(`L2:L${rows.length + 1}`).dataValidation = { rule: { type: "list", values: ["measured", "calculated", "assumed", "estimated", "not_measured", "below_detection_limit", "assumed_absent", "intentionally_excluded"] } };
phase7.getRange(`M2:M${rows.length + 1}`).dataValidation = { rule: { type: "list", values: ["A", "B", "C", "D", "E"] } };
const table = phase7.tables.add(`A1:U${rows.length + 1}`, true, "Phase7ParametersTable");
table.style = "TableStyleMedium4";
table.showBandedRows = false;

await fs.mkdir(previewDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);

for (const sheet of workbook.worksheets.items) {
  const safeName = sheet.name.replace(/[^A-Za-z0-9_-]+/g, "_");
  const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const summary = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 12000 });
console.log(summary.ndjson);
const phase7Inspection = await workbook.inspect({
  kind: "table",
  sheetId: "Phase7Parameters",
  range: `A1:U${rows.length + 1}`,
  include: "values,formulas",
  tableMaxRows: 14,
  tableMaxCols: 21,
  maxChars: 22000,
});
console.log(phase7Inspection.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  maxChars: 12000,
});
console.log(errors.ndjson);
console.log(JSON.stringify({ workbookPath, phase7Rows: rows.length, previewDir }));
