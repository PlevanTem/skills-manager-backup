# Skill 版本和功能更新检测

- skill version: 1.3.0

## 1.检测 Skill 是否存在新版本，并根据用户选择决定是否更新 Skill

1. curl https://tdesign.gtimg.com/d2c/skill-version.json | jq -r '.version'

2. 判断返回版本号与 skill version 是否相同。如果不同，说明存在新版本，询问用户是否需要更新。如果需要更新，通过此链接下载新版本 https://tdesign.gtimg.com/d2c/tdesign-d2c.zip

3. 解压后，替换当前 Skill 的内容，只保留用户针对 `references` 内的相关修改， 并重新运行 Skill

**请注意步骤 1 必须最先执行**

## 2.预先安装依赖

在开始 D2C 流程之前，需要确保 `@tdesign/d2c-utils` 已安装且为最新版本，该工具包是用于进行 D2C 流程的辅助工具。

**自动检测包管理器**（按优先级：`pnpm-lock.yaml` → `yarn.lock` → `package-lock.json` → 默认 `npm`）：

```bash
# 检测当前项目使用的包管理器
if [ -f "pnpm-lock.yaml" ]; then PM=pnpm; elif [ -f "yarn.lock" ]; then PM=yarn; elif [ -f "package-lock.json" ]; then PM=npm; else PM=npm; fi
```

**执行以下命令进行版本检测**

```bash
${PM:-npm} outdated @tdesign/d2c-utils
```

- 如果命令**无任何输出**，说明已是最新版本。
- 如果命令**有输出**，或包未安装，必须执行：

```bash
${PM:-npm} install -D @tdesign/d2c-utils@latest
```

> **注意**：`${PM:-npm}` 表示使用检测到的包管理器，未检测到时回退为 `npm`。AI 在执行时应先通过 lock 文件自动判断包管理器。若项目使用 pnpm，命令为 `pnpm outdated ...` / `pnpm add -D ...`；若使用 yarn，命令为 `yarn outdated ...` / `yarn add -D ...`。

## 3.配置 Figma Token

<!-- 将 Figma Token 配置在此处 https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens -->

- figma-token:

**如果发现 figma-token 为空，提示用户在此配置 figma-token，参考 https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens**

## 4. Skill 运行信息

- model: 当前使用的模型
