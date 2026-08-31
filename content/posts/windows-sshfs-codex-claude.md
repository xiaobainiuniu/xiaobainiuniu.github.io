---
title: "Windows 下用 SSHFS 把远程服务器挂成本地磁盘：让 Codex / Claude Code 直接改远程代码"
published: 2026-08-31
description: "使用 WinFsp + SSHFS-Win 将 Linux 服务器目录映射为 Windows 本地盘，方便 Codex、Claude Code 和编辑器直接修改远程文件。"
tags: ["Windows", "SSHFS", "Codex", "Claude Code", "Remote Development"]
category: Tools
draft: false
---

这次发现了两个非常小但很好用的 Windows 工具：**WinFsp + SSHFS-Win**。

最终效果是把 Linux 服务器上的目录直接映射成 Windows 的 `Z:` 盘：

```text
远程服务器目录
      ↓ SSH
   SSHFS-Win
      ↓
Windows Z:
      ↓
Codex / Claude Code / 编辑器
```

在资源管理器里看起来和本地磁盘几乎一样，但文件实际上仍然保存在服务器上。**不是把服务器几十 GB、几百 GB 全部同步到本地**，而是按需通过 SSH 读取和写入。

## 一、需要安装的两个工具

### 1. WinFsp

Windows 用户态文件系统基础组件，SSHFS-Win 依赖它。

官方 Release：

