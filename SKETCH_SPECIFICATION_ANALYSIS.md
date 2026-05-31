# Sketch Specification DocType - Comprehensive Analysis

## Overview
The Sketch Specification doctype is a complex technical pack management system for fashion design with 200+ fields covering design details, measurements, workstations, colors, and costs.

---

## CRITICAL ISSUES

### 1. **Inconsistent Field Naming & Labeling**
**Severity:** HIGH

**Issue:** Field names don't match their labels, causing confusion:
- `cf_length` → Label: "CB दैर्घ्य (HPS → CB हेम)" (should be CB, not CF)
- `cb_length` → Label: "बक्स (Chest)" (should be Chest, not CB)
- `full_length_arm` → Label: "एलबो (Elbow)" (should be Sleeve Length)
- `pocket_placket` → Label: "कफ़ेर की दैर्घ्य (Cuff Length)" (should be Pocket Placket)

**Impact:** Users enter data in wrong fields; reports/calculations fail

**Fix:** Rename fields to match labels or vice versa for consistency

---

### 2. **Duplicate & Conflicting Measurement Fields**
**Severity:** HIGH

**Issue:** Multiple fields for same measurement:
- `waist_circumstance` vs `komor` (both Waist)
- `bust` vs `high_hip` (both High Hip)
- `upper_hip` vs `low_hip` (naming reversed)
- `pocket_width` appears twice with different meanings
- `shoulder_tip_to_side_waist` vs `shoulder_tip_to_pocket_starting` (unclear difference)

**Impact:** Data inconsistency; users don't know which field to use

**Fix:** Consolidate duplicate fields; rename for clarity

---

### 3. **Broken Field Type Mismatches**
**Severity:** MEDIUM

**Issue:** Fields with wrong data types:
- `komor`, `high_hip`, `low_hip`, `thigh_uru`, `knee_x2`, `leg_opening_x2` → Type: **Data** (should be Float)
- `elasticrubber_width`, `beltloop_width`, `wb_to_pocket_opening`, `pocket_depth` → Type: **Data** (should be Float)
- `hand_embroider`, `sample`, `time`, `rate` → Type: **Data** (should be Float/Currency)

**Impact:** Cannot perform calculations; sorting/filtering broken; validation fails

**Fix:** Change fieldtype from Data to Float/Currency

---

### 4. **Orphaned/Unused Fields**
**Severity:** MEDIUM

**Issue:** Fields with cryptic names that appear unused:
- `data_xmgl`, `data_ryzm`, `data_muzc`, `data_lfwb`, `data_hnjh`, `data_zsdd`, `data_uxrz`, `data_mnat`, `data_wptw`, `data_znsh`
  - These are paired with color fields but have no labels
  - Unclear purpose (color names? codes? descriptions?)
  - No documentation

**Impact:** Confusion; potential data loss if deleted; unclear usage

**Fix:** Add proper labels; document purpose; consider renaming to `color_name_1`, `color_name_2`, etc.

---

### 5. **Measurement Section Organization Issues**
**Severity:** MEDIUM

**Issue:** 
- Main measurements section has 30+ fields (too many)
- Koti/Shrug measurements duplicated (ik_* prefix) - 30+ more fields
- Bottom measurements scattered across multiple sections
- No clear grouping by garment part (top, bottom, sleeves, etc.)

**Impact:** UI is overwhelming; hard to navigate; data entry errors

**Fix:** Reorganize into logical subsections (Top Measurements, Bottom Measurements, Sleeve Measurements, etc.)

---

### 6. **Conditional Field Dependencies Not Enforced**
**Severity:** MEDIUM

**Issue:**
- `workstation_screen_print` section depends on `sp == "1"` but no validation
- `sample_hand_embroider_section` depends on `hand_embroidery == "1"` but no validation
- Users can fill these sections even when conditions aren't met

**Impact:** Invalid data; confusing UI; data integrity issues

**Fix:** Add server-side validation in `before_save()` to enforce dependencies

---

### 7. **Missing Required Field Validations**
**Severity:** MEDIUM

**Issue:**
- `category` is marked as required but is "Temporary" (should be replaced with proper category link)
- `item_name` is marked as required but is "Temporary" (should link to Item doctype)
- `sample_size` field exists but is never defined in field_order
- `status` field is read-only but manually set in code (should use docstatus instead)

**Impact:** Data quality issues; inconsistent status tracking

**Fix:** 
- Replace temporary fields with proper links
- Use docstatus (0=Draft, 1=Submitted, 2=Cancelled) instead of custom status field
- Add missing field definitions

---

### 8. **Color Management Issues**
**Severity:** MEDIUM

**Issue:**
- Hard-coded 10 color fields (color, color_2...color_10)
- `color_units` field controls visibility but doesn't validate data
- No way to add more than 10 colors
- Color names stored in cryptic `data_*` fields
- Print format expects exact field names; brittle

