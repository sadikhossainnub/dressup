# Colors Section - Quick Reference Guide

## 📍 Location
**Images Section এর নিচে → Colors Section**

---

## 🎨 Fields at a Glance

| # | Field Name | Type | Label | Purpose |
|---|---|---|---|---|
| 1 | `color_units` | Select | Color Units | কতটি রঙ ব্যবহার করবেন (1-10) |
| 2 | `color` | Color | Color 1 | প্রথম রঙ নির্বাচন |
| 3 | `color_2` | Color | Color 2 | দ্বিতীয় রঙ নির্বাচন |
| 4 | `color_3` | Color | Color 3 | তৃতীয় রঙ নির্বাচন |
| 5 | `color_4` | Color | Color 4 | চতুর্থ রঙ নির্বাচন |
| 6 | `color_5` | Color | Color 5 | পঞ্চম রঙ নির্বাচন |
| 7 | `color_6` | Color | Color 6 | ষষ্ঠ রঙ নির্বাচন |
| 8 | `color_7` | Color | Color 7 | সপ্তম রঙ নির্বাচন |
| 9 | `color_8` | Color | Color 8 | অষ্টম রঙ নির্বাচন |
| 10 | `color_9` | Color | Color 9 | নবম রঙ নির্বাচন |
| 11 | `color_10` | Color | Color 10 | দশম রঙ নির্বাচন |
| 12 | `color_description` | Small Text | Color Description | রঙের নাম/বর্ণনা |
| 13 | `body_artwork_color` | Select | Body Artwork Color | শরীরের আর্টওয়ার্ক রঙ (1-10) |
| 14 | `koti_artwork_color` | Select | Koti Artwork Color | কোটির আর্টওয়ার্ক রঙ (1-10) |
| 15 | `bottom_artwork_color` | Select | Bottom Artwork Color | নিচের আর্টওয়ার্ক রঙ (1-10) |
| 16 | `dupatta_artwork_color` | Select | Dupatta Artwork Color | দুপাটার আর্টওয়ার্ক রঙ (1-10) |

---

## 📊 Field Count Summary

```
Total Fields: 16

Breakdown:
├─ Select Fields: 5
│  ├─ color_units
│  ├─ body_artwork_color
│  ├─ koti_artwork_color
│  ├─ bottom_artwork_color
│  └─ dupatta_artwork_color
│
├─ Color Fields: 10
│  ├─ color (Color 1)
│  ├─ color_2 to color_10
│
└─ Text Fields: 1
   └─ color_description
```

---

## 🎯 How to Use

### Step 1: Select Number of Colorways
```
Color Units: [Select 1-10]
```
এটি নির্ধারণ করে আপনি কতটি রঙ ব্যবহার করবেন।

### Step 2: Choose Colors
```
Color 1: [Color Picker] → Navy Blue
Color 2: [Color Picker] → Red
Color 3: [Color Picker] → White
... (up to 10 colors)
```
প্রতিটি রঙ একটি hex color picker দিয়ে নির্বাচন করুন।

### Step 3: Add Color Description
```
Color Description: Navy Blue, Red, White
```
রঙের নাম বা বর্ণনা লিখুন।

### Step 4: Select Artwork Colors
```
Body Artwork Color: Color 1 (Navy Blue)
Koti Artwork Color: Color 2 (Red)
Bottom Artwork Color: Color 1 (Navy Blue)
Dupatta Artwork Color: Color 3 (White)
```
প্রতিটি garment part এর জন্য কোন রঙে আর্টওয়ার্ক প্রিন্ট করবেন তা নির্বাচন করুন।

---

## 🔄 Field Dependencies

### Color Units Controls Visibility
```
color_units = 1  → Show: color
color_units = 2  → Show: color, color_2
color_units = 3  → Show: color, color_2, color_3
...
color_units = 10 → Show: color to color_10
```

### Artwork Color Selection
```
body_artwork_color options: 1-10
koti_artwork_color options: 1-10
bottom_artwork_color options: 1-10
dupatta_artwork_color options: 1-10
```

---

## 📋 Field Details

### color_units
- **Type:** Select
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Default:** (empty)
- **Required:** No
- **Visibility:** Always visible
- **Purpose:** কতটি রঙ ব্যবহার করবেন তা নির্বাচন করুন

