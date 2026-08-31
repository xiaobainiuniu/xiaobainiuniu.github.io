---
title: "Windows 下用 CLIProxyAPI 统一管理 Codex 多模型与中转：从安装到 Responses 兼容、代理与前缀路由"
published: 2026-08-31
description: "在 Windows 本地部署 CLIProxyAPI（CPA），把多个 OpenAI 兼容中转、官方 Codex OAuth 和不同模型统一到一个本地 API，并解决 Responses、代理、User-Agent 与前缀路由问题。"
tags: ["Windows", "CLIProxyAPI", "Codex", "OpenAI", "API Gateway"]
category: Tools
draft: false
---

最近一直在折腾 Codex CLI、多家 API 中转和不同模型。

如果每一家都直接在客户端里单独配置，模型一多之后会越来越乱：

```text
Codex
├─ 中转 A
├─ 中转 B
├─ NVIDIA
├─ 官方 Codex OAuth
└─ 其他 OpenAI 兼容服务
```

后来我开始使用 **CLIProxyAPI（下面简称 CPA）**，把这些入口统一到本机一个地址：

```text
Codex / CC Switch
        ↓
http://127.0.0.1:8317/v1
        ↓
       CPA
   ┌────┼────┬──────┐
   ↓    ↓    ↓      ↓
官方   NVIDIA 中转A  中转B
```

最终 Codex 只需要认识 CPA，不需要频繁修改 URL 和 Key。

本文记录我在 Windows 上实际配置 CPA 的完整过程，以及几个非常容易踩的坑：

- Chat Completions 与 Responses 的区别
- OpenAI 兼容提供商应该放在哪里
- 全局代理和 `direct` 到底怎么用
- 为什么某些中转直连正常，经过 CPA 却返回 404
- 如何用前缀明确指定某一家提供商
- CPA 配置是否需要每次重启

> 本文所有 Key、账号和私有地址均使用占位符，不要把真实密钥提交到公开仓库。

## 一、安装 CLIProxyAPI

项目地址：

