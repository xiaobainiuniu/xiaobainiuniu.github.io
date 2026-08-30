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


site_cfg = site / "src/config/siteConfig.ts"
replace(site_cfg, 'site: "https://shirone.mysqil.com/",', 'site: "https://xiaobainiuniu.github.io/",')
replace(site_cfg, 'title: "Shirone",', 'title: "niuniu",')
replace(site_cfg, 'subtitle: "A Material 3 anime blog",', 'subtitle: "Computer Vision · Deep Learning · AI Agent",')
replace(site_cfg, 'lang: "en",', 'lang: "zh_CN",')

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

(site / "src/config/profileConfig.ts").write_text(
    '''import type { ProfileConfig } from "@/types/config";
import { withUserConfig } from "../utils/config-overlay.ts";

export const profileConfig: ProfileConfig = withUserConfig("profile", {
\tavatar: "/avatar.png",
\tname: "niuniu",
\tbio: "Computer Vision · Deep Learning · AI Agent",
\tlinks: [
\t\t{
\t\t\tname: "GitHub",
\t\t\ticon: "fa6-brands:github",
\t\t\turl: "https://github.com/xiaobainiuniu",
\t\t},
\t],
});
''',
    encoding="utf-8",
)

nav_cfg = site / "src/config/navBarConfig.ts"
nav = nav_cfg.read_text(encoding="utf-8")
nav = nav.replace('url: "https://github.com/LyraVoid/Shirone",', 'url: "https://github.com/xiaobainiuniu",')
start = nav.index("const defaultNavBarConfig: NavBarConfig = {")
end = nav.index('/** `$t:home`', start)
nav = nav[:start] + '''const defaultNavBarConfig: NavBarConfig = {
\tlinks: [
\t\tLinkPresets.Home,
\t\t...(projectsConfig.enable ? [LinkPresets.Projects] : []),
\t\t...(skillsConfig.enable ? [LinkPresets.Skills] : []),
\t\tLinkPresets.GitHub,
\t],
};

''' + nav[end:]
nav_cfg.write_text(nav, encoding="utf-8")

(site / "src/data/projects.ts").write_text(
    '''import type { ProjectItem } from "@/types/projectsConfig";

export const projectsData: ProjectItem[] = [
\t{
\t\tkey: "auto-clicker",
\t\ttitle: "Auto Clicker",
\t\tsummary: "Windows 连点工具，支持多显示器取点、全局热键、倒计时与后台点击。",
\t\tcategory: "desktop",
\t\tphase: "building",
\t\ttechnologies: ["Rust", "egui", "WinAPI"],
\t\ticon: "material-symbols:mouse-outline-rounded",
\t\tfeatured: true,
\t\trepository: "https://github.com/xiaobainiuniu/auto-clicker",
\t\tyear: "2026",
\t},
\t{
\t\tkey: "paste-image-as-file",
\t\ttitle: "PasteImageAsFile",
\t\tsummary: "在 Windows 资源管理器中直接将剪贴板图片粘贴为 PNG 文件。",
\t\tcategory: "desktop",
\t\tphase: "building",
\t\ttechnologies: ["C++17", "Win32", "CMake"],
\t\ticon: "material-symbols:image-outline-rounded",
\t\tfeatured: true,
\t\trepository: "https://github.com/xiaobainiuniu/PasteImageAsFile",
\t\tyear: "2026",
\t},
];

export function getProjectsList(): ProjectItem[] {
\treturn projectsData;
}
''',
    encoding="utf-8",
)

projects_cfg = site / "src/config/projectsConfig.ts"
ptext = projects_cfg.read_text(encoding="utf-8")
ptext = re.sub(
    r'categories: \[.*?\n\t\],',
    'categories: [\n\t\t{ key: "desktop", label: "Desktop", icon: "material-symbols:desktop-windows-outline-rounded" },\n\t],',
    ptext,
    flags=re.S,
)
projects_cfg.write_text(ptext, encoding="utf-8")

(site / "src/data/skills.ts").write_text(
    '''import type { SkillItem } from "@/types/skillsConfig";

export const skillsData: SkillItem[] = [
\t{ name: "Python", icon: "simple-icons:python", category: "language", level: "advanced" },
\t{ name: "Java", icon: "simple-icons:openjdk", category: "language", level: "intermediate" },
\t{ name: "C++", icon: "simple-icons:cplusplus", category: "language", level: "intermediate" },
\t{ name: "Rust", icon: "simple-icons:rust", category: "language", level: "intermediate" },
\t{ name: "PyTorch", icon: "simple-icons:pytorch", category: "ai", level: "advanced" },
\t{ name: "OpenCV", icon: "simple-icons:opencv", category: "ai", level: "advanced" },
\t{ name: "Computer Vision", icon: "material-symbols:visibility-outline-rounded", category: "ai", level: "advanced" },
\t{ name: "Deep Learning", icon: "material-symbols:neurology-outline-rounded", category: "ai", level: "advanced" },
\t{ name: "Git", icon: "simple-icons:git", category: "tooling", level: "advanced" },
\t{ name: "Docker", icon: "simple-icons:docker", category: "tooling", level: "intermediate" },
];

export function getSkillsList(): SkillItem[] {
\treturn skillsData;
}
''',
    encoding="utf-8",
)

(site / "src/config/skillsConfig.ts").write_text(
    '''import type { SkillsConfig } from "@/types/skillsConfig";
import { withUserConfig } from "../utils/config-overlay.ts";

export const skillsConfig: SkillsConfig = withUserConfig("skills", {
\tenable: true,
\tcategories: [
\t\t{ key: "language", label: "Languages", icon: "material-symbols:code-rounded" },
\t\t{ key: "ai", label: "AI / Vision", icon: "material-symbols:neurology-outline-rounded" },
\t\t{ key: "tooling", label: "Tooling", icon: "material-symbols:construction-rounded" },
\t],
});
''',
    encoding="utf-8",
)

posts = site / "src/content/posts"
if posts.exists():
    shutil.rmtree(posts)
posts.mkdir(parents=True, exist_ok=True)
(posts / "projects.md").write_text(
    '''---
title: "Projects"
published: 2026-08-30
pinned: true
description: "Auto Clicker · PasteImageAsFile"
tags: ["Projects"]
category: Projects
draft: false
---

## Auto Clicker

Windows 连点工具：多显示器取点、全局热键、倒计时、后台点击。

[GitHub](https://github.com/xiaobainiuniu/auto-clicker)

## PasteImageAsFile

Windows 工具：复制图片后，在资源管理器按 `Ctrl+V` 直接生成 PNG 文件。

[GitHub](https://github.com/xiaobainiuniu/PasteImageAsFile)
''',
    encoding="utf-8",
)

print("Shirone customization complete")
