# Progress Tracker - Quick Reference Card

## 🎯 At a Glance

**What:** Enhanced HTML table-based progress trackers  
**Where:** Tutorial README files (00-03 updated, template available for 04-09)  
**Why:** Better UX, more information, professional appearance

---

## 📊 Status Badge Reference

| Badge | Meaning | When to Use |
|-------|---------|-------------|
| ![Complete](https://img.shields.io/badge/✓-COMPLETE-success?style=flat-square) | Tutorial finished | User has completed this tutorial |
| ![Current](https://img.shields.io/badge/●-CURRENT-blue?style=flat-square) | Currently working | User is on this tutorial now |
| ![Todo](https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square) | Not yet started | Future tutorials |

---

## 🎨 Visual Elements

### Current Tutorial Highlighting
```html
<tr style="background-color: #e8f5e9;">
  <td align="center"><strong>02</strong></td>
  <td><strong>👉 <a href="...">🥈 Silver Layer</a></strong></td>
  <td align="center"><img src="...CURRENT..." alt="Current"></td>
  ...
</tr>
```

**Key Features:**
- Light green background (`#e8f5e9`)
- Bold tutorial number and name
- 👉 pointing hand emoji
- Blue "CURRENT" badge

---

## 🔄 How to Update Status

### Moving from Tutorial 01 → Tutorial 02

**Step 1:** Change Tutorial 01 from CURRENT to COMPLETE
```html
<!-- OLD -->
<tr style="background-color: #e8f5e9;">
  <td align="center"><strong>01</strong></td>
  <td><strong>👉 <a href="...">🥉 Bronze Layer</a></strong></td>
  <td align="center"><img src="...●-CURRENT-blue..." alt="Current"></td>

<!-- NEW -->
<tr>
  <td align="center">01</td>
  <td><a href="...">🥉 Bronze Layer</a></td>
  <td align="center"><img src="...✓-COMPLETE-success..." alt="Complete"></td>
```

**Step 2:** Change Tutorial 02 from TODO to CURRENT
```html
<!-- OLD -->
<tr>
  <td align="center">02</td>
  <td><a href="...">🥈 Silver Layer</a></td>
  <td align="center"><img src="...○-TODO-lightgrey..." alt="Todo"></td>

<!-- NEW -->
<tr style="background-color: #e8f5e9;">
  <td align="center"><strong>02</strong></td>
  <td><strong>👉 <a href="...">🥈 Silver Layer</a></strong></td>
  <td align="center"><img src="...●-CURRENT-blue..." alt="Current"></td>
```

---

## 📋 Tutorial List Reference

| # | Emoji | Name | Time | Level |
|---|-------|------|------|-------|
| 00 | ⚙️ | Environment Setup | 45-60 min | ⭐ |
| 01 | 🥉 | Bronze Layer | 60-90 min | ⭐ |
| 02 | 🥈 | Silver Layer | 60-90 min | ⭐⭐ |
| 03 | 🥇 | Gold Layer | 90-120 min | ⭐⭐ |
| 04 | ⚡ | Real-Time Analytics | 90-120 min | ⭐⭐⭐ |
| 05 | 📊 | Direct Lake & Power BI | 60-90 min | ⭐⭐ |
| 06 | 🔄 | Data Pipelines | 60-90 min | ⭐⭐ |
| 07 | 🛡️ | Governance & Purview | 60-90 min | ⭐⭐ |
| 08 | 🔄 | Database Mirroring | 60-90 min | ⭐⭐ |
| 09 | 🤖 | Advanced AI/ML | 90-120 min | ⭐⭐⭐ |

---

## 🔗 Badge URLs

### Complete Badge
```
https://img.shields.io/badge/✓-COMPLETE-success?style=flat-square
```

### Current Badge
```
https://img.shields.io/badge/●-CURRENT-blue?style=flat-square
```

### Todo Badge
```
https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square
```

---

## 📁 File Locations

### Updated Files
- `tutorials/00-environment-setup/README.md`
- `tutorials/01-bronze-layer/README.md`
- `tutorials/02-silver-layer/README.md`
- `tutorials/03-gold-layer/README.md`

### Documentation
- `tutorials/PROGRESS_TRACKER_TEMPLATE.md` - Full template
- `tutorials/PROGRESS_TRACKER_ENHANCEMENTS_SUMMARY.md` - Overview
- `tutorials/PROGRESS_TRACKER_VISUAL_REFERENCE.md` - Examples
- `tutorials/PROGRESS_TRACKER_BEFORE_AFTER.md` - Comparison
- `tutorials/PROGRESS_TRACKER_QUICK_REFERENCE.md` - This file

---

## 🛠️ Common Tasks

### Add New Tutorial
1. Copy a row from the template
2. Update tutorial number (10, 11, etc.)
3. Update tutorial name and link
4. Set status badge to TODO
5. Add duration and difficulty

### Change Difficulty
```html
⭐ Beginner
⭐⭐ Intermediate
⭐⭐⭐ Advanced
```

### Update Duration
```html
<td align="center">45-60 min</td>
<td align="center">60-90 min</td>
<td align="center">90-120 min</td>
```

---

## 🎯 Design Decisions

| Decision | Reason |
|----------|--------|
| **HTML Tables** | Better control over styling, responsive |
| **Shields.io Badges** | Professional, GitHub ecosystem standard |
| **Green Background** | Light, non-intrusive highlight |
| **5 Columns** | Optimal information density |
| **All 10 Tutorials** | Complete learning path visibility |
| **Clickable Links** | Reduce navigation friction |

---

## 📱 Responsive Breakpoints

| Screen Size | Behavior |
|-------------|----------|
| **> 1024px** | Full table, all columns visible |
| **768-1024px** | Full table, may wrap slightly |
| **480-768px** | Compressed columns, horizontal scroll |
| **< 480px** | Horizontal scroll, minimum widths maintained |

---

## ♿ Accessibility Checklist

- ✅ Semantic HTML (`<table>`, `<thead>`, `<tbody>`)
- ✅ Alt text on all images (badges)
- ✅ Proper link text (not "click here")
- ✅ Color contrast meets WCAG AA
- ✅ Keyboard navigable (all links)
- ✅ Screen reader friendly

---

## 🔍 Troubleshooting

### Badge Not Displaying
**Issue:** Badge URL broken or incorrect  
**Fix:** Verify URL matches one of the three badge URLs above

### Background Color Not Showing
**Issue:** Inline style missing  
**Fix:** Add `style="background-color: #e8f5e9;"` to `<tr>` tag

### Links Not Working
**Issue:** Incorrect relative path  
**Fix:** Use `../XX-tutorial-name/README.md` format

### Table Not Responsive
**Issue:** Fixed widths on mobile  
**Fix:** Use percentage widths (`width="10%"`) not pixel widths

---

## 💡 Pro Tips

1. **Consistency:** Use the template for all tutorials
2. **Testing:** View on mobile before committing
3. **Maintenance:** Update all trackers when adding tutorials
4. **Documentation:** Keep this reference card updated
5. **Git Diff:** Check changes before committing

---

## 📞 Need Help?

Refer to these detailed docs:
- **Implementation:** `PROGRESS_TRACKER_TEMPLATE.md`
- **Visual Examples:** `PROGRESS_TRACKER_VISUAL_REFERENCE.md`
- **Comparison:** `PROGRESS_TRACKER_BEFORE_AFTER.md`
- **Summary:** `PROGRESS_TRACKER_ENHANCEMENTS_SUMMARY.md`

---

**Quick Reference Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Status:** ✅ Complete
