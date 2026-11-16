# 透明物体深度恢复与双相机融合：分析记录包

对应论文：**Transparent-Object Depth Recovery with Heterogeneous RGB-D Views: An Empirical Study of Observation Gains and Fusion Costs**  
作者：Haoyang Lu、Bin Xu；湖北科技学院。科学内容基线：B0.9；本资料包编号：`public-records-v1`。

这是从既有记录整理的公开查阅包，不是新算法、已录用论文声明或完整训练工程。包编号不表示已经创建了GitHub Release，也不表示已经取得论文DOI。

## 包含什么

- 两份前端逐图CSV：各43,860行，共87,720行，包含原始输出与共同后处理结果；另保留早期D/seed11记录，后者与最终记录重叠，不是额外测试集。
- 既有总体、逐场景、留一场景、完整G4和场景Bootstrap结果；六次融合训练的内部选择节点及FDCT开发节点。
- 原计时协议1,400次调用和驻留协议4,224次调用（包括1,056次预热、3,168次正式测量），及配对、调度和保存的模型状态记录。
- 2,498个目录、305条早期排除原因和最终2,193对样本的历史元数据；最终清单空`exclusions`仅指后续新增排除0。
- 两类CPU分析脚本、配置记录、结果字段说明、补充小节索引、文件来源与哈希。

## 不包含什么

不含TransCG原始RGB、深度、真值、掩码、图4图像或缓存NPZ；不含模型权重、完整历史逐像素误差数组、第三方网络实现、论文PDF、AI评审、邮件、私人账户信息和内部旧稿。原数据应从[TransCG官方入口](https://graspnet.net/transcg)获得。

这套材料用于检查已报告的分析，不能从零训练/推理复现全部实验，不能从逐图汇总精确重建总体P95/P99，也不能重新认证全部历史GPU输出。五组TDCNet历史误差数组校验和以及驻留输出等价性的既有限制继续保留。

## 先检查包，不自动重做统计

```bash
python -B analysis/verify_release.py
```

检查器只核对文件哈希、记录键、计数与包结构，不运行模型、不读像素、不重算误差或Bootstrap。`analysis/test_sensitivity.py`是已有的小型合成单元测试，不使用实验样本。

需要复算已有CSV时，参见[分析脚本说明](docs/REPRODUCTION.md)。这次打包没有运行实验样本上的统计复算；已保留历史统计结果，不能将打包校验称为一次新的完整实验复现。

## 结论边界

固定D435→L515、320×240、TransCG单子集、两个固定前端检查点、单机计时。`D`指TDCNet-local，`FDCT`指FDCT-local。FDCT完整G4为0/3满足；六项驻留节省均不足15%。不同训练历史不用于架构排序；受限V-FUSE不是原方法性能下界；不主张统计等价或机器人任务收益。

配置中的`LOCAL_PROJECT`等为脱敏后的历史定位标签，不是本仓库中的真实训练路径。所有原字节复制、脱敏和结构调整均在`PUBLIC_FILE_MANIFEST.json`中注明，原始历史记录未被回写。

## 权利说明

本次尚未给整仓库授予统一的MIT/CC BY等复用许可；公开查阅不等于改变第三方材料原许可。具体见[RIGHTS_AND_LICENSES.md](RIGHTS_AND_LICENSES.md)。这种安排避免在未作出许可选择时替作者自动授予广泛复用权；后续选择自有代码/记录许可证时再明确范围。
