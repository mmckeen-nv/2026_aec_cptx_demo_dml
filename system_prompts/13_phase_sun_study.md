# Phase — Sun Study Animation
### Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: project_prompt.md for building location and orientation*
*Version 1.0 — May 2026*
*Tool chain: Rhino 3D + RhinoMCP (C# scripting) + ffmpeg*

---

## Purpose

Produce a sun study animation showing how daylight and shadows move across
the building over a defined date and time range. Hermes drives the Rhino Sun
configurator for each computed frame, captures numbered PNGs with date/time
stamps, and compiles a finished MP4.

This is a primary demo deliverable showing the building's solar performance
and shadow behaviour across seasons and times of day.

---

## Inputs

From user interview / project_prompt.md:
- Building location (latitude, longitude)
- Building orientation (compass direction the front facade faces)
- Study date range (start date → end date)
- Study time range per day (start time → end time, local time)
- Number of days to sample between start and end date
- Frame rate (fps) for final MP4
- Playback duration per day (seconds per day in the video)
- Output resolution (width × height)
- Timezone offset (hours from UTC) and daylight saving (true/false)

## Outputs

- Numbered PNG frames: `{project}/renders/sun_study/frames_{res}/frame_NNNN.png`
- Compiled MP4: `{project}/renders/sun_study/sun_study_{res}.mp4`
- Parameter log: `{project}/renders/sun_study/sun_study_params.txt`

---

## Pre-Phase Audit Checklist

- [ ] Latitude, longitude, and timezone confirmed from project brief
- [ ] Date range confirmed (e.g. summer solstice → winter solstice)
- [ ] Time range confirmed (e.g. 06:00 → 20:00 local time)
- [ ] Number of days, frame rate, duration per day confirmed
- [ ] Output resolution confirmed
- [ ] Output folders created (silent failure if missing)
- [ ] Rhino Sun enabled and set to geographic mode

---

## Master Algorithm

### Step 1 — Collect Parameters

Confirm with the user:

```
latitude          {{lat}}          decimal degrees N (e.g. 38.4)
longitude         {{lon}}          decimal degrees W negative (e.g. -122.7)
timezone_offset   {{tz}}           hours from UTC (e.g. -8 for PST)
daylight_saving   {{dst}}          true / false
start_date        {{start_date}}   YYYY-MM-DD
end_date          {{end_date}}     YYYY-MM-DD
start_time        {{start_time}}   HH:MM local time (e.g. 06:00)
end_time          {{end_time}}     HH:MM local time (e.g. 20:00)
number_of_days    {{n_days}}       days sampled between start and end
frame_rate        {{fps}}          frames per second in output MP4
duration_per_day  {{dur}}          seconds per day in output video
resolution        {{W}}x{{H}}      output frame size in pixels
```

### Step 2 — Derive Frame Parameters

```python
frames_per_day  = frame_rate * duration_per_day
total_frames    = frames_per_day * number_of_days
time_span_mins  = (end_time - start_time).total_minutes()
time_step_mins  = time_span_mins / frames_per_day
date_span_days  = (end_date - start_date).days
date_step_days  = date_span_days / max(number_of_days - 1, 1)
```

Write `sun_study_params.txt` now, before any rendering starts:
```
Latitude: {lat}   Longitude: {lon}   Timezone: UTC{tz:+d}
Start date: {start_date}   End date: {end_date}
Start time: {start_time}   End time: {end_time}
Days: {n_days}   Frames/day: {frames_per_day}   Total: {total_frames}
Frame rate: {fps}fps   Duration/day: {dur}s
Resolution: {W}x{H}
```

### Step 3 — Configure Rhino Sun

```csharp
var doc = Rhino.RhinoDoc.ActiveDoc;
var sun = doc.Lights.Sun;
var ctx = Rhino.Render.RenderContent.ChangeContexts.Program;

sun.BeginChange(ctx);
sun.Enabled         = true;
sun.TimeZone        = {{tz}};
sun.DaylightSaving  = {{dst}};
sun.Latitude        = {{lat}};
sun.Longitude       = {{lon}};
sun.EndChange();
doc.Views.Redraw();
```

### Step 4 — Create Output Folder

```csharp
string outDir = @"{ROOT}\aa_demo_versions\{project}\renders\sun_study\frames_{W}x{H}";
System.IO.Directory.CreateDirectory(outDir);
```

**Always create the folder before the capture loop. Captures silently fail
if the folder does not exist.**

### Step 5 — Frame Capture Loop

```csharp
int frameIdx = 0;
for (int dayI = 0; dayI < nDays; dayI++) {
    // Current date for this day
    double dateFrac = (nDays > 1) ? (double)dayI / (nDays - 1) : 0;
    System.DateTime currentDate = startDate.AddDays(dateFrac * dateSpanDays);

    for (int frameI = 0; frameI < framesPerDay; frameI++) {
        // Current time for this frame
        double timeFrac = (framesPerDay > 1) ? (double)frameI / (framesPerDay - 1) : 0;
        int totalMins   = (int)(startTimeMins + timeFrac * timeSpanMins);
        int hour        = totalMins / 60;
        int minute      = totalMins % 60;

        // Set sun date and time
        var dt = new System.DateTime(
            currentDate.Year, currentDate.Month, currentDate.Day,
            hour, minute, 0);
        sun.BeginChange(ctx);
        sun.SetDateTime(dt, false);  // false = local time, not UTC
        sun.EndChange();
        doc.Views.Redraw();

        // Wait for viewport to settle (increase for higher resolutions)
        int waited = 0;
        while (waited < 150) { RhinoApp.Wait(); waited += 10; }

        // Capture frame
        var bmp = doc.Views.ActiveView
            .CaptureToBitmap(new System.Drawing.Size(W, H));

        // Embed date/time stamp
        using (var g = System.Drawing.Graphics.FromImage(bmp)) {
            float fontSize = W / 80f;
            var font   = new System.Drawing.Font("Arial", fontSize,
                             System.Drawing.FontStyle.Bold);
            var white  = new System.Drawing.SolidBrush(System.Drawing.Color.White);
            var shadow = new System.Drawing.SolidBrush(
                             System.Drawing.Color.FromArgb(160, 0, 0, 0));
            string stamp = $"{currentDate:yyyy-MM-dd}  {hour:D2}:{minute:D2}";
            float x = W * 0.02f, y = H * 0.92f;
            g.DrawString(stamp, font, shadow, x + 2, y + 2);
            g.DrawString(stamp, font, white,  x,     y);
        }

        // Save frame
        string path = System.IO.Path.Combine(outDir,
            $"frame_{frameIdx:D4}.png");
        bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png);
        frameIdx++;
    }
}
```

### Step 6 — Compile MP4

Run on the Hermes machine after all frames are captured:

```bash
ffmpeg -y \
  -framerate {fps} \
  -i "{outDir_linux}/frame_%04d.png" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  "{outDir_linux}/sun_study_{W}x{H}.mp4"
```

`outDir_linux` = SMB path e.g. `/mnt/cptx_demo/aa_demo_versions/{project}/renders/sun_study/frames_{W}x{H}`

---

## Alternative: Manual Azimuth/Altitude Mode

When the user does not specify lat/lon but sets sun positions directly in
the Rhino Sun Editor (Render → Sun or type `Sun`):

1. Tell user to set start position in Sun Editor
2. Read start azimuth/altitude
3. Tell user to set end position
4. Read end azimuth/altitude
5. Interpolate with smoothstep across total_frames

```csharp
double smoothstep(double t) => t * t * (3.0 - 2.0 * t);

// Azimuth wraparound
double azDelta = endAz - startAz;
if (azDelta >  180) azDelta -= 360;
if (azDelta < -180) azDelta += 360;

for (int i = 0; i < totalFrames; i++) {
    double t = smoothstep((double)i / (totalFrames - 1));
    sun.BeginChange(ctx);
    sun.Azimuth  = startAz  + azDelta * t;
    sun.Altitude = startAlt + (endAlt - startAlt) * t;
    sun.EndChange();
    doc.Views.Redraw();
    // wait, capture, stamp, save — same as Step 5 above
}
```

---

## Timing Reference

| Resolution | Frames | Wait/frame | Capture time | ffmpeg |
|---|---|---|---|---|
| 1080p | 180 | 150ms | ~55s | ~10s |
| 4K | 180 | 150ms | ~143s | ~30s |
| 4K | 360 | 150ms | ~275s | ~60s |
| 8K | 180 | 200ms | ~275s | ~90s |
| 8K | 360 | 200ms | ~550s | ~180s |

MCP timeout settings:
- ≤180 frames: `timeout=600`
- ≤360 frames: `timeout=900`
- 360 frames at 8K: `timeout=1200`

---

## Post-Phase Checklist

- [ ] `sun_study_params.txt` written before capture started
- [ ] All `total_frames` PNG files present in output folder
- [ ] Frame numbering is sequential with no gaps (frame_0000 … frame_NNNN)
- [ ] Date/time stamp visible and readable on each frame
- [ ] First frame shows correct start date and start time
- [ ] Last frame shows correct end date and end time
- [ ] Sun position visually tracks across sky correctly (not reversed, not stuck)
- [ ] MP4 compiled and plays at correct duration
- [ ] MP4 saved to `renders/sun_study/`

---

## ▶ REVIEW GATE — Sun Study

Present:
1. First frame, middle frame, last frame side by side (or as screenshots)
2. MP4 playback confirmation

Confirm:
- Shadow direction and angle are correct for the specified location and dates
- Day/night transitions (if included) are smooth
- Timestamp reads correctly on each frame
- Playback duration matches the specified duration per day

---

## Known Failure Modes

| Symptom | Root cause | Fix |
|---|---|---|
| Sun doesn't move | `CommitChanges()` used instead of `BeginChange/EndChange` | Replace with `BeginChange(ChangeContexts.Program)` / `EndChange()` |
| Sun jumps instead of interpolating | `SetDateTime` only — no intermediate frames | Ensure frame loop is iterating correctly |
| Azimuth goes the wrong way around | Wraparound not handled | Apply delta correction: >180 subtract 360, <-180 add 360 |
| Frames all identical | Viewport not redrawing | Call `doc.Views.Redraw()` before each capture |
| Frames dark/black | Wait too short for Rhino to settle | Increase wait to 200ms+ especially at high res |
| Output folder missing — files not saved | Folder not created before loop | Always `Directory.CreateDirectory()` before capture loop |
| ffmpeg fails | Frame path wrong or frames not on Linux mount | Verify SMB mount is live; check frame path via `ls` |
| Timestamp overlapping geometry | Font size too large | Reduce `W / 80f` denominator (e.g. `W / 100f`) |
| 8K capture freezes Rhino | Too many large captures in tight loop | Add 200ms+ wait; reduce frame count for 8K runs |
| Wrong timezone | `SetDateTime(..., true)` passes UTC not local | Use `false` for local time |

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."

Proceed to `11_phase_final_render.md` for Blender final rendering,
or return to `06_phase_detailing.md` if further Rhino work is needed.
