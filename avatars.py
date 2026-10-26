"""
avatars.py - three original friendly characters, drawn by code as SVG.

Pipo   a little green dinosaur that bobs along and turns its head toward you
Misi   an orange tabby cat with a star on its chest (no bow, no brand look-alikes)
Lorito a green parrot

Responsible-design choices:
* Original shapes only. Nothing copies an existing character.
* Any child can choose any character.
* Motion is gentle, slow and never flashes. It switches off for people whose
  device says "reduce motion".
* No external images, scripts or links inside the drawings.
* Characters encourage and never scold.
"""
import random

AVATARS = {
    "pipo": {"name": "Pipo", "desc": "un dinosaurio amistoso"},
    "misi": {"name": "Misi", "desc": "una gatita curiosa"},
    "lorito": {"name": "Lorito", "desc": "un loro parlanchín"},
}
MOODS = ("idle", "happy", "oops")

# what each character says (simple Spanish, always supportive)
SPEECH = {
    "greet": ["¡Hola! Soy {name}. ¡Vamos a jugar!"],
    "correct": ["¡Sí! ¡Qué bien!", "¡Lo sabía!", "¡Eso es!"],
    "retry": ["¡Tú puedes!", "¡Otra vez!", "¡Casi!"],
    "reveal": ["¡Tú puedes! La próxima vez.", "¡No pasa nada! Seguimos."],
    "final_high": ["¡Somos campeones!"],
    "final_mid": ["¡Buen trabajo! Jugamos otra vez."],
    "final_low": ["¡Seguimos practicando juntos!"],
    "rest": ["¡Buen trabajo! Descansa un poco. 🌿"],
}
MOOD_FOR = {
    "greet": "idle", "correct": "happy", "retry": "oops", "reveal": "oops",
    "final_high": "happy", "final_mid": "happy", "final_low": "idle", "rest": "idle",
}


def speech(kind, name, rng=None):
    return (rng or random).choice(SPEECH[kind]).format(name=name)


# ------------------------------------------------------------------ shared drawing bits
_STYLE = """<style>
.bob{animation:bob 1.5s ease-in-out infinite}
.turn{animation:turn 1.6s ease-out 1 forwards}
.sway{animation:sway 2.4s ease-in-out infinite}
.step1{animation:step 1.5s ease-in-out infinite}
.step2{animation:step 1.5s ease-in-out infinite reverse}
.blink{animation:blink 4s infinite;transform-box:fill-box;transform-origin:center}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
@keyframes turn{0%{transform:rotate(-14deg)}45%{transform:rotate(8deg)}100%{transform:rotate(0)}}
@keyframes sway{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(8deg)}}
@keyframes step{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}
@keyframes blink{0%,92%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
@media (prefers-reduced-motion: reduce){*{animation:none !important}}
</style>"""
_DARK = "#2c3e50"
_MOUTH = "#7b241c"


def _eyes(left_x, right_x, y, mood, iris="#2c3e50"):
    if mood == "happy":      # closed, smiling eyes
        return "".join(
            f'<path d="M{x - 7} {y + 3} Q{x} {y - 8} {x + 7} {y + 3}" stroke="{_DARK}" '
            f'stroke-width="3.5" fill="none" stroke-linecap="round"/>' for x in (left_x, right_x))
    parts = []
    for x in (left_x, right_x):
        parts.append(
            f'<g class="blink"><circle cx="{x}" cy="{y}" r="8" fill="white"/>'
            f'<circle cx="{x}" cy="{y}" r="4.2" fill="{iris}"/>'
            f'<circle cx="{x + 1.5}" cy="{y - 1.5}" r="1.4" fill="white"/></g>')
    if mood == "oops":       # gentle, worried eyebrows
        for x, sign in ((left_x, 1), (right_x, -1)):
            parts.append(
                f'<path d="M{x - 7 * sign} {y - 13} L{x + 6 * sign} {y - 16}" stroke="{_DARK}" '
                f'stroke-width="2.5" stroke-linecap="round"/>')
    return "".join(parts)


def _mouth(x, y, mood):
    if mood == "happy":
        return f'<path d="M{x - 10} {y - 1} Q{x} {y + 15} {x + 10} {y - 1} Z" fill="#c0392b"/>'
    if mood == "oops":
        return f'<ellipse cx="{x}" cy="{y + 2}" rx="4" ry="5" fill="{_MOUTH}"/>'
    return (f'<path d="M{x - 7} {y} Q{x} {y + 7} {x + 7} {y}" stroke="{_MOUTH}" '
            f'stroke-width="3" fill="none" stroke-linecap="round"/>')


