---
title: "腾讯云轻量服务器 SSH 安全配置：校园网绕过 22 端口、密钥登录与 Codex 一键部署"
published: 2026-09-12
description: "记录一次真实的腾讯云轻量服务器初始化：校园网封锁 22 端口、改用 2222、Ed25519 密钥、Windows ssh-agent、SSH 别名，以及 Codex 通过 ssh tencent 部署代码。"
tags: ["Tencent Cloud", "SSH", "Windows", "Codex", "Linux", "Deployment"]
category: Tools
draft: false
---

这篇文章记录我刚刚完整配置一台腾讯云轻量服务器的过程。

我的实际环境：

```text
腾讯云轻量应用服务器
4 核 / 4 GB
40 GB SSD
3 Mbps
Ubuntu 26.04 LTS
服务器用户：ubuntu
Windows 11
SSH 最终端口：2222
SSH 别名：tencent
```

> **备注：本文记录的是我的真实配置和真实排错过程。出于安全考虑，公网服务器地址统一写成 `<服务器IP>`，不公开真实服务器 IP；其余端口、用户名、别名和命令均按我的实际配置记录。**

最终我想要的效果非常简单：

```text
Windows / Codex
      ↓
ssh tencent
      ↓
Windows ssh-agent
      ↓
Ed25519 私钥
      ↓
校园网
      ↓
腾讯云 SSH 2222
      ↓
ubuntu
```

平时手动登录只需要：

```powershell
ssh tencent
```

Codex 也只需要执行：

```bash
ssh tencent
```

不需要再给 Codex 服务器 IP、端口、用户名、服务器密码，更不需要把 SSH 私钥复制进聊天。

---

## 一、以后让 Codex 部署代码，我直接复制这个提示词

完整版：

> **请把当前项目部署到我的腾讯云服务器。服务器已配置 SSH 别名 `tencent`，直接通过 `ssh tencent` 连接即可，不要向我索要或读取、输出 SSH 私钥和密码。先检查当前项目结构，再将代码上传到服务器的 `/home/ubuntu/<项目名>`。优先使用现有的 SSH / SCP / rsync 等标准工具，不要为了上传额外安装不必要的软件。不要上传 `.git`、`node_modules`、虚拟环境、缓存、构建临时文件，也不要上传或覆盖 `.env`、密钥、Token 等敏感文件，除非我明确要求。不要执行 `--delete`、删除服务器已有文件或覆盖重要配置，除非确认安全。上传完成后检查服务器端文件是否完整，并告诉我实际执行了什么、代码最终位于哪个目录。**

平时也可以直接用精简版：

> **把当前项目部署到 `tencent:/home/ubuntu/<项目名>`，使用现有 SSH 配置和密钥认证。不要读取或输出私钥，不上传敏感文件，不删除服务器已有数据，完成后验证上传结果。**

例如：

```text
把当前项目部署到 tencent:/home/ubuntu/wechat-api，使用现有 SSH 配置和密钥认证。不要读取或输出私钥，不上传敏感文件，不删除服务器已有数据，完成后验证上传结果。
```

关键点只有一个：**让 Codex 使用密钥，而不是把密钥告诉 Codex。**

---

## 二、这次到底解决了什么

这次主要解决了四件事。

第一，校园网无法连接服务器默认 SSH 端口 `22`。手机热点可以连接，但校园网一直超时。最终给 SSH 增加 `2222` 端口，并在腾讯云防火墙放行 `2222`，校园网立即恢复正常。

第二，把服务器从“用户名 + 密码登录”改成了 **Ed25519 SSH 密钥登录**。

第三，SSH 私钥设置了 passphrase，并让 Windows 自带的 `ssh-agent` 管理密钥。这样私钥文件即使被复制走，也还有 passphrase 这一层保护；正常使用时又不用每次 SSH 都输入一遍长密码。

第四，把 IP、端口、用户名和密钥路径全部封装进：

```text
C:\Users\liu\.ssh\config
```

以后只需要：

```powershell
ssh tencent
```

Codex 也可以直接使用这个别名。

### Windows 重启以后要做什么

这是我最容易忘的一点。

`ssh-agent` 已经设置成 Windows 自动启动：

```powershell
Set-Service -Name ssh-agent -StartupType Automatic
```

