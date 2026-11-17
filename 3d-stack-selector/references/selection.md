# 场景与技术选型

从交付物向前推，先选**表示与目标运行时**，再决定构建方式。下面是默认候选，不是强制规则；尽量沿用现有系统。核查时间：2026-10-31，版本、能力、价格和许可随时间变化。

| 目标 / 优先级 | 合适的候选链路 | 关键权衡 |
|---|---|---|
| 可编辑艺术物件、产品展示、电影级静帧/动画 | Blender 建模/Geometry Nodes/`bpy` → 材质、灯光、相机 → 渲染；可导出目标格式 | 艺术控制强；离线渲染时间、材质和动画导出要验证 |
| 尺寸精确、参数可修改、机械零件 | CadQuery / OpenSCAD 或已有 CAD 系统 → STEP/网格等目标格式 | 参数化和工程约束重要；导出网格不等于通过制造与公差验证 |
| 网页交互、可探索世界、产品配置 | Three.js 或现有 Babylon.js / React Three Fiber 栈 → WebGL/WebGPU 目标环境；Blender 制作资产时可评估 glTF/GLB | 加载量、渲染性能、交互和浏览器支持是硬约束；R3F 是 React 集成，非独立格式 |
| 游戏或复杂实时交互 | Godot、Unity、Unreal 或现有引擎 → 场景/脚本 → 目标平台 | 游戏逻辑、物理、部署与团队经验影响选型；先验证工具与目标平台可用 |
| 参数化大场景、群集、地形 | 程序化几何、Blender Geometry Nodes、引擎内生成或专门的程序化工具 | 种子、参数、实例化、层级细节与性能要控制；真实感仍需设计与验证 |
| 角色、骨骼动画、镜头叙事 | DCC 建模 / rig / 动画 → 离线渲染或目标引擎 | 拓扑、权重、骨骼、动画烘焙和格式兼容分别验证 |
| 物理动画或仿真 | DCC 求解器或目标引擎物理系统 → 模拟、缓存、回放 | 视觉可信、物理精确和实时性是不同目标；每项需要对应测试 |
| 机器人、关节、训练仿真 | URDF/MJCF 等描述 + 目标模拟器，例如 MuJoCo 或 Isaac Sim | URDF 是描述而非求解器；碰撞、质量、惯量、单位、驱动及坐标均需验证 |
| 水、云、光、体积感等视觉效果 | Shader（GLSL/WGSL 等）+ 合适的图形运行时，或 DCC 体积渲染 | 像素效果可能没有可编辑几何；目标设备和渲染器兼容需测试 |
| 有实景图片或视频的重建 | 摄影测量或 NeRF / Gaussian Splatting → 查看器；若需要网格再评估转换和修复 | 采集覆盖、遮挡、反射、GPU 与格式决定结果；新视角外观不等于拓扑正确 |
| 文本/图像生成 3D 候选 | 可用且获授权的生成工具/模型 → 生成 → DCC 清理和目标环境导入 | 可加快草稿，但拓扑、背面、尺度、材质和使用许可需逐项核实；不假定任何服务已配置 |
| 3D 引导视频 | 3D 场景、动作、镜头 → 影像序列 → 视频风格化工具 | 视频模型可能更改结构和运动；成片不等于可编辑 3D 资产 |
| CAD、网页、渲染和仿真混合 | 在主工具建模 → 分别导出各目标 → 分别验收 | 各格式的信息损失和坐标转换要显式测试，保留原始工程 |

## 选格式时关注

- **原始工程/脚本**：保留可编辑构建信息、版本、依赖和随机种子；网格导出通常不保留完整过程。
- **glTF/GLB**：常见实时资产交换候选，检查目标支持的扩展、贴图、动画与压缩；GLB 通常为单文件。
- **OBJ / STL**：按接收端实际需要使用；不要假设保留完整材质、层级、骨骼或动画。打印还需检查闭合与制造约束。
- **STEP**：适合支持该格式的 CAD 交换；核实单位、实体和接收端导入。
- **USD**：可用于复杂场景与特定工具链；版本、渲染和物理语义依接收软件验证。
- **URDF/MJCF**：机器人结构/仿真描述，按模拟器要求准备网格、碰撞和物理属性；导入成功仍需关节运行与物理检查。

## 原始参考

- [Blender Geometry Nodes](https://docs.blender.org/manual/en/5.0/modeling/geometry_nodes/introduction.html)；[glTF 导入导出](https://docs.blender.org/manual/en/4.2/addons/import_export/scene_gltf2.html)
- [Three.js GLTFLoader](https://threejs.org/docs/pages/GLTFLoader)；[Godot 3D 入门](https://docs.godotengine.org/en/stable/tutorials/3d/introduction_to_3d.html)
- [NVIDIA URDF 导入](https://docs.nvidia.com/learning/physical-ai/getting-started-with-isaac-sim/latest/ingesting-robot-assets-and-simulating-your-robot-in-isaac-sim/01-importing-urdf-assets.html)；[Nerfstudio Splatfacto](https://docs.nerf.studio/nerfology/methods/splat.html)
