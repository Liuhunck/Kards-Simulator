# Kards-Simulator

Kards Simulator (engine-first, Python 3).

## Quick start

### 1) Create venv + install

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Dev deps (tests):

```powershell
pip install -e .[dev]
pytest
```

### 2) Run the CLI prototype

```powershell
python -m kards_sim
```

This is a minimal engine prototype with:

-   2 players, deck/hand/discard
-   2-lane board model (frontline/supportline) with 5 columns
-   Actions: play unit, play order (MVP: damage), attack, end turn

## Roadmap

The goal is a faithful KARDS rules engine. Many mechanics are intentionally stubbed or simplified in this first prototype.


## Test cmd

```bash
d 2 0; e; d 0 1; d 0 2; e; a 0 0; k 3 2;
```

```
Major power: japan
Ally: france
HQ: 特鲁克

japan:
4x (0K) 深挖
1x (1K) 九三式装甲车
3x (1K) 九四式轻装甲车
4x (1K) 扩张
3x (1K) 骑兵第十五联队
2x (1K) 搜索第三十三联队
1x (1K) 转变战法
2x (1K) 佐镇第五特别陆战队
1x (2K) 搜索第十联队
1x (2K) 亡命之计
2x (3K) 步兵第百五十一联队
1x (3K) 第二挺进团
2x (3K) 京都联队
1x (3K) 侦察队
1x (3K) Ki-30 九七轻爆
1x (3K) Ki-46 百式司侦
2x (4K) 鲭江联队

france:
1x (0K) 出动
2x (0K) 第 13 龙骑兵团
1x (1K) 荣誉与忠诚
2x (2K) 第 110 摩托化步兵团
1x (3K) 迪勒计划

%%36|5C666B7lhHlFnrrktCtMvc;6CrVt1tFtGtJx5;6x7e;5ZtQ
```

```
Major power: usa
Ally: britain
HQ: 瑟堡

usa:
2x (0K) 胁迫
2x (1K) 航母掩护
2x (1K) 为了自由
4x (2K) USS 沙利文兄弟号
2x (3K) 航母打击群
2x (3K) 空中掩护
1x (3K) 霹雳师
2x (3K) PB2Y 科罗纳多
2x (3K) SC 海鹰
1x (3K) USS 密苏里号
2x (4K) 第 41 步兵团
2x (4K) 三巨头
2x (5K) USS 约克城号
1x (6K) 战略轰炸
1x (6K) F7F 虎猫

britain:
1x (1K) 米德尔塞克斯团
4x (1K) 米色团
3x (3K) 边防团
1x (3K) 虎蛾
2x (4K) 前进观察员

%%52|bEtYv6v9vYw8;blbqohqYsGsHu6u8v7vRvU;pU;sUvS
```