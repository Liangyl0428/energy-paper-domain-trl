# 单篇文献相对于同领域 TRL

这个仓库实现单篇论文（或其他带细主题和技术载体的文献）相对于同行领域的 TRL 对比。输入一篇目标文献和文献库，输出目标文献的每个细主题分别对应的同行统计：同行数量、中位数、均值、四分位区间、IQR、等级分布以及目标 TRL 与同行中位数的差值。

同领域定义为“同一个已确认细主题 + 同一个技术载体”。一篇文献有多个细主题时，算法为每个细主题建立独立同行集合并分别计算；不会把多个主题合成一个领域。同行按文献 ID 和标准化标题去重，且排除目标文献。没有有效 1–9 TRL 的记录不进入数值统计，但会保留在候选记录计数中。少于默认 20 篇有效同行时返回 `insufficient_peers`，不强行填补。

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m energy_paper_domain_trl --target target.json --corpus papers.jsonl --output comparison.json
```

记录格式示例：

```json
{"doc_id":"W1","title":"...","topic_codes":["CFT-0003","CFT-0100"],"technology_carrier":"battery","trl_level":6}
```

输出中的同行统计是语料库条件下的相对位置，不是技术成熟度认证；同行集合的主题标签、技术载体和 TRL 质量决定比较结果的可靠性。
