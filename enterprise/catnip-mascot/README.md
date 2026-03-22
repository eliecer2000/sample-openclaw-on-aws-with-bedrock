# Catnip AI — Free Cat Mascot Kit

> Originally designed for PitchShow's AI chat interface.
> Line-art style, pure SVG, MIT/Apache 2.0. Free to use.

---

## Files

| File | Description |
|------|-------------|
| `cat-icon.svg` | Static icon, transparent bg, 256×256 |
| `catnip-preview.html` | Live preview with all states + code snippets |

---

## SVG (copy-paste)

```svg
<svg viewBox="0 0 48 48" width="28" height="28" fill="none"
     stroke="#e5e5e5" stroke-width="2.2" stroke-linecap="round">
  <path d="M12,20 Q10,8 16,14"/>
  <path d="M36,20 Q38,8 32,14"/>
  <ellipse cx="24" cy="27" rx="15" ry="13"/>
  <circle cx="18" cy="26" r="2.2" fill="#e5e5e5" stroke="none"/>
  <circle cx="30" cy="26" r="2.2" fill="#e5e5e5" stroke="none"/>
  <path d="M23,30 L24,31.5 L25,30" stroke-width="1.5"/>
  <path d="M22,32.5 Q24,34 26,32.5" stroke-width="1.2"/>
  <line x1="4"  y1="26" x2="12" y2="28" stroke-width="1" opacity=".6"/>
  <line x1="5"  y1="30" x2="12" y2="30" stroke-width="1" opacity=".6"/>
  <line x1="44" y1="26" x2="36" y2="28" stroke-width="1" opacity=".6"/>
  <line x1="43" y1="30" x2="36" y2="30" stroke-width="1" opacity=".6"/>
</svg>
```

## Customise stroke color

- White on dark: `stroke="#e5e5e5"` (default)
- Purple AI: `stroke="#a78bfa"`
- Dark on light: `stroke="#1a1a2c"`
- Custom: replace `stroke` value with any CSS color

## CSS Animations

```css
/* Idle: slow blink */
.cat-eyes {
  animation: catBlink 5s ease-in-out infinite;
  transform-origin: center 26px;
  transform-box: fill-box;
}
/* Working: head wobble + fast double blink */
.cat-working { animation: catTilt 1.5s cubic-bezier(.4,0,.2,1) infinite; }
.cat-working .cat-eyes { animation: catBlinkFast 2s cubic-bezier(.4,0,.2,1) infinite; }

@keyframes catBlink {
  0%,38%,42%,100% { transform: scaleY(1); }
  40% { transform: scaleY(0.05); }
}
@keyframes catBlinkFast {
  0%,35%,42%,100% { transform: scaleY(1); }
  38% { transform: scaleY(0.05); }
  70%,74% { transform: scaleY(1); }
  72% { transform: scaleY(0.05); }
}
@keyframes catTilt {
  0%,100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}
```

## React component

```tsx
interface Props { size?: number; animate?: 'idle' | 'working' | 'none' }
function CatIcon({ size = 28, animate = 'idle' }: Props) {
  const s = '#e5e5e5';
  return (
    <svg viewBox="0 0 48 48" width={size} height={size} fill="none"
         stroke={s} strokeWidth={2.2} strokeLinecap="round">
      <path d="M12,20 Q10,8 16,14"/>
      <path d="M36,20 Q38,8 32,14"/>
      <ellipse cx="24" cy="27" rx="15" ry="13"/>
      <g className={animate === 'idle' ? 'cat-eyes' : animate === 'working' ? 'cat-eyes-fast' : ''}>
        <circle cx="18" cy="26" r="2.2" fill={s} stroke="none"/>
        <circle cx="30" cy="26" r="2.2" fill={s} stroke="none"/>
      </g>
      <path d="M23,30 L24,31.5 L25,30" strokeWidth={1.5}/>
      <path d="M22,32.5 Q24,34 26,32.5" strokeWidth={1.2}/>
      <line x1="4"  y1="26" x2="12" y2="28" strokeWidth={1} opacity={0.6}/>
      <line x1="5"  y1="30" x2="12" y2="30" strokeWidth={1} opacity={0.6}/>
      <line x1="44" y1="26" x2="36" y2="28" strokeWidth={1} opacity={0.6}/>
      <line x1="43" y1="30" x2="36" y2="30" strokeWidth={1} opacity={0.6}/>
    </svg>
  );
}
```

---

## License

Apache 2.0 — free to use commercially and personally.
Credit appreciated but not required: *"Catnip AI by Wu_JiaDe / PitchShow"*