# ------------------------------------------------------------------ the three characters
def _pipo(mood):
    g, dark, belly = "#58b858", "#3b9a3b", "#d6f5d6"
    return f"""
<g class="bob">
  <g class="sway" style="transform-origin:62px 128px">
    <path d="M62 116 Q20 108 12 142 Q42 142 64 140 Z" fill="{g}"/>
  </g>
  <g class="step1" style="transform-origin:86px 150px">
    <rect x="78" y="148" width="17" height="32" rx="8" fill="{dark}"/>
    <ellipse cx="86" cy="181" rx="13" ry="6" fill="{dark}"/>
  </g>
  <g class="step2" style="transform-origin:116px 150px">
    <rect x="108" y="148" width="17" height="32" rx="8" fill="{dark}"/>
    <ellipse cx="116" cy="181" rx="13" ry="6" fill="{dark}"/>
  </g>
  <ellipse cx="100" cy="128" rx="48" ry="36" fill="{g}"/>
  <ellipse cx="106" cy="138" rx="30" ry="22" fill="{belly}"/>
  <polygon points="66,100 75,80 86,98" fill="{dark}"/>
  <polygon points="88,94 99,72 110,92" fill="{dark}"/>
  <polygon points="112,96 122,78 132,100" fill="{dark}"/>
  <g class="turn" style="transform-origin:128px 112px">
    <circle cx="140" cy="84" r="30" fill="{g}"/>
    <ellipse cx="160" cy="92" rx="17" ry="13" fill="{g}"/>
    <circle cx="164" cy="86" r="2" fill="{dark}"/><circle cx="170" cy="88" r="2" fill="{dark}"/>
    <circle cx="136" cy="98" r="6" fill="#ff9aa2" opacity="0.6"/>
    {_eyes(132, 150, 76, mood)}
    {_mouth(156, 100, mood)}
  </g>
</g>"""


def _misi(mood):
    o, dark = "#f5a02a", "#c9741a"
    return f"""
<g class="bob">
  <g class="sway" style="transform-origin:136px 150px">
    <path d="M136 152 Q186 146 174 100" stroke="{o}" stroke-width="13" fill="none" stroke-linecap="round"/>
  </g>
  <ellipse cx="100" cy="142" rx="40" ry="36" fill="{o}"/>
  <ellipse cx="100" cy="152" rx="24" ry="22" fill="#fff6e5"/>
  <polygon points="100,138 104,147 114,148 106,154 109,164 100,158 91,164 94,154 86,148 96,147" fill="#f4d03f"/>
  <ellipse cx="80" cy="177" rx="14" ry="9" fill="{dark}"/>
  <ellipse cx="120" cy="177" rx="14" ry="9" fill="{dark}"/>
  <g class="turn" style="transform-origin:100px 108px">
    <polygon points="68,60 62,26 94,48" fill="{o}"/>
    <polygon points="132,60 138,26 106,48" fill="{o}"/>
    <polygon points="70,54 67,36 85,48" fill="#ffb3c1"/>
    <polygon points="130,54 133,36 115,48" fill="#ffb3c1"/>
    <circle cx="100" cy="82" r="37" fill="{o}"/>
    <path d="M100 46 L100 58 M90 48 L92 58 M110 48 L108 58" stroke="{dark}" stroke-width="3" stroke-linecap="round"/>
    <circle cx="80" cy="97" r="6" fill="#ff9aa2" opacity="0.55"/>
    <circle cx="120" cy="97" r="6" fill="#ff9aa2" opacity="0.55"/>
    {_eyes(86, 114, 78, mood, iris="#27ae60")}
    <polygon points="95,90 105,90 100,97" fill="#ff7f9d"/>
    {_mouth(100, 101, mood)}
    <path d="M66 92 L48 88 M66 98 L48 100 M134 92 L152 88 M134 98 L152 100" stroke="{_DARK}" stroke-width="1.6" stroke-linecap="round"/>
  </g>
</g>"""


def _lorito(mood):
    g, dark = "#34c77b", "#239b5c"
    return f"""
<g class="bob">
  <polygon points="92,168 78,198 98,190" fill="#e74c3c"/>
  <polygon points="108,168 124,198 102,190" fill="#3498db"/>
  <ellipse cx="100" cy="126" rx="38" ry="48" fill="{g}"/>
  <ellipse cx="106" cy="136" rx="22" ry="32" fill="#b5f1cf"/>
  <path d="M68 108 Q46 150 76 180 Q96 150 90 110 Z" fill="{dark}"/>
  <path d="M76 168 Q70 184 84 190 Q92 178 88 166 Z" fill="#e74c3c"/>
  <line x1="88" y1="172" x2="88" y2="186" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
  <line x1="112" y1="172" x2="112" y2="186" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
  <g class="turn" style="transform-origin:100px 96px">
    <ellipse cx="90" cy="38" rx="5" ry="13" fill="#e74c3c" transform="rotate(-20 90 38)"/>
    <ellipse cx="102" cy="34" rx="5" ry="14" fill="#f39c12" transform="rotate(0 102 34)"/>
    <ellipse cx="114" cy="38" rx="5" ry="13" fill="#e74c3c" transform="rotate(20 114 38)"/>
    <circle cx="100" cy="68" r="31" fill="{g}"/>
    <circle cx="82" cy="82" r="6" fill="#ff9aa2" opacity="0.55"/>
    {_eyes(90, 114, 62, mood)}
    <path d="M100 74 Q138 70 132 96 Q120 86 100 90 Z" fill="#f4d03f"/>
    <path d="M104 88 Q122 86 128 94" stroke="#d4ac0d" stroke-width="2" fill="none"/>
  </g>
</g>"""


_DRAW = {"pipo": _pipo, "misi": _misi, "lorito": _lorito}


def avatar_svg(key, mood="idle", size=140):
    """The drawing of one character in one mood, as an SVG string."""
    if key not in _DRAW:
        raise ValueError(f"Unknown character: {key}")
    if mood not in MOODS:
        raise ValueError(f"Unknown mood: {mood}")
    info = AVATARS[key]
    label = f"{info['name']}, {info['desc']}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="{size}" '
        f'height="{size}" role="img" aria-label="{label}"><title>{label}</title>'
        f"{_STYLE}{_DRAW[key](mood)}</svg>"
    )