**Impact:** Limited to 10 colors; hard to extend; data structure inflexible

**Fix:** Consider using a child table for colors instead of hard-coded fields

---

### 9. **Workstation Checkboxes Lack Validation**
**Severity:** LOW-MEDIUM

**Issue:**
- Workstation fields (cutting, sp, me, bp, td, sewing, hand_embroidery, fb, hand_work, karchupi) are just checkboxes
- No linked workstation records
- No cost/time tracking
- No workflow enforcement

**Impact:** Cannot track workstation capacity; no resource planning

**Fix:** Consider linking to Workstation doctype; add cost/time fields

---

### 10. **Screen Print Cost Fields Are Strings**
**Severity:** MEDIUM

**Issue:**
- `cost_for_30_unit`, `cost_for_50_unit`, `cost_for_70_unit`, `cost_for_100_unit` → Type: **Data** (should be Currency)
- `frame_cost`, `process_cost`, `chemical_cost`, `print_cost` → Type: **Data** (should be Currency)

**Impact:** Cannot perform calculations; sorting broken; no currency formatting

**Fix:** Change fieldtype to Currency

---

### 11. **Missing Field: `sample_size`**
**Severity:** MEDIUM

**Issue:**
- `sample_size` is referenced in print format and field_order
- But NOT defined in fields array
- Will cause errors when accessed

**Impact:** Print format fails; data access errors

**Fix:** Add field definition for `sample_size`

---

### 12. **Inconsistent Naming Conventions**
**Severity:** LOW-MEDIUM

**Issue:**
- Mix of snake_case and abbreviated names
- Some fields use abbreviations: `fb` (Fusing & Bundling), `sp` (Screen Print), `me` (Machine Embroidery), `bp` (Block Print), `td` (Tie & Dye)
- Some use full names: `cutting`, `sewing`, `hand_embroidery`, `hand_work`
- Inconsistent prefixes: `ik_*` for Koti measurements

**Impact:** Hard to maintain; confusing for developers

**Fix:** Standardize naming (use full names or consistent abbreviations)

---

### 13. **Design No Generation Logic Issues**
**Severity:** MEDIUM

**Issue:**
- `generate_design_no()` depends on Employee abbreviation (`abbr` field)
- If Employee has no abbreviation, returns None
- No fallback mechanism
- Design no can be manually overridden, breaking auto-generation logic

**Impact:** Design numbers may not generate; inconsistent numbering

**Fix:** Add validation; ensure Employee has abbreviation; add fallback logic

---

### 14. **Fetch Field Dependency**
**Severity:** LOW

**Issue:**
- `design_no` is fetched from `designer.employee_number` but also auto-generated
- Conflict: which takes precedence?
- `designer_name` is fetched from `designer.employee_name` (redundant)

**Impact:** Confusion about which field is authoritative

**Fix:** Clarify logic; remove redundant fetch fields

---

### 15. **Missing Permissions Definition**
**Severity:** MEDIUM

**Issue:**
- Sketch Specification JSON doesn't show permissions array (truncated)
- Cannot verify role-based access control
- Likely missing permissions for Fashion Designer role

**Impact:** Security/access control issues

**Fix:** Verify and add proper permissions for all roles

---

### 16. **Dupatta Section Incomplete**
**Severity:** LOW

**Issue:**
- `dupatta_section` has only 3 fields: `dlength`, `dwidth`, `dupatta_note`
- No dupatta style, fabric, embroidery options
- Inconsistent with top/bottom detail level

**Impact:** Incomplete dupatta specifications

**Fix:** Add more dupatta-specific fields (style, fabric, embroidery, etc.)

---

### 17. **Image Management Issues**
**Severity:** MEDIUM

**Issue:**
- `image` field (Attach Image) for main design
- `attach_image` field (Image) - redundant?
- `additional_images` table with `image`, `description`, `print` fields
- `image_previews` is HTML field (read-only) - good for display but not for data
- Print format uses `table_jtfk` but doctype uses `additional_images` - MISMATCH!

**Impact:** Confusion about which image field to use; print format may fail

**Fix:** 
- Clarify image field usage
- Rename `table_jtfk` to `additional_images` in print format
- Remove redundant `attach_image` field

---

### 18. **CRITICAL: Missing Field `table_jtfk`**
**Severity:** CRITICAL

**Issue:**
- Print format references `doc.table_jtfk` for images
- But doctype defines `additional_images` instead
- `table_jtfk` is NOT in field_order or fields array
- This will cause print format to fail completely

**Impact:** Print format completely broken - cannot generate tech pack

**Fix:** Either:
1. Rename `additional_images` to `table_jtfk` in doctype, OR
2. Update print format to use `additional_images`

**Recommended:** Option 2 - update print format (better naming)

---

### 19. **Measurement Chart Mapping Issues**
**Severity:** MEDIUM