### color (Color 1-10)
- **Type:** Color (Hex Color Picker)
- **Default:** (empty)
- **Required:** No
- **Visibility:** Depends on color_units
- **Purpose:** প্রতিটি রঙ নির্বাচন করুন
- **Example:** #1a3a52 (Navy Blue)

### color_description
- **Type:** Small Text
- **Default:** (empty)
- **Required:** No
- **Visibility:** Always visible
- **Purpose:** রঙের নাম বা বিস্তারিত বর্ণনা
- **Example:** "Navy Blue, Red, White with Gold trim"

### body_artwork_color
- **Type:** Select
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Default:** (empty)
- **Required:** No
- **Visibility:** Always visible
- **Purpose:** শরীরের আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

### koti_artwork_color
- **Type:** Select
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Default:** (empty)
- **Required:** No
- **Visibility:** Always visible
- **Purpose:** কোটির আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

### bottom_artwork_color
- **Type:** Select
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Default:** (empty)
- **Required:** No
- **Visibility:** Always visible
- **Purpose:** নিচের অংশের আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

### dupatta_artwork_color
- **Type:** Select
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Default:** (empty)
- **Required:** No
- **Visibility:** Always visible
- **Purpose:** দুপাটার আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

---

## 🎨 UI Layout

```
┌─────────────────────────────────────────────────────────┐
│                   COLORS SECTION                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Color Units: [Select 1-10]                            │
│                                                         │
│  ┌─ Color Selection ─────────────────────────────────┐ │
│  │                                                   │ │
│  │  Color 1: [#1a3a52]    Color 6: [#ffffff]        │ │
│  │  Color 2: [#ff0000]    Color 7: [#000000]        │ │
│  │  Color 3: [#ffffff]    Color 8: [#ffd700]        │ │
│  │  Color 4: [#008000]    Color 9: [#800080]        │ │
│  │  Color 5: [#ffa500]    Color 10: [#ffc0cb]       │ │
│  │                                                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Color Description: Navy Blue, Red, White, Green...    │
│                                                         │
│  ┌─ Artwork Color Selection ─────────────────────────┐ │
│  │                                                   │ │
│  │  Body Artwork Color: [1]  Koti Artwork Color: [2]│ │
│  │  Bottom Artwork Color: [1] Dupatta Artwork: [3]  │ │
│  │                                                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 💾 Data Storage

### Example Data
```json
{
  "color_units": "3",
  "color": "#1a3a52",
  "color_2": "#ff0000",
  "color_3": "#ffffff",
  "color_4": null,
  "color_5": null,
  "color_6": null,
  "color_7": null,
  "color_8": null,
  "color_9": null,
  "color_10": null,
  "color_description": "Navy Blue, Red, White",
  "body_artwork_color": "1",
  "koti_artwork_color": "2",
  "bottom_artwork_color": "1",
  "dupatta_artwork_color": "3"
}
```

---

## 🔗 Integration Points

### Print Format
- Color swatches displayed in tech pack
- Artwork color information shown
- Color descriptions printed

### JavaScript (sketch_specification.js)
- `toggle_color_fields()` - Controls color field visibility based on color_units
- `render_image_previews()` - May need update for color display

### Reports
- Color information used in design reports
- Artwork color tracking

---

## ✅ Validation Rules

### color_units
- Must be between 1-10
- Controls visibility of other color fields

### color (Color 1-10)
- Must be valid hex color code
- Format: #RRGGBB or #RGB
- Examples: #1a3a52, #fff, #ff0000

### color_description
- Free text field
- No length limit (Small Text)
- Examples: "Navy Blue", "Red with Gold trim"

### Artwork Color Selection
- Must be between 1-10
- Should match selected color_units
- Can be empty

---

## 🚀 Next Steps

1. **Update JavaScript** - Modify `toggle_color_fields()` function
2. **Update Print Format** - Use new field names
3. **Test Color Visibility** - Verify color_units controls visibility
4. **Test Artwork Colors** - Verify artwork color selection works
5. **Update Reports** - If any reports use old data_* fields
6. **Data Migration** - Migrate old data_* values to new color_name_* fields

---

## 📞 Support

For questions about Colors Section:
- Check field definitions in sketch_specification.json
- Review print format: sketch_tech_pack.html
- Check JavaScript: sketch_specification.js
- See analysis: SKETCH_SPECIFICATION_ANALYSIS.md
