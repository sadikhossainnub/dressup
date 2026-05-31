# Body Artwork Colors - Dynamic Color Fields Feature

## Overview
Body Artwork Color এর নিচে dynamic color fields যোগ করা হয়েছে। যখন user Body Artwork Color select করে, তখন সেই অনুযায়ী color fields দেখা যায়।

---

## Feature Description

### How It Works
```
Body Artwork Color: [Select 1-10]
                    ↓
            (Based on selection)
                    ↓
Body Artwork Color 1: [Color Picker]
Body Artwork Color 2: [Color Picker]
Body Artwork Color 3: [Color Picker]
... (up to selected number)
```

### Example
```
If Body Artwork Color = 3:
├─ Body Artwork Color 1: [Color Picker] ✓ Visible
├─ Body Artwork Color 2: [Color Picker] ✓ Visible
├─ Body Artwork Color 3: [Color Picker] ✓ Visible
├─ Body Artwork Color 4: [Color Picker] ✗ Hidden
├─ Body Artwork Color 5: [Color Picker] ✗ Hidden
├─ Body Artwork Color 6: [Color Picker] ✗ Hidden
├─ Body Artwork Color 7: [Color Picker] ✗ Hidden
├─ Body Artwork Color 8: [Color Picker] ✗ Hidden
├─ Body Artwork Color 9: [Color Picker] ✗ Hidden
└─ Body Artwork Color 10: [Color Picker] ✗ Hidden
```

---

## Fields Added

### Body Artwork Section
- **Section Name:** `body_artwork_section`
- **Label:** Body Artwork Colors
- **Purpose:** Organize body artwork color fields

### Body Artwork Color (Selector)
- **Field Name:** `body_artwork_color`
- **Type:** Select
- **Label:** Body Artwork Color
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Purpose:** Select how many body artwork colors to use

### Body Artwork Color Fields (1-10)
- **Field Names:** `body_artwork_color_1` to `body_artwork_color_10`
- **Type:** Color (Hex Color Picker)
- **Labels:** Body Artwork Color 1 to Body Artwork Color 10
- **Visibility:** Depends on `body_artwork_color` value
- **Purpose:** Define actual colors for body artwork

### Column Breaks
- **`column_break_body_art_1`** - After Color 4
- **`column_break_body_art_2`** - After Color 8
- **Purpose:** 2-column layout for better UI

---

## Field Dependencies

### Visibility Logic
```
body_artwork_color = 1  → Show: body_artwork_color_1
body_artwork_color = 2  → Show: body_artwork_color_1, body_artwork_color_2
body_artwork_color = 3  → Show: body_artwork_color_1 to body_artwork_color_3
body_artwork_color = 4  → Show: body_artwork_color_1 to body_artwork_color_4
body_artwork_color = 5  → Show: body_artwork_color_1 to body_artwork_color_5
body_artwork_color = 6  → Show: body_artwork_color_1 to body_artwork_color_6
body_artwork_color = 7  → Show: body_artwork_color_1 to body_artwork_color_7
body_artwork_color = 8  → Show: body_artwork_color_1 to body_artwork_color_8
body_artwork_color = 9  → Show: body_artwork_color_1 to body_artwork_color_9
body_artwork_color = 10 → Show: body_artwork_color_1 to body_artwork_color_10
```

### Depends_on Formula
```
body_artwork_color_1: depends_on: "eval:doc.body_artwork_color >= 1"
body_artwork_color_2: depends_on: "eval:doc.body_artwork_color >= 2"
body_artwork_color_3: depends_on: "eval:doc.body_artwork_color >= 3"
... and so on
```

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   BODY ARTWORK COLORS SECTION                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Body Artwork Color: [Select 1-10]                                     │
│                                                                         │
│  ┌─ Color Selection (2 Columns) ────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  Body Artwork Color 1: [Color Picker]  Body Artwork Color 6: [CP]  │
│  │  Body Artwork Color 2: [Color Picker]  Body Artwork Color 7: [CP]  │
│  │  Body Artwork Color 3: [Color Picker]  Body Artwork Color 8: [CP]  │
│  │  Body Artwork Color 4: [Color Picker]  Body Artwork Color 9: [CP]  │
│  │  Body Artwork Color 5: [Color Picker]  Body Artwork Color 10:[CP]  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Structure

### Example Data
```json
{
  "body_artwork_color": "3",
  "body_artwork_color_1": "#ff0000",    // Red
  "body_artwork_color_2": "#00ff00",    // Green
  "body_artwork_color_3": "#0000ff",    // Blue
  "body_artwork_color_4": null,
  "body_artwork_color_5": null,
  "body_artwork_color_6": null,
  "body_artwork_color_7": null,
  "body_artwork_color_8": null,
  "body_artwork_color_9": null,
  "body_artwork_color_10": null
}
```