[WinFsp 官方 GitHub Releases](https://github.com/winfsp/winfsp/releases)

我安装的是：

```text
WinFsp 2026 Beta4
winfsp-2.2.26215.msi
```

我的安装位置：

```text
D:\software\WinFsp\
```

只需要：

```text
Core ✅
Developer ❌
Kernel Developer ❌
FUSE for Cygwin ❌
```

### 2. SSHFS-Win

负责通过 SSH/SFTP 将 Linux 服务器目录映射为 Windows 驱动器。

官方 Release：

[SSHFS-Win 官方 GitHub Releases](https://github.com/winfsp/sshfs-win/releases)

我选择的是稳定版：

```text
SSHFS-Win 2021
v3.5.20357
sshfs-win-3.5.20357-x64.msi
```

我的安装位置：

```text
D:\software\SSHFS-Win\
```

## 二、不要直接把真实服务器信息写进公开博客

下面统一使用：

```text
<用户名>
<服务器IP>
<SSH端口>
<远程目录>
```

例如 SSH 登录方式：

```cmd
ssh <用户名>@<服务器IP> -p <SSH端口>
```

远程项目：

```text
/xxx/project/my-project
```

## 三、挂载服务器目录

SSHFS-Win 可以直接通过 Windows 的“映射网络驱动器”使用。

但我实际测试时，GUI 挂载可以正常读取文件，却出现了：

```text
目标文件夹访问被拒绝
你需要权限来执行此操作
```

也就是：

```text
读取 ✅
新建文件 ❌
修改/写入 ❌
```

而我的目的就是让 Codex / Claude Code 直接修改服务器代码，所以最后改用了 SSHFS-Win 自带的命令行挂载方式。

## 四、推荐的可写挂载方式

### 1. 先断开旧的 Z 盘

```cmd
net use Z: /delete
```

### 2. 使用 SSHFS-Win 重新挂载

如果 SSHFS-Win 安装在：

```text
D:\software\SSHFS-Win\
```

执行：

```cmd
"D:\software\SSHFS-Win\bin\sshfs-win.exe" cmd <用户名>@<服务器IP>:/xxx/project/my-project Z: -p <SSH端口> -o uid=-1,gid=-1,umask=000,create_umask=000
```

执行后会要求输入 SSH 密码。

成功后：

```text
Linux:
/xxx/project/my-project

↓

Windows:
Z:\
```

> `umask=000/create_umask=000` 是为解决 Windows 端写入权限映射问题采用的参数。共享服务器上使用时，仍应遵守服务器本身的目录权限策略，不要修改自己无权修改的目录。

## 五、测试是否真的可以写入

CMD：

```cmd
echo hello > Z:\sshfs_test.txt
```

然后：

```cmd
type Z:\sshfs_test.txt
```

如果输出：

```text
hello
```

说明写入已经成功。

再到服务器上：

```bash
ls
cat sshfs_test.txt
```

同样可以看到这个文件。

至此可以确认：

```text
读取服务器文件 ✅
创建服务器文件 ✅
修改服务器文件 ✅
删除服务器文件 ✅
```

## 六、直接使用 Codex / Claude Code

以后 CMD 直接：

```cmd
Z:
codex
```

或者：

```cmd
Z:
claude
```

对于 Codex / Claude Code 来说，`Z:` 看起来就是普通工作目录。

例如：

```text
Z:\train.py
```

实际上对应的是：

```text
服务器 /xxx/project/my-project/train.py
```

AI 修改 `Z:\train.py` 后，服务器上的原文件会直接变化，不需要：

```text
下载
→ 本地修改
→ 上传
```

也不需要把 Codex / Claude Code 安装到服务器。

## 七、它不是“同步盘”

这是最容易误解的一点。

SSHFS：

```text
远程服务器 100GB
      ↓
按需读取
      ↓
Windows Z:
```

并不是：

```text
远程服务器 100GB
      ↓
全部下载 100GB 到本机 ❌
```

所以即使资源管理器显示：

```text
Z:
714 TB 可用
787 TB 总容量
```

也不代表电脑突然多了 787TB 😂

这是**远程服务器文件系统的容量信息**。

## 八、需要注意

`Z:` 虽然像本地盘，但本质仍然是远程 SSH 文件系统：

```text
改文件 → 修改服务器原文件
删文件 → 删除服务器原文件
网络断开 → Z: 暂时不可访问
```

另外 Codex / Claude Code 本身还是运行在 Windows：

```text
读取/修改 Z: 文件 → 服务器文件 ✅
直接执行 python/npm 等命令 → 默认是本机 Windows 环境
```

如果需要执行服务器上的 CUDA、Conda、Python 环境，仍然应该 SSH 到服务器运行。

## 九、卸载

不想用了很好清理。

先断开：

```cmd
net use Z: /delete
```

然后：

```text
Windows 设置
→ 应用
→ 已安装的应用
```

依次卸载：

```text
SSHFS-Win
WinFsp
```

建议顺序：

```text
SSHFS-Win → WinFsp
```

## 十、重启和睡眠后的处理

### 重启电脑以后

重启后 `Z:` 一般不会自动挂载。**不需要 `taskkill`**，直接普通 CMD 执行挂载命令：

```cmd
"D:\software\SSHFS-Win\bin\sshfs-win.exe" cmd <用户名>@<服务器IP>:/xxx/project/my-project Z: -p <SSH端口> -o uid=-1,gid=-1,umask=000,create_umask=000
```

出现：

```text
<用户名>@<服务器IP>'s password:
```

输入密码后回车即可。

### 睡眠唤醒以后

先点一下 `Z:`：

- **能打开** → 不需要处理
- **打不开 / 出现问号** → 普通 CMD：

```cmd
taskkill /IM sshfs.exe /F
```

然后重新执行挂载命令。

如果 `taskkill` 提示：

```text
没有找到进程 sshfs.exe
```

也没关系，直接重新挂载即可。

只有出现那种**死掉的 `Z:?` 怎么都清不掉**的极少数情况，才需要管理员 CMD：

```cmd
"D:\software\WinFsp\bin\fsptool-x64.exe" unload
"D:\software\WinFsp\bin\fsptool-x64.exe" load
```

然后**关闭管理员 CMD，再用普通 CMD 挂载**。

最终记住这三种情况即可：

```text
正常重启：
普通 CMD → 挂载命令 → 输密码

睡眠醒来：
Z: 能用 → 不管
Z: 不能用 → taskkill → 重新挂载

死盘符清不掉：
管理员 CMD → WinFsp unload/load
→ 回普通 CMD 重新挂载
```

## 最后

这两个工具体积都非常小，但解决的问题很实际：

> **把远程 Linux 代码目录映射到 Windows，让本地 Codex、Claude Code、编辑器直接操作服务器文件。**

对于“AI Agent 只装本地，但代码放在远程服务器”的场景，非常舒服。

```text
服务器代码
  ↓ SSHFS
Windows Z:
  ↓
本地 Codex / Claude Code
```

小工具，大作用。😂