[CLIProxyAPI GitHub](https://github.com/router-for-me/CLIProxyAPI)

我使用的是 Windows x86-64 版本：

```text
CLIProxyAPI 7.2.146
CLIProxyAPI_7.2.146_windows_amd64
```

解压后主要会看到：

```text
cli-proxy-api.exe
config.example.yaml
```

复制一份配置：

```text
config.example.yaml
        ↓
config.yaml
```

然后启动：

```cmd
cli-proxy-api.exe
```

默认监听端口：

```text
8317
```

因此本地 API 地址就是：

```text
http://127.0.0.1:8317/v1
```

管理页面：

```text
http://127.0.0.1:8317/management.html
```

## 二、最基础的本地配置

我的目标只是本机使用，所以只绑定：

```yaml
host: "127.0.0.1"
port: 8317
```

本地客户端访问 CPA 时再设置一个单独的 API Key：

```yaml
api-keys:
  - "<CPA_LOCAL_KEY>"
```

例如后面测试时统一写：

```text
Authorization: Bearer <CPA_LOCAL_KEY>
```

不要把这个本地 Key 和上游提供商的真实 Key 混在一起。

## 三、CC Switch / Codex 只需要指向 CPA

如果本来就在使用 CC Switch，可以新增一个 Codex Provider：

```text
名称：CPA
API 地址：http://127.0.0.1:8317/v1
API Key：<CPA_LOCAL_KEY>
```

默认模型可以先选一个已经确认可用的模型，例如：

```text
gpt-5.6-sol
```

之后整体结构就是：

```text
Codex
  ↓
CC Switch
  ↓
CPA
  ↓
不同上游提供商
```

CC Switch 以后基本只负责让 Codex 指向 CPA，真正的上游路由、协议转换、代理和请求头都由 CPA 负责。

## 四、最重要的一点：Chat Completions 和 Responses 不要搞混

很多中转虽然写着“OpenAI 兼容”，实际提供的是：

```text
/v1/chat/completions
```

而 Codex 更偏向使用：

```text
/v1/responses
```

CPA 里面对应的配置思路是：

```text
上游原生 /chat/completions
→ 放到「OpenAI 兼容」

上游原生 /responses
→ 使用 Codex API Key 一类的 Responses 配置
```

这里非常容易理解反。

**OpenAI 兼容并不等于上游原生支持 Responses。**

CPA 的价值之一，就是可以在中间做协议转换：

```text
Codex /responses
        ↓
       CPA
        ↓ 转换
上游 /chat/completions
```

所以对于只提供 Chat Completions 的中转，不需要为了 Codex 强行把它配置成 Responses Provider。

## 五、添加 OpenAI 兼容中转

在管理页面：

```text
AI 提供商
→ OpenAI 兼容
→ 新增
```

基本填写：

```text
名称：<provider-name>
服务地址：https://example.com/v1
API Key：<UPSTREAM_API_KEY>
```

如果模型真实名称已经很干净，例如：

```text
grok-4.6
glm-5.2
gemini-3.1-pro
```

Alias 可以留空。

如果上游名称比较长，例如：

```text
deepseek-ai/deepseek-v4-flash-0731
```

可以映射成：

```text
deepseek-v4-flash-0731
```

这样 Codex 的 `/model` 看起来会整齐很多。

## 六、先用 `/v1/models` 确认 CPA 是否识别到模型

CMD 中测试：

```cmd
curl.exe http://127.0.0.1:8317/v1/models -H "Authorization: Bearer <CPA_LOCAL_KEY>"
```

只要能够看到刚刚配置的模型，说明：

```text
CPA 已读取配置 ✅
模型已进入路由表 ✅
```

但要注意：

**模型出现在 `/v1/models` 中，不代表真实推理一定成功。**

还要继续测试请求。

## 七、先测试 Chat Completions

如果上游本来就是 Chat Completions，先直接测试 CPA 的 Chat 接口：

```cmd
curl.exe http://127.0.0.1:8317/v1/chat/completions -H "Authorization: Bearer <CPA_LOCAL_KEY>" -H "Content-Type: application/json" -d "{\"model\":\"gemini-3.1-pro\",\"messages\":[{\"role\":\"user\",\"content\":\"只回复OK\"}],\"stream\":false}"
```

正常结果类似：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "OK"
      }
    }
  ]
}
```

如果这里成功，至少说明：

```text
CPA → 上游 → 模型
```

这一条链路已经通了。

## 八、再测试 Responses 转换

接着测试：

```cmd
curl.exe http://127.0.0.1:8317/v1/responses -H "Authorization: Bearer <CPA_LOCAL_KEY>" -H "Content-Type: application/json" -d "{\"model\":\"gemini-3.1-pro\",\"input\":\"只回复OK\",\"stream\":false}"
```

如果返回：

```text
status: completed
text: OK
```

说明：

```text
Codex /responses
        ↓
       CPA
        ↓