但是 **Windows 重启以后，ssh-agent 虽然会自动运行，已经解锁的私钥通常不会一直保留在 agent 内存里。**

所以每次 Windows 重新开机后，我只需要在 PowerShell 执行：

```powershell
ssh-add $env:USERPROFILE\.ssh\tencent_cloud_ed25519
```

输入一次密钥的 passphrase。

然后检查：

```powershell
ssh-add -l
```

最后：

```powershell
ssh tencent
```

之后这一轮开机期间，PowerShell、Git、Codex 等通过 Windows OpenSSH 使用这把密钥时，就不需要反复输入 passphrase 了。

---

# 三、详细过程：从刚买服务器开始

## 1. 重装 Ubuntu

腾讯云轻量服务器刚买回来时默认是 OpenCloudOS。

我直接在腾讯云控制台进入：

```text
服务器
→ 更多操作
→ 重装系统
→ 基于操作系统镜像
→ Ubuntu
```

最终安装的是：

```text
Ubuntu 26.04 LTS
```

腾讯云控制台显示的“实例名称”不会因为重装系统自动变化，这只是控制台里的备注名称，与服务器实际系统无关。

Ubuntu 默认登录用户是：

```text
ubuntu
```

---

## 2. 第一次发现 SSH 连不上

Windows PowerShell：

```powershell
ssh ubuntu@<服务器IP>
```

结果：

```text
ssh: connect to host <服务器IP> port 22: Connection timed out
```

先检查腾讯云防火墙，发现：

```text
TCP 22
全部 IPv4 地址
允许
```

所以腾讯云这一层其实没有问题。

然后通过腾讯云 VNC 直接进入服务器，检查 SSH：

```bash
sudo systemctl status ssh
```

结果：

```text
Active: active (running)
```

说明 SSH 服务本身也是正常的。

进一步看监听端口：

```bash
sudo ss -lntp | grep :22
```

22 端口也正常监听。

最后做了最简单的交叉测试：

```text
校园网 + SSH 22  → 超时
手机热点 + SSH 22 → 立即成功
```

问题就定位清楚了：**不是腾讯云坏了，也不是 SSH 没启动，而是我当前校园网无法直接访问外部 TCP 22。**

---

## 3. 给 SSH 增加 2222 备用端口

这台 Ubuntu 使用了 `ssh.socket`，所以我通过 systemd override 增加一个监听端口。

执行：

```bash
sudo systemctl edit ssh.socket
```

Ubuntu 默认打开的是 `nano`，不是 Vim。

nano 常用操作：

```text
Ctrl + O    保存
Enter       确认文件名
Ctrl + X    退出
```

而 Vim 的：

```text
Esc
:wq
:q!
```

在 nano 里不是一套操作。

写入：

```ini
[Socket]
ListenStream=
ListenStream=0.0.0.0:22
ListenStream=[::]:22
ListenStream=0.0.0.0:2222
ListenStream=[::]:2222
```

这里第一行：

```ini
ListenStream=
```

不能删，它用于先清空原有的 `ListenStream` 配置，再重新添加 22 和 2222。

保存以后先完整检查：

```bash
sudo systemctl cat ssh.socket
```

确认 override 正确，再执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart ssh.socket
```

检查：

```bash
sudo ss -lntp | grep -E ':(22|2222)\b'
```

最终看到：

```text
0.0.0.0:22      LISTEN
0.0.0.0:2222    LISTEN
[::]:22         LISTEN
[::]:2222       LISTEN
```

说明服务器端已经成功监听 2222。

---

## 4. 腾讯云防火墙放行 2222

回到腾讯云轻量服务器：

```text
防火墙
→ 添加规则
```

配置：

```text
应用类型：自定义
来源：全部 IPv4 地址
协议：TCP
端口：2222
策略：允许
备注：SSH备用端口
```

保存。

电脑切回校园网后测试：

```powershell
Test-NetConnection <服务器IP> -Port 2222
```

然后 SSH：

```powershell
ssh -p 2222 ubuntu@<服务器IP>
```

成功。

Xshell 8 里也只需要改成：

```text
主机：<服务器IP>
端口：2222
用户名：ubuntu
协议：SSH
```

至此，校园网问题解决。

确认 `2222` 长期正常以后，腾讯云防火墙里的公网 `22` 入站规则就可以关闭。服务器内部保留 22 监听也没有关系，因为云防火墙已经可以在公网入口直接拦截。

---

# 四、配置 Ed25519 SSH 密钥

## 1. 在 Windows 本机生成密钥

**不在浏览器生成，也不在服务器上生成。**

直接在自己的 Windows PowerShell：

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\tencent_cloud_ed25519
```

