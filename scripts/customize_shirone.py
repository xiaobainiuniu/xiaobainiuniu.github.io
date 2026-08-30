from __future__ import annotations

import re
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
site = root / "_shirone"


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected text not found in {path}: {old[:80]}")
    path.write_text(text.replace(old, new), encoding="utf-8")


# Site identity
site_cfg = site / "src/config/siteConfig.ts"
replace(site_cfg, 'site: "https://shirone.mysqil.com/",', 'site: "https://xiaobainiuniu.github.io/",')
replace(site_cfg, 'title: "Shirone",', 'title: "niuniu",')
replace(site_cfg, 'subtitle: "A Material 3 anime blog",', 'subtitle: "Computer Vision · Deep Learning · AI Agent",')
replace(site_cfg, 'lang: "en",', 'lang: "zh_CN",')
replace(site_cfg, '\t\ttitle: "Shirone",', '\t\ttitle: "niuniu",')

text = site_cfg.read_text(encoding="utf-8")
text = re.sub(
    r'\t\t\tsubtitle: \[.*?\n\t\t\t\],\n\t\t\ttypewriter:',
    '\t\t\tsubtitle: [\n'
    '\t\t\t\t"Computer Vision · Deep Learning",\n'
    '\t\t\t\t"Object Detection · Industrial Defect Detection",\n'
    '\t\t\t\t"LLM · RAG · AI Agent",\n'
    '\t\t\t],\n\t\t\ttypewriter:',
    text,
    flags=re.S,
)
site_cfg.write_text(text, encoding="utf-8")

# Profile
(site / "src/config/profileConfig.ts").write_text(
    '''import type { ProfileConfig } from "@/types/config";\n'
    'import { withUserConfig } from "../utils/config-overlay.ts";\n\n'
    'export const profileConfig: ProfileConfig = withUserConfig("profile", {\n'
    '\tavatar: "/avatar.png",\n'
    '\tname: "niuniu",\n'
    '\tbio: "Computer Vision · Deep Learning · AI Agent",\n'
    '\tlinks: [\n'
    '\t\t{\n'
    '\t\t\tname: "GitHub",\n'
    '\t\t\ticon: "fa6-brands:github",\n'
    '\t\t\turl: "https://github.com/xiaobainiuniu",\n'
    '\t\t},\n'
    '\t],\n'
    '});\n'''.replace("'\n    '", ""),
    encoding="utf-8",
)

# Navigation: Home / Projects / Skills / GitHub only
nav_cfg = site / "src/config/navBarConfig.ts"
nav = nav_cfg.read_text(encoding="utf-8")
nav = nav.replace('url: "https://github.com/LyraVoid/Shirone",', 'url: "https://github.com/xiaobainiuniu",')
start = nav.index("const defaultNavBarConfig: NavBarConfig = {")
end = nav.index('/** `$t:home`', start)
nav = nav[:start] + '''const defaultNavBarConfig: NavBarConfig = {\n\tlinks: [\n\t\tLinkPresets.Home,\n\t\t...(projectsConfig.enable ? [LinkPresets.Projects] : []),\n\t\t...(skillsConfig.enable ? [LinkPresets.Skills] : []),\n\t\tLinkPresets.GitHub,\n\t],\n};\n\n''' + nav[end:]
nav_cfg.write_text(nav, encoding="utf-8")

# Projects
(site / "src/data/projects.ts").write_text(
    '''import type { ProjectItem } from "@/types/projectsConfig";\n\n'
    'export const projectsData: ProjectItem[] = [\n'
    '\t{\n'
    '\t\tkey: "auto-clicker",\n'
    '\t\ttitle: "Auto Clicker",\n'
    '\t\tsummary: "Windows 连点工具，支持多显示器取点、全局热键、倒计时与后台点击。",\n'
    '\t\tcategory: "desktop",\n'
    '\t\tphase: "building",\n'
    '\t\ttechnologies: ["Rust", "egui", "WinAPI"],\n'
    '\t\ticon: "material-symbols:mouse-outline-rounded",\n'
    '\t\tfeatured: true,\n'
    '\t\trepository: "https://github.com/xiaobainiuniu/auto-clicker",\n'
    '\t\tyear: "2026",\n'
    '\t},\n'
    '\t{\n'
    '\t\tkey: "paste-image-as-file",\n'
    '\t\ttitle: "PasteImageAsFile",\n'
    '\t\tsummary: "在 Windows 资源管理器中直接将剪贴板图片粘贴为 PNG 文件。",\n'
    '\t\tcategory: "desktop",\n'
    '\t\tphase: "building",\n'
    '\t\ttechnologies: ["C++17", "Win32", "CMake"],\n'
    '\t\ticon: "material-symbols:image-outline-rounded",\n'
    '\t\tfeatured: true,\n'
    '\t\trepository: "https://github.com/xiaobainiuniu/PasteImageAsFile",\n'
    '\t\tyear: "2026",\n'
    '\t},\n'
    '];\n\n'
    'export function getProjectsList(): ProjectItem[] {\n'
    '\treturn projectsData;\n'
    '}\n'''.replace("'\n    '", ""),
    encoding="utf-8",
)

