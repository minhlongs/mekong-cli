---
phase: testing
title: String Calculator Testing Strategy
description: Test cases for String Calculator
---

# Testing Strategy

## Unit Tests

### Component: add()
- [ ] Test case 1: Empty string returns 0
- [ ] Test case 2: "1" returns 1
- [ ] Test case 3: "1,2" returns 3
- [ ] Test case 4: "1,2,3,4" returns 10
- [ ] Test case 5: "1\n2,3" returns 6
- [ ] Test case 6: "//;\n1;2" returns 3
- [ ] Test case 7: "-1,2" throws "negatives not allowed: -1"
- [ ] Test case 8: "-1,-2" throws "negatives not allowed: -1,-2"
