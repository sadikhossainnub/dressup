# Sketch Tech Pack — Full Redesign (Final Plan)

## Goal

পুরো `sketch_tech_pack` print format → **A4 Landscape**, Fabrilife-style। সব pages same header + footer।

---

## Final Page Structure

| Page | Title | Content |
|------|-------|---------|
| **1** | DESIGN PACKAGE | Front + Back Sketch + Colorway swatch |
| **2** | COMPONENT DETAILS | Bottom Front + Back (2 large images) |
| **3** | COMPONENT DETAILS | All parts (3 medium images) |
| **4** | ARTWORK DETAILS | "TOP" artwork + Print Colors |
| **5** | ARTWORK DETAILS | "BOTTOM + SLEEVE" artwork + Print Colors |
| **Last** | MEASUREMENT CHART | Full measurement table (Code, Point of Measures, S→4XL with B/I & A/I columns) |

> [!NOTE]
> **বাদ দেওয়া হচ্ছে:** Workstations badges, Screen Print details, Hand Embroidery details, Notes section — এগুলো last page-এ থাকবে না।

---

## Repeating Header (সব page-এ same)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Brand  │ DressUp      │ Style No       │ design_no │ Category Lead │       │ [LOGO] │
│ Season │ session      │ Style Desc     │ item_name │ Designer      │ name  │        │
│ Category│ category    │ No. of Colorways│color_units│ Sourcing Lead │       │        │
│ Collection│sewing_finish│ Sample Size   │           │ Concern Merch │       │        │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Repeating Footer (সব page-এ same)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Important: Confidential information belongs exclusively to DressUp  │ Page X │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## PAGE 1 — DESIGN PACKAGE

```
│ DESIGN PACKAGE                                                              │
│  ┌───────────────────┐   ┌───────────────────┐   ┌──────────────┐           │
│  │   Front Sketch    │   │   Back Sketch     │   │  Colorway-1  │           │
│  │   (doc.image)     │   │   (add_img[0])    │   │  [■ swatch]  │           │
│  │   ~40%  LARGE     │   │   ~40%  LARGE     │   │ Fabric Code: │           │
│  │                   │   │                   │   │ data_xmgl    │           │
│  └───────────────────┘   └───────────────────┘   └──────────────┘           │
│ Remarks: text_editor_noaa                                                    │
```

---

## PAGE 2 — COMPONENT DETAILS (Bottom, 2 large)

```
│ COMPONENT DETAILS                                                            │
│  ┌────────────────────────────┐   ┌────────────────────────────┐             │
│  │     Component Front        │   │     Component Back         │             │
│  │     (add_img[1])           │   │     (add_img[2])           │             │
│  │     ~50%  VERY LARGE       │   │     ~50%  VERY LARGE       │             │
│  └────────────────────────────┘   └────────────────────────────┘             │
```

> Conditional: only if `additional_images` ≥ 3

---

## PAGE 3 — COMPONENT DETAILS (All Parts, 3-column)

```
│ COMPONENT DETAILS                                                            │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │  Top Front       │   │  Bottom Front   │   │  Bottom Back    │            │
│  │  (doc.image)     │   │  (add_img[1])   │   │  (add_img[2])   │            │
│  │  ~33% width      │   │  ~33% width     │   │  ~33% width     │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
```

> Conditional: only if `additional_images` ≥ 3

---

## PAGE 4+ — ARTWORK DETAILS (Dynamic per artwork image)

```
│ ARTWORK DETAILS                                          Print Color         │
│  PRINT ARTWORK                          ┌─────────────────────────────┐      │
│  PLACEMENT PRINT                        │ ┌────────┐  Pantone name   │      │
│  {{ description }}                      │ │ Color1 │  (data_xmgl)   │      │
│                                         │ │ swatch │                 │      │
│  ┌──────────────────────────────┐       │ └────────┘                 │      │
│  │   Artwork Image              │       │ ┌────────┐  Pantone name   │      │
│  │   ~70% width, VERY LARGE    │       │ │ Color2 │  (data_ryzm)   │      │
│  │                              │       │ └────────┘                 │      │
│  └──────────────────────────────┘       │ ┌────────┐  Pantone name   │      │
│                                         │ │ Color3 │  (data_muzc)   │      │
│                                         │ └────────┘                 │      │
│                                         └─────────────────────────────┘      │
```

**Dynamic:** `additional_images[3:]` — each image gets its own ARTWORK page
- Subtitle from `img.description` (e.g. "TOP", "BOTTOM + SLEEVE")
- Same Print Color swatches on every artwork page

---

## LAST PAGE — MEASUREMENT CHART ⭐

```
│ MEASUREMENT CHART                                                            │
│                                                                              │
│ ┌──────┬──────────────────────┬───────────────┬───────────────┬──── ─── ──┐  │
│ │ Code │ Point of Measures    │ S      │ M      │ L      │ XL    │ XXL  ...│  │
│ │      │                      │ B/I│A/I│ B/I│A/I│ B/I│A/I│B/I│A/I│B/I│A/I │  │
│ ├──────┼──────────────────────┼────┼───┼────┼───┼────┼───┼───┼───┼───┼────┤  │
│ │  1   │ ½ Chest              │ 48 │   │ 50 │   │ 52 │   │ 55│   │ 58│    │  │
│ │  2   │ ½ Waist              │    │   │    │   │    │   │   │   │   │    │  │
│ │  3   │ ½ Bottom             │ 48 │   │ 50 │   │ 52 │   │ 55│   │ 58│    │  │
│ │  4   │ Total Length (HPS)   │ 68 │   │ 70 │   │ 72 │   │ 74│   │ 76│    │  │
│ │  5   │ Back Neck Width      │ 18 │   │18.5│   │ 19 │   │19.5│  │ 20│    │  │
│ │  ... │ ...                  │ ...│   │ ...│   │ ...│   │...│   │...│    │  │
│ │  15  │ Bottom & Sleeve Hem  │  2 │   │  2 │   │  2 │   │ 2 │   │ 2│    │  │
│ └──────┴──────────────────────┴────┴───┴────┴───┴────┴───┴───┴───┴───┴────┘  │
```

