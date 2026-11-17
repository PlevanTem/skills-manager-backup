# 3DCodeVerse 技术分类与证据

核查日期：2026-10-31。主要依据：[项目主页](https://3dcodeverse.com/)、[官方 Harness 文档](https://github.com/gaoypeng/3dcodeverse/blob/main/harness/README.md)、[官方仓库](https://github.com/gaoypeng/3dcodeverse)、[论文](https://arxiv.org/abs/2610.22341)。这些是项目作者的描述；下列选型建议是本 Skill 的工程判断，并非项目声称已完成的应用。

## 先分清层次

- 四个任务类型：静态物体、关节物体、场景、图形效果。
- 表示/创作：Blender Python (`bpy`)、CadQuery、OpenSCAD、Three.js、URDF、GLSL、OpenGL 各有不同职责，不能当作同层次互斥选项；URDF 是机器人描述格式，OpenGL 是图形 API，GLSL 是着色语言。
- 项目主页及数据集包含 OpenSCAD；截至核查日 Harness README 的语言列表为 `blender`, `cadquery`, `threejs`, `urdf_blender`, `scene_threejs`, `glsl_shader`, `opengl_python`，没有 OpenSCAD。工具路径和能力可能变化，应查看当前官方版本。
- Harness 是可选执行框架，不是每种选型都需要安装的依赖。其文档描述使用编码代理与执行、空间测量和视觉反馈迭代；不能把论文结果等同于本次任务效果。

## 技术矩阵

| 需求 | 建议主链路 | 适合 / 原因 | 限制及验收 |
|---|---|---|---|
| 艺术物件、材质、灯光、动画及离线画面 | Python → Blender `bpy` → Blender 场景/渲染，按需导出网格 | 程序化形体和渲染统一制作；主页展示 Blender Python 对象和场景 | 导出后材质、动画和格式兼容需实际检验；多视角、接触、比例和渲染核验 |
| 尺寸、装配、参数化 CAD | Python → CadQuery → CAD 几何，按目标环境导出 | 规则零件、参数和工程几何 | 单独验证单位、尺寸、公差、布尔结果和目标软件导入；不能仅凭外观证明可制造 |
| 简单参数化实体 | OpenSCAD → 参数化实体/网格 | 参数和 CSG 思路清晰；项目展示对象及数据集来源 | 项目收录不等同 Harness 生成支持；复杂曲面、结构和导入需试验 |
| 浏览器可交互对象或世界 | JavaScript + Three.js → 浏览器运行 | 对象拾取、镜头漫游、交互及程序化场景；主页 Jade Guardian 为浏览器实时 Three.js | 设备性能、加载和浏览器兼容需实测；网页视觉不证明网格或物理精确 |
| 机器人/关节对象 | URDF 描述 link/joint → 目标机器人工具或模拟器，按需 Blender 建模/预览 | 需要连接关系、关节范围与运动学 | URDF 本身不是物理求解器；质量、惯量、碰撞、坐标系及目标模拟器支持需验证。项目展示 Blender 工厂动画，不证明该演示直接产出 URDF |
| 烟、水、刚体、布料等离线动态 | Blender Python → 相应物理求解 → 烘焙/渲染 | 主页明确展示 Bullet 刚体、Mantaflow 液体/尘以及布料案例 | 计算、缓存和视觉精度有成本；材质动画与真实物理不可等同；布料求解细节主页未明确，不推定实现 |
| 实时水、光、体积感、程序化图形 | GLSL shader → 浏览器/图形运行时；或 OpenGL + GLSL | 优先追求实时像素效果而非编辑网格 | shader 可只生成像素，不必有真实几何；检查编译、目标 GPU 性能及画面 |
| 可控镜头与运动 + 视频风格化 | 代码构建三维场景、运动与相机 → 渲染 → 视频模型 | 主页用代码场景与 Seedance 做风格变化展示 | 视频模型可能改变结构、时序或细节；示例中的保持轨迹是项目展示，并非一般保证；输出视频不等于可编辑三维资产 |

## 项目案例与已知信息

- **Jade Guardian**：主页明确称网格、材质和灯光由浏览器中的 Three.js 生成；支持漫游和源码定位。不要把这一运行时套给全部 22 个作品。
- **River of a Thousand Lanterns**：主页区分 Blender 版本与可浏览的世界；它们服务不同输出，不据此假设两者实现或资产完全一致。
- **Codeworks robot factory**：主页称 Blender Python 创建并驱动多个机器人；它的仿真真实性、URDF 导出和目标模拟器互通未由展示证明。
- **Wrecking ball / Dam break / Silk drape**：分别展示刚体、流体、布料。主页明确提及 Bullet 和 Mantaflow（包括 dust、FLIP liquid），但没有逐项给出全部仿真参数或布料求解细节。
- **参数化高山村庄**：主页描述 Blender generator 与参数化重建；参数修改、可复现重建是已展示的设计意图，具体时间和效果不应推广为通用性能保证。
- **视频导演**：主页展示代码场景、蝴蝶运动与镜头作为条件交给 Seedance；这是混合链路，视频结果并非直接产生真实可编辑 3D。
- **GLSL 与 URDF 示例**：主页称 GLSL 在浏览器中编译运行、URDF 展示真实关节状态；不代表所有设备或模拟环境已验证。

## 验证与现实约束

项目 Harness 的方法可借鉴：计划 → 构建 → 执行检查 → 空间测量 → 多视角评估 → 定点修复；具体测量比图像判断更能证明尺寸/碰撞等约束。它是一种研究实现，不要求普通任务照搬多代理或打分系统。优先完成能够直接检验用户目标的小规模样例。
