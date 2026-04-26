# /public/media — hero assets

## hero-bg.mp4

The cinematic hero background video for the landing page (`/`). Generated via Midjourney by the user.

**Specs (recommended):**
- Format: MP4 (H.264) for max browser compatibility; consider WebM/AV1 as additional source for smaller bundle
- Resolution: 1920×1080 minimum; 2560×1440 ideal
- Duration: 6–10s loop (the landing component handles the seamless loop with crossfade)
- Aspect: 16:9 cover; the landing applies `object-fit: cover`
- Audio: muted (browser autoplay requires it)
- Color: works in any palette — landing applies `hue-rotate(70deg) saturate(1.6)` to push everything green

## Fallback behavior

If `hero-bg.mp4` is missing or fails to load, the landing component (`web/components/landing.tsx` → `CinematicHero`) catches the `onError` event and removes the `<video>` element. The hero falls back gracefully to:
- Vertical dark gradient (top-to-bottom fade)
- Radial green glow (left-center)

So the landing renders fine without the video — just less cinematic.

## To add the asset

```
cp ~/Downloads/midjourney-hero.mp4 web/public/media/hero-bg.mp4
```

Then refresh the dev server. No code changes needed.