会问：

```text
Enter passphrase (empty for no passphrase):
```

我最后选择了：**设置 passphrase，不留空。**

原因很简单：

```text
Ed25519 私钥本身很强
+
私钥文件再加一层 passphrase
```

如果电脑上的私钥文件未来意外被复制，对方也不能拿着文件直接登录服务器。

生成后得到：

```text
C:\Users\liu\.ssh\tencent_cloud_ed25519
C:\Users\liu\.ssh\tencent_cloud_ed25519.pub
```

其中：

```text
tencent_cloud_ed25519      私钥，绝对不要公开
tencent_cloud_ed25519.pub  公钥，可以放到服务器
```

**不要把私钥复制给 Codex，不要粘贴进聊天，不要提交 GitHub，不要放项目目录。**

---

## 2. 把公钥放到服务器

我第一次尝试过直接把 PowerShell 文本管道写到：

```text
~/.ssh/authorized_keys
```

后来发现服务端并没有正确接受这把公钥。

检查：

```bash
ssh-keygen -lf ~/.ssh/authorized_keys
```

当时提示：

```text
/home/ubuntu/.ssh/authorized_keys is not a public key file.
```

为了避免 Windows PowerShell 与 Linux 之间可能出现的文本编码、换行等问题，最终采用最稳的办法：**直接用 SCP 上传原始 `.pub` 文件。**

Windows PowerShell：

```powershell
scp -P 2222 $env:USERPROFILE\.ssh\tencent_cloud_ed25519.pub ubuntu@<服务器IP>:/home/ubuntu/.ssh/authorized_keys
```

输入一次服务器原来的登录密码。

传输完成后，再执行：

```powershell
ssh tencent
```

服务器终于直接接受公钥。

---

# 五、Windows ssh-agent：只输入一次 passphrase

如果私钥设置了 passphrase，但每一次 SSH 都要输入一遍，会很烦。

标准的解决方式就是 Windows 自带的：

```text
OpenSSH Authentication Agent
ssh-agent
```

它不是第三方程序，也没有额外下载安装东西。

## 1. 设置 ssh-agent 自动启动

用**管理员 PowerShell**：

```powershell
Set-Service -Name ssh-agent -StartupType Automatic
```

启动：

```powershell
Start-Service ssh-agent
```

## 2. 把密钥加入 agent

```powershell
ssh-add $env:USERPROFILE\.ssh\tencent_cloud_ed25519
```

这里输入一次刚才设置的密钥 passphrase。

成功后会看到类似：

```text
Identity added: C:\Users\liu\.ssh\tencent_cloud_ed25519
```

检查：

```powershell
ssh-add -l
```

能看到 ED25519 密钥即可。

以后本次 Windows 会话中，SSH 可以通过 agent 使用已经解锁的密钥。

再次强调，**Windows 重启以后一般重新执行一次：**

```powershell
ssh-add $env:USERPROFILE\.ssh\tencent_cloud_ed25519
```

输入一次 passphrase 即可。

---

# 六、配置 SSH 别名 `tencent`

打开：

```powershell
notepad $env:USERPROFILE\.ssh\config
```

我的文件位置就是：

```text
C:\Users\liu\.ssh\config
```

在原有配置最下面加入：

```sshconfig
Host tencent
    HostName <服务器IP>
    User ubuntu
    Port 2222
    IdentityFile ~/.ssh/tencent_cloud_ed25519
    IdentitiesOnly yes
```

以后：

```powershell
ssh tencent
```

等价于把服务器 IP、用户名、2222 端口和密钥路径全部写完整。

最终达到：

```text
ssh tencent
→ 不输入服务器密码
→ 不重新填写 IP
→ 不重新填写 2222
→ 不重新填写用户名
→ ssh-agent 自动使用已经解锁的 Ed25519 密钥
```

