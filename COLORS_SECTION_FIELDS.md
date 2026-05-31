# Colors Section - Field List

## Overview
Colors section এ নিম্নলিখিত fields রয়েছে:

---

## Color Selection Fields (10 Colorways)

### Color 1
- **Field Name:** `color`
- **Type:** Color
- **Label:** Color
- **Description:** প্রথম রঙ নির্বাচন করুন

### Color 2
- **Field Name:** `color_2`
- **Type:** Color
- **Label:** Color 2

### Color 3
- **Field Name:** `color_3`
- **Type:** Color
- **Label:** Color 3

### Color 4
- **Field Name:** `color_4`
- **Type:** Color
- **Label:** Color 4

### Color 5
- **Field Name:** `color_5`
- **Type:** Color
- **Label:** Color 5

### Color 6
- **Field Name:** `color_6`
- **Type:** Color
- **Label:** Color 6

### Color 7
- **Field Name:** `color_7`
- **Type:** Color
- **Label:** Color 7

### Color 8
- **Field Name:** `color_8`
- **Type:** Color
- **Label:** Color 8

### Color 9
- **Field Name:** `color_9`
- **Type:** Color
- **Label:** Color 9

### Color 10
- **Field Name:** `color_10`
- **Type:** Color
- **Label:** Color 10

---

## Color Management Fields

### Color Units (Colorways Count)
- **Field Name:** `color_units`
- **Type:** Select
- **Label:** Color Units
- **Options:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- **Description:** কতটি রঙ ব্যবহার করা হবে তা নির্বাচন করুন

### Color Description
- **Field Name:** `color_description`
- **Type:** Small Text
- **Label:** Color Description
- **Description:** রঙের বিস্তারিত বর্ণনা

---

## Artwork Color Selection (By Garment Part)

### Body Artwork Color
- **Field Name:** `body_artwork_color`
- **Type:** Select
- **Label:** Body Artwork Color
- **Options:** 1-10 (রঙ নম্বর অনুযায়ী)
- **Description:** শরীরের আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

### Koti Artwork Color
- **Field Name:** `koti_artwork_color`
- **Type:** Select
- **Label:** Koti Artwork Color
- **Options:** 1-10
- **Description:** কোটির আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

### Bottom Artwork Color
- **Field Name:** `bottom_artwork_color`
- **Type:** Select
- **Label:** Bottom Artwork Color
- **Options:** 1-10
- **Description:** নিচের অংশের আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

### Dupatta Artwork Color
- **Field Name:** `dupatta_artwork_color`
- **Type:** Select
- **Label:** Dupatta Artwork Color
- **Options:** 1-10
- **Description:** দুপাটার আর্টওয়ার্ক কোন রঙে প্রিন্ট করবেন

---

## Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│                    COLORS SECTION                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Color Units: [Select 1-10]                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Color 1: [Color Picker]  Color 2: [Color Picker]│   │
│  │ Color 3: [Color Picker]  Color 4: [Color Picker]│   │
│  │ Color 5: [Color Picker]  Color 6: [Color Picker]│   │
│  │ Color 7: [Color Picker]  Color 8: [Color Picker]│   │
│  │ Color 9: [Color Picker]  Color 10: [Color Picker]   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Color Description: [Text Area]                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Body Artwork Color: [Select 1-10]               │   │
│  │ Koti Artwork Color: [Select 1-10]               │   │
│  │ Bottom Artwork Color: [Select 1-10]             │   │
│  │ Dupatta Artwork Color: [Select 1-10]            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Total Fields in Colors Section

| Category | Count | Fields |
|----------|-------|--------|
| Color Selection | 10 | color, color_2 to color_10 |
| Color Management | 2 | color_units, color_description |
| Artwork Color Selection | 4 | body_artwork_color, koti_artwork_color, bottom_artwork_color, dupatta_artwork_color |
| **Total** | **16** | - |

---

## Usage Notes

1. **Color Units** - এটি নির্ধারণ করে কতটি রঙ ব্যবহার করা হবে
2. **Color Selection** - প্রতিটি রঙ একটি hex color picker দিয়ে নির্বাচন করা যায়
3. **Color Description** - রঙের নাম বা বর্ণনা লিখুন (যেমন: "Navy Blue", "Maroon", ইত্যাদি)
4. **Artwork Color Selection** - প্রতিটি garment part এর জন্য কোন রঙে আর্টওয়ার্ক প্রিন্ট করবেন তা নির্বাচন করুন

---

## Integration with Print Format

Colors section এর data print format এ ব্যবহৃত হয়:
- Color swatches প্রদর্শন করা হয়
- Artwork color information দেখানো হয়
- Color names/descriptions প্রিন্ট করা হয়