/chat/completions 上游
```

这一层转换也已经正常。

不过真实 Codex 请求通常比这条测试复杂，还可能携带 Tools、Reasoning 等字段，所以最终仍然建议进入 Codex CLI 实际跑一次。

## 九、一个很隐蔽的坑：直连成功，经过 CPA 却 404

这次遇到过一个非常奇怪的问题。

同一个中转、同一个模型、同一个 Key，直接 curl：

```text
/v1/chat/completions
```

可以正常返回：

```text
OK
```

但经过 CPA 请求时，上游却返回了一整页 HTML：

```text
404 NOT FOUND
```

一开始很容易怀疑：

```text
是不是 Base URL 填错？
是不是代理问题？
是不是模型名不对？
是不是 Responses 不兼容？
```

后来做了一个单变量测试才发现，问题来自请求头。

CPA 的 OpenAI Compatibility Executor 默认会发送：

```text
User-Agent: cli-proxy-openai-compat
```

而这个特定上游对该 User-Agent 做了特殊处理。

直接 curl 时默认 User-Agent 是：

```text
curl/8.16.0
```

于是进入：

```text
OpenAI 兼容提供商
→ 编辑
→ 请求头
```

添加：

```text
User-Agent = curl/8.16.0
```

再次测试，立即恢复正常。

所以以后遇到这种现象：

```text
直接 curl ✅
CPA 请求 ❌
```

不要只盯着 URL 和 Key，还要比较：

```text
URL
Header
Body
代理出口
```

尤其是 User-Agent。

> 这不是所有中转都需要设置。只有确认某一家存在兼容问题时再单独覆盖，不建议给所有提供商统一乱加请求头。

## 十、全局代理和 `direct` 怎么理解

CPA 支持全局代理，例如：

```yaml
proxy-url: "http://127.0.0.1:<LOCAL_PROXY_PORT>"
```

如果单个提供商的 `proxy-url` 留空：

```text
留空
→ 继承 CPA 全局代理
```

如果单独填写：

```text
direct
```

则表示：

```text
这一条凭据明确直连
不使用 CPA 全局代理
也不使用环境代理
```

因此可以做到：

```text
官方 OAuth → 使用全局代理
某些国内/可直连中转 → direct
其他提供商 → 留空继承全局配置
```

重点是：**CPA 不可能自动知道每一家中转最适合走哪条网络。**

以前直接用 CC Switch 时，请求最终可能由原客户端发出；现在加了一层 CPA 后，真正连接上游的是 CPA，所以出站网络也需要在 CPA 这一层考虑。

不过不要一开始就给所有提供商填 `direct`。

最稳的做法是：

```text
能正常用 → 不改
明确发现网络路径有问题 → 再调整 direct / 单独代理
```

## 十一、前缀路由真的很好用

当两个提供商都有同一个模型，例如：

```text
grok-4.6
```

如果全部暴露成同一个名称，很难知道这一次到底走了哪一家。

CPA 的 Prefix 很适合解决这个问题。

例如给备用提供商设置：

```text
prefix: linshi
```

那么 Codex `/model` 中就可以同时看到：

```text
grok-4.6
linshi/grok-4.6
```

使用：

```text
grok-4.6
```

走默认路由；

使用：

```text
linshi/grok-4.6
```

则明确指定这个带前缀的提供商。

我现在非常喜欢这种方式，因为调试时特别直观：

```text
主线路由 → 干净模型名
备用/临时站 → provider/model
```

比把很多来源全部堆到同一个模型名下面更容易排查。

## 十二、CPA 支持热更新，不需要每次重启

CPA 本身有配置 watcher。

日常修改：

```text
API Key
模型
Alias
Prefix
请求头
Provider 配置
proxy-url
```

保存后通常都会热更新。

正常流程：

```text
修改
→ 保存
→ 直接测试
```

不需要每次：

```text
关闭 CPA
→ 再重新启动
```

只有这些情况我才会考虑重启：

```text
升级 cli-proxy-api.exe
保存后明显仍然读取旧状态
认证 / cooldown 状态异常
排障时想彻底排除内存状态影响
启动级配置发生变化
```

所以日常使用其实很轻松。

## 十三、我现在的推荐配置思路

最后总结一下我现在比较舒服的架构：

```text
Codex CLI
   ↓
CC Switch
   ↓
http://127.0.0.1:8317/v1
   ↓
CLIProxyAPI
   ├─ 官方 Codex OAuth
   ├─ NVIDIA
   ├─ OpenAI Compatible A
   ├─ OpenAI Compatible B
   └─ 其他 Provider
```

配置原则：

```text
1. Codex 永远只连 CPA
2. Chat Completions 上游放 OpenAI 兼容
3. Responses 原生上游按对应 Responses Provider 配置
4. 模型名太长就 Alias
5. 需要明确指定来源就 Prefix
6. 能正常请求的 Provider 不要乱改 Header / Proxy
7. 某一家有问题，再单独做兼容设置
8. 配置一般热更新，不必反复重启
```

## 十四、几个常用测试命令

### 查看模型

```cmd
curl.exe http://127.0.0.1:8317/v1/models -H "Authorization: Bearer <CPA_LOCAL_KEY>"
```

### 测试 Chat Completions

```cmd
curl.exe http://127.0.0.1:8317/v1/chat/completions -H "Authorization: Bearer <CPA_LOCAL_KEY>" -H "Content-Type: application/json" -d "{\"model\":\"<MODEL>\",\"messages\":[{\"role\":\"user\",\"content\":\"只回复OK\"}],\"stream\":false}"
```

### 测试 Responses

```cmd
curl.exe http://127.0.0.1:8317/v1/responses -H "Authorization: Bearer <CPA_LOCAL_KEY>" -H "Content-Type: application/json" -d "{\"model\":\"<MODEL>\",\"input\":\"只回复OK\",\"stream\":false}"
```

## 结语

CPA 真正吸引我的地方，不是“又多了一个代理层”，而是把之前分散在不同客户端里的模型和提供商统一起来了。

刚开始配置确实会遇到一些协议、代理和 Header 的细节问题，但一旦跑通以后，客户端这一层会干净很多：

```text
一个 URL
一个本地 Key
一份模型列表
```

后面再增加新中转时，基本只需要在 CPA 里加 Provider，Codex 本身不需要反复折腾。

对于同时使用 Codex CLI、多模型和多家 API Provider 的场景，这套方式确实很舒服。