这一步也是后面 Codex 自动操作服务器的关键。

---

# 七、关闭服务器 SSH 密码登录和 root SSH 登录

在确认：

```powershell
ssh tencent
```

已经可以通过密钥正常进入服务器以后，再做这一步。

**一定不要在密钥登录还没验证成功时先关密码。**

## 1. 检查当前 SSH 实际配置

服务器执行：

```bash
sudo sshd -T | grep -E 'passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|permitrootlogin'
```

我最初得到：

```text
permitrootlogin yes
pubkeyauthentication yes
passwordauthentication yes
kbdinteractiveauthentication no
```

进一步找配置来源：

```bash
sudo grep -RniE '^[[:space:]]*(PasswordAuthentication|PermitRootLogin|PubkeyAuthentication|KbdInteractiveAuthentication)[[:space:]]+' /etc/ssh/sshd_config /etc/ssh/sshd_config.d 2>/dev/null
```

我的实际情况：

```text
/etc/ssh/sshd_config:54:PermitRootLogin yes
/etc/ssh/sshd_config:85:KbdInteractiveAuthentication no
/etc/ssh/sshd_config.d/50-cloud-init.conf:1:PasswordAuthentication yes
```

这里还有腾讯云 / cloud-init 生成的配置，所以没有直接粗暴修改 `50-cloud-init.conf`，而是新建自己的 hardening 配置。

## 2. 新建 SSH 安全配置

```bash
printf '%s\n' 'PasswordAuthentication no' 'PermitRootLogin no' 'PubkeyAuthentication yes' 'KbdInteractiveAuthentication no' | sudo tee /etc/ssh/sshd_config.d/00-hardening.conf
```

得到：

```text
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
KbdInteractiveAuthentication no
```

先检查语法和实际结果：

```bash
sudo sshd -t && sudo sshd -T | grep -E 'passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|permitrootlogin'
```

最终应为：

```text
permitrootlogin no
pubkeyauthentication yes
passwordauthentication no
kbdinteractiveauthentication no
```

确认正确后：

```bash
sudo systemctl reload ssh
```

**这时候先不要关闭当前已登录的 SSH / Xshell 窗口。**

新开一个 PowerShell 再测试：

```powershell
ssh tencent
```

能够正常进入以后，再测试密码登录是否确实已经被拒绝：

```powershell
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password tencent
```

我的最终结果：

```text
ubuntu@<服务器IP>: Permission denied (publickey).
```

这正是想要的结果：**服务器已经不接受 SSH 密码登录，只接受公钥。**

---

# 八、最终状态

最后我的 SSH 状态变成：

```text
Ubuntu 26.04 LTS
用户 ubuntu
SSH 2222
Ed25519 密钥登录
私钥带 passphrase
Windows ssh-agent 管理私钥
SSH 密码登录关闭
root SSH 登录关闭
SSH 别名 tencent
校园网可以正常连接
```

日常登录：

```powershell
ssh tencent
```

Windows 刚重启以后：

```powershell
ssh-add $env:USERPROFILE\.ssh\tencent_cloud_ed25519
ssh-add -l
ssh tencent
```

以后 Codex 要部署代码，只需要让它使用：

```text
ssh tencent
```

而不是把：

```text
服务器密码
SSH 私钥内容
密钥 passphrase
```

发给模型。

---

# 九、我现在的 Codex 使用原则

我会把权限关系保持成：

```text
Codex
  ↓
调用 ssh tencent
  ↓
Windows OpenSSH / ssh-agent
  ↓
使用本机已经配置好的认证
  ↓
腾讯云服务器
```

而不是：

```text
Codex
  ↓
读取我的私钥正文
  ↓
拿到密码 / passphrase
```

前者的好处是：**凭据管理仍然交给本机 SSH 工具链，Codex 只负责调用已经配置好的连接。**

以后不管是部署 FastAPI、微信小程序后端、Docker Compose、Nginx，还是把本地项目同步到服务器，统一围绕 `ssh tencent` 做即可。

下一步就是正式把这台 4C4G 腾讯云服务器变成自己的长期后端机器：Docker、Git、Nginx、FastAPI、数据库和微信小程序 API 都可以逐步部署上去。
