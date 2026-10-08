# Research Report: Maritime Channel Dredging & Masterplan Capacity (Phases 197-198)

## 1. Statutory Grounding
- **Decree 58/2017/NĐ-CP & Decree 57/2024/NĐ-CP**: Management of maritime shipping channels, port waters, and capital/maintenance dredging operations.
- **Decision 1579/QĐ-TTg (2021)**: Master Plan for Development of Vietnam Seaport System to 2030, vision to 2050 (Special, Class I, II, III seaport classification).
- **PIANC Report No. 121 / IMO MSC.1/Circ. 1475**: Under Keel Clearance (UKC) standard guidelines and dynamic squat formulas.

## 2. Mathematical & Algorithmic Logic
- **Dynamic Ship Squat in Shallow Water (Barrass formula)**:
  $$S_{quat} = \frac{C_b \cdot V^2}{100} \cdot K_h$$
  Where $C_b$ is block coefficient, $V$ is vessel speed (knots), and $K_h = 1.0$ for open water or $2.0$ for confined channels ($h/T < 1.2$).
- **Under Keel Clearance (UKC)**:
  $$Gross\_UKC = Channel\_Depth + Tide - Maximum\_Draft$$
  $$Net\_UKC = Gross\_UKC - (Squat + Wave\_Swell\_Allowance + Mud\_Sediment\_Allowance)$$
  Clearance is granted if $Net\_UKC \ge Safety\_Margin$ (typically $0.3\text{m}$ to $0.5\text{m}$ for inland/port waters per Decree 58/2017).
- **Seaport Wharf Throughput Capacity (Decision 1579 Masterplan)**:
  $$Q_{annual} = \frac{T_{op} \cdot N_{berth} \cdot P_{handling} \cdot K_{util}}{t_{turnaround}}$$
  Assesses berth occupancy rate $\rho = \frac{\lambda}{\mu \cdot c}$ against statutory queuing service limits ($\le 70\%$ for container/dry bulk berths).
