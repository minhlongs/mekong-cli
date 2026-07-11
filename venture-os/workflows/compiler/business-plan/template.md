# Business Plan — {{venture.name}}

## Tổng quan doanh nghiệp / Business Overview
- **Venture:** {{venture.name}} ({{venture.type}})
- **ID:** {{venture.id}}
- **Phase:** {{lifecycle.current_phase}} — {{lifecycle.phase_label}}
- **Compiled:** {{compiled_at}}

## Vấn đề / Problem
{{idea.description}}

## Thị trường / Market
{{#market}}
**TAM:** {{market.tam}} | **SAM:** {{market.sam}} | **SOM:** {{market.som}}

**Xu hướng / Trends:**
{{#market.trends}}
- {{.}}
{{/market.trends}}

**Đối thủ / Competitors:**
{{#market.competitors}}
- {{.}}
{{/market.competitors}}
{{/market}}

## Giải pháp / Solution
[Outline how the venture addresses the problem]

## Kế hoạch tài chính / Financial Plan
[High-level revenue model and cost structure]

## Kế hoạch MVP / MVP Plan
[Key milestones and timeline]

---
> Compiled by VentureOS