**Issue:**
- `make_measurement_chart()` maps `design_no` → `style_no`
- But Measurement Chart expects `style_no` to match exactly
- If design_no format changes, mapping breaks

**Impact:** Measurement chart creation fails

**Fix:** Add validation; ensure design_no format is consistent

---

### 20. **Cost Estimation Mapping Issues**
**Severity:** MEDIUM

**Issue:**
- `make_cost_estimation()` maps many fields
- Some mappings are unclear: `fb` → `fusing_bundling` (abbreviation to full name)
- No validation that Cost Estimation doctype has these fields
- If Cost Estimation fields change, mapping breaks

**Impact:** Cost estimation creation fails silently

**Fix:** Add validation; document field mappings; add error handling

---

## DESIGN ISSUES

### 21. **No Audit Trail for Design Changes**
**Severity:** LOW

**Issue:**
- No version control for design changes
- `amended_from` field exists but no amendment workflow
- No change log

**Impact:** Cannot track design evolution

**Fix:** Implement amendment workflow; add change tracking

---

### 22. **No Approval Workflow**
**Severity:** MEDIUM

**Issue:**
- `trigger_request_for_approval()` method exists but no workflow
- No approval status tracking
- No approval history

**Impact:** Cannot enforce design approval process

**Fix:** Implement proper workflow with approval states

---

### 23. **No Linked Documents Tracking**
**Severity:** LOW

**Issue:**
- No way to see which Cost Estimations, Measurement Charts, or PPS records are linked
- Must manually query database

**Impact:** Hard to track document relationships

**Fix:** Add child tables or links to track related documents

---

## DATA QUALITY ISSUES

### 24. **No Validation for Measurement Ranges**
**Severity:** LOW

**Issue:**
- Measurement fields accept any Float value
- No validation for realistic ranges (e.g., negative values, extremely large values)

**Impact:** Invalid data can be entered

**Fix:** Add validation rules for measurement ranges

---

### 25. **No Validation for Color Values**
**Severity:** LOW

**Issue:**
- Color fields are Color type (good) but no validation
- Can accept invalid hex codes

**Impact:** Invalid colors in print format

**Fix:** Add validation for valid hex color codes

---

## RECOMMENDATIONS

### Priority 1 (Critical - Fix Immediately)
1. **Fix `table_jtfk` vs `additional_images` mismatch** - Print format is broken
2. Add missing `sample_size` field definition
3. Fix field type mismatches (Data → Float/Currency)
4. Fix field name/label inconsistencies

### Priority 2 (High - Fix Soon)
5. Consolidate duplicate measurement fields
6. Add proper labels to `data_*` fields
7. Add server-side validation for conditional fields
8. Replace temporary fields with proper links
9. Implement proper status tracking using docstatus

### Priority 3 (Medium - Plan for Next Release)
10. Reorganize measurements into logical sections
11. Consider child table for colors instead of hard-coded fields
12. Implement approval workflow
13. Add workstation linking and cost tracking
14. Standardize naming conventions

### Priority 4 (Low - Nice to Have)
15. Add audit trail/amendment workflow
16. Add measurement validation ranges
17. Improve dupatta section
18. Add linked documents tracking

---

## SUMMARY

**Total Issues Found:** 25
- **Critical:** 1
- **High:** 4
- **Medium:** 12
- **Low:** 8

**Main Problem Areas:**
1. Field naming and type inconsistencies
2. Duplicate/conflicting fields
3. Print format/doctype mismatch (CRITICAL)
4. Missing field definitions
5. Lack of validation and workflow

**Estimated Effort to Fix:** 40-60 hours

---

## QUICK REFERENCE: Field Issues by Category

### Fields with Wrong Type (Data → Float/Currency)
- komor, high_hip, low_hip, thigh_uru, knee_x2, leg_opening_x2
- elasticrubber_width, beltloop_width, wb_to_pocket_opening, pocket_depth
- hand_embroider, sample, time, rate
- cost_for_30_unit, cost_for_50_unit, cost_for_70_unit, cost_for_100_unit
- frame_cost, process_cost, chemical_cost, print_cost

### Fields with Mismatched Names/Labels
- cf_length, cb_length, full_length_arm, pocket_placket, shoulder_drop, shoulder, armhole, elbow, cuff_length, cuff_width, cuff_opening, pocket_length

### Cryptic/Unlabeled Fields
- data_xmgl, data_ryzm, data_muzc, data_lfwb, data_hnjh, data_zsdd, data_uxrz, data_mnat, data_wptw, data_znsh

### Duplicate Fields
- waist_circumstance ↔ komor
- bust ↔ high_hip
- upper_hip ↔ low_hip
- pocket_width (appears twice)
- shoulder_tip_to_side_waist ↔ shoulder_tip_to_pocket_starting

### Temporary/Placeholder Fields
- category (marked as "Temporary")
- item_name (marked as "Temporary")