**Data source:** `Measurement Chart` DocType (linked via `style_no` = `doc.design_no`)

```jinja
{% set mc = frappe.get_all("Measurement Chart", 
    filters={"style_no": doc.design_no}, 
    limit=1) %}
{% if mc %}
    {% set mc_doc = frappe.get_doc("Measurement Chart", mc[0].name) %}
    {% for item in mc_doc.measurement_chart_items %}
        → Render row: item.code, item.point_of_measures, 
          item.s_b_i, item.s_a_i, item.m_b_i, item.m_a_i, 
          item.l_b_i, item.l_a_i, item.xl_b_i, item.xl_a_i, 
          item.xxl_b_i, item.xxl_a_i, item.3xl_b_i, item.3xl_a_i, 
          item.4xl_b_i, item.4xl_a_i
    {% endfor %}
{% endif %}
```

**Measurement Chart Item columns:**

| Field | Label |
|---|---|
| `code` | Code (1, 2, 3...) |
| `point_of_measures` | Point of Measures |
| `s_b_i` / `s_a_i` | S — B/I, A/I |
| `m_b_i` / `m_a_i` | M — B/I, A/I |
| `l_b_i` / `l_a_i` | L — B/I, A/I |
| `xl_b_i` / `xl_a_i` | XL — B/I, A/I |
| `xxl_b_i` / `xxl_a_i` | XXL — B/I, A/I |
| `3xl_b_i` / `3xl_a_i` | 3XL — B/I, A/I |
| `4xl_b_i` / `4xl_a_i` | 4XL — B/I, A/I |

---

## Image Index Mapping (Final)

| Index | Role | Used On |
|---|---|---|
| `doc.image` | Main front sketch | P1, P3 |
| `add_img[0]` | Back sketch | P1 |
| `add_img[1]` | Bottom/Component front | P2, P3 |
| `add_img[2]` | Bottom/Component back | P2, P3 |
| `add_img[3]` | Artwork #1 (desc: "TOP") | P4 |
| `add_img[4]` | Artwork #2 (desc: "BOTTOM + SLEEVE") | P5 |
| `add_img[5+]` | More artworks (dynamic) | P6+ |

---

## Field Mapping (Final)

| Layout Field | DocType Field |
|---|---|
| Brand | "DressUp" (hardcoded) |
| Season | `doc.session` |
| Category | `doc.category` |
| Collection | `doc.sewing_finish` |
| Style No | `doc.design_no` |
| Style Description | `doc.item_name` |
| No. of Colorways | `doc.color_units` |
| Sample Size | — (blank) |
| Category Lead | — (blank) |
| Designer | `doc.designer_name` |
| Sourcing Lead | — (blank) |
| Concern Merchant | — (blank) |
| Colorway-1 swatch | `doc.color` + `doc.data_xmgl` |
| Print Colors | `doc.color` → `doc.color_10` + data fields |
| Artwork subtitle | `additional_images[N].description` |
| Remarks | `doc.text_editor_noaa` |
| Logo | `/files/Capture.PNG` |
| Measurement data | Linked `Measurement Chart` DocType |

---

## Proposed Changes

### [MODIFY] [sketch_tech_pack.html](file:///home/sayed/frappe-bench/apps/dressup/dressup/dressup/print_format/sketch_tech_pack/sketch_tech_pack.html)

সম্পূর্ণ HTML rewrite (~600 lines):

1. **CSS** — `@page { size: A4 landscape; margin: 6mm; }`, tables, images, swatches
2. **`<thead>`** — Repeating info grid header + logo
3. **`<tfoot>`** — Repeating confidential footer
4. **Page 1** — DESIGN PACKAGE (front/back + colorway + remarks)
5. **Page 2** — COMPONENT DETAILS (2 images, conditional)
6. **Page 3** — COMPONENT DETAILS (3 images, conditional)
7. **Pages 4+** — ARTWORK DETAILS (dynamic loop `add_img[3:]`, each gets own page)
8. **Last Page** — MEASUREMENT CHART (table from linked Measurement Chart DocType)

**বাদ:** Workstations, Screen Print details, Hand Embroidery details, Notes section

---

## Conditional Page Logic

```
Page 1: Always (needs doc.image)
Page 2: if additional_images|length >= 3
Page 3: if additional_images|length >= 3
Page 4+: for each img in additional_images[3:]
Last:   if linked Measurement Chart exists
```

---

## Verification Plan

PDF download করে verify:
- ✅ A4 Landscape all pages
- ✅ P1: DESIGN PACKAGE + large images + colorway
- ✅ P2: COMPONENT DETAILS + 2 large images
- ✅ P3: COMPONENT DETAILS + 3 images
- ✅ P4: ARTWORK DETAILS TOP + print colors
- ✅ P5: ARTWORK DETAILS BOTTOM+SLEEVE + print colors  
- ✅ Last: MEASUREMENT CHART table (Code, Point of Measures, S→4XL)
- ✅ Same header/footer every page
- ✅ NO workstations/screen print/embroidery/notes
- ✅ Clean borders, professional look