---

## Integration Points

### JavaScript (sketch_specification.js)
Need to add/update:
```javascript
// Toggle body artwork color fields based on selection
var toggle_body_artwork_colors = function (frm) {
  let count = parseInt(frm.doc.body_artwork_color) || 0;
  
  for (let i = 1; i <= 10; i++) {
    frm.toggle_display(`body_artwork_color_${i}`, i <= count);
  }
};

// Call on form refresh and when body_artwork_color changes
frappe.ui.form.on('Sketch Specification', {
  refresh: function (frm) {
    toggle_body_artwork_colors(frm);
  },
  body_artwork_color: function (frm) {
    toggle_body_artwork_colors(frm);
  }
});
```

### Print Format (sketch_tech_pack.html)
Need to update:
```html
<!-- Display body artwork colors based on selection -->
{% if doc.body_artwork_color %}
  <div class="body-artwork-colors">
    {% for i in range(1, doc.body_artwork_color|int + 1) %}
      <div class="color-item">
        <div class="color-swatch" style="background-color: {{ doc.get('body_artwork_color_' ~ i) }}"></div>
        <div class="color-label">Body Artwork Color {{ i }}</div>
      </div>
    {% endfor %}
  </div>
{% endif %}
```

---

## Usage Example

### Step 1: Select Number of Colors
```
Body Artwork Color: [Select] → Choose "3"
```

### Step 2: Color Fields Appear
```
Body Artwork Color 1: [Color Picker] → Select Red (#ff0000)
Body Artwork Color 2: [Color Picker] → Select Green (#00ff00)
Body Artwork Color 3: [Color Picker] → Select Blue (#0000ff)
```

### Step 3: Save
```
Document saved with 3 body artwork colors
```

### Step 4: Print
```
Tech pack PDF shows 3 body artwork color swatches
```

---

## Advantages

✅ **Dynamic UI** - Only shows relevant color fields
✅ **Clean Interface** - No clutter from unused fields
✅ **User-Friendly** - Intuitive color selection
✅ **Flexible** - Can select 1-10 colors
✅ **Organized** - Separate section for body artwork colors
✅ **Scalable** - Easy to extend to other artwork types

---

## Similar Features

Same feature structure applied to:
- **Koti Artwork Colors** (koti_artwork_section)
- **Bottom Artwork Colors** (bottom_artwork_section)
- **Dupatta Artwork Colors** (dupatta_artwork_section)

Each has its own section with dynamic color fields.

---

## Field Count Summary

| Section | Fields | Type |
|---------|--------|------|
| Body Artwork Colors | 12 | 1 Select + 10 Color + 2 Column Break |
| Koti Artwork Colors | 2 | 1 Select (expandable) |
| Bottom Artwork Colors | 2 | 1 Select (expandable) |
| Dupatta Artwork Colors | 2 | 1 Select (expandable) |

---

## Next Steps

1. **Update JavaScript** (sketch_specification.js)
   - Add `toggle_body_artwork_colors()` function
   - Call on form refresh and field change

2. **Update Print Format** (sketch_tech_pack.html)
   - Add body artwork color display logic
   - Test color swatch rendering

3. **Testing**
   - Test field visibility toggle
   - Test color selection
   - Test print format output

4. **Extend to Other Artwork Types**
   - Apply same pattern to Koti, Bottom, Dupatta
   - Add color fields for each

---

## Technical Details

### Depends_on Syntax
```
depends_on: "eval:doc.body_artwork_color >= 1"
```
This means: Show this field only if `body_artwork_color` >= 1

### Why >= Instead of ==
- `>=` allows showing fields even if user changes selection
- `==` would hide fields if user changes selection
- `>=` is more user-friendly

### Column Breaks
- After Color 4: `column_break_body_art_1`
- After Color 8: `column_break_body_art_2`
- Creates 2-column layout for better UI

---

## Troubleshooting

### Fields Not Showing
- Check `depends_on` formula is correct
- Verify `body_artwork_color` value is set
- Clear browser cache and refresh

### Colors Not Saving
- Check field names are correct
- Verify field types are Color
- Check database permissions

### Print Format Issues
- Verify field names in template
- Check color values are valid hex codes
- Test with sample data

---

## References

- **Main File:** sketch_specification.json
- **JavaScript:** sketch_specification.js
- **Print Format:** sketch_tech_pack.html
- **Documentation:** BODY_ARTWORK_COLORS_FEATURE.md