# Project categories
projects_cfg = site / "src/config/projectsConfig.ts"
ptext = projects_cfg.read_text(encoding="utf-8")
ptext = re.sub(
    r'categories: \[.*?\n\t\],',
    'categories: [\n\t\t{ key: "desktop", label: "Desktop", icon: "material-symbols:desktop-windows-outline-rounded" },\n\t],',
    ptext,
    flags=re.S,
)
projects_cfg.write_text(ptext, encoding="utf-8")

# Skills
(site / "src/data/skills.ts").write_text(
    '''import type { SkillItem } from "@/types/skillsConfig";\n\n'
    'export const skillsData: SkillItem[] = [\n'
    '\t{ name: "Python", icon: "simple-icons:python", category: "language", level: "advanced" },\n'
    '\t{ name: "Java", icon: "simple-icons:openjdk", category: "language", level: "intermediate" },\n'
    '\t{ name: "C++", icon: "simple-icons:cplusplus", category: "language", level: "intermediate" },\n'
    '\t{ name: "Rust", icon: "simple-icons:rust", category: "language", level: "intermediate" },\n'
    '\t{ name: "PyTorch", icon: "simple-icons:pytorch", category: "ai", level: "advanced" },\n'
    '\t{ name: "OpenCV", icon: "simple-icons:opencv", category: "ai", level: "advanced" },\n'
    '\t{ name: "Computer Vision", icon: "material-symbols:visibility-outline-rounded", category: "ai", level: "advanced" },\n'
    '\t{ name: "Deep Learning", icon: "material-symbols:neurology-outline-rounded", category: "ai", level: "advanced" },\n'
    '\t{ name: "Git", icon: "simple-icons:git", category: "tooling", level: "advanced" },\n'
    '\t{ name: "Docker", icon: "simple-icons:docker", category: "tooling", level: "intermediate" },\n'
    '];\n\n'
    'export function getSkillsList(): SkillItem[] {\n'
    '\treturn skillsData;\n'
    '}\n'''.replace("'\n    '", ""),
    encoding="utf-8",
)

(site / "src/config/skillsConfig.ts").write_text(
    '''import type { SkillsConfig } from "@/types/skillsConfig";\n'
    'import { withUserConfig } from "../utils/config-overlay.ts";\n\n'
    'export const skillsConfig: SkillsConfig = withUserConfig("skills", {\n'
    '\tenable: true,\n'
    '\tcategories: [\n'
    '\t\t{ key: "language", label: "Languages", icon: "material-symbols:code-rounded" },\n'
    '\t\t{ key: "ai", label: "AI / Vision", icon: "material-symbols:neurology-outline-rounded" },\n'
    '\t\t{ key: "tooling", label: "Tooling", icon: "material-symbols:construction-rounded" },\n'
    '\t],\n'
    '});\n'''.replace("'\n    '", ""),
    encoding="utf-8",
)

# Remove upstream demo posts and leave one concise index post.
posts = site / "src/content/posts"
if posts.exists():
    shutil.rmtree(posts)
posts.mkdir(parents=True, exist_ok=True)
(posts / "projects.md").write_text(
    '''---\ntitle: "Projects"\npublished: 2026-08-30\npinned: true\ndescription: "Auto Clicker · PasteImageAsFile"\ntags: ["Projects"]\ncategory: Projects\ndraft: false\n---\n\n## Auto Clicker\n\nWindows 连点工具：多显示器取点、全局热键、倒计时、后台点击。\n\n[GitHub](https://github.com/xiaobainiuniu/auto-clicker)\n\n## PasteImageAsFile\n\nWindows 工具：复制图片后，在资源管理器按 `Ctrl+V` 直接生成 PNG 文件。\n\n[GitHub](https://github.com/xiaobainiuniu/PasteImageAsFile)\n''',
    encoding="utf-8",
)

# Avatar
public = site / "public"
public.mkdir(parents=True, exist_ok=True)

print("Shirone customization complete")
