# Product Requirements Document: User Onboarding Redesign

## Overview

The current onboarding flow has a 34% drop-off rate at step 3. This redesign simplifies the flow from 7 steps to 4, focusing on time-to-value.

## Goals

- Reduce onboarding drop-off rate from 34% to under 15%
- Decrease time-to-first-action from 8 minutes to under 3 minutes
- Increase 7-day retention by 20%

## User Stories

1. As a new user, I want to see the product's value immediately so that I understand why I signed up
1. As a new user, I want to skip optional setup steps so that I can start using the product faster
1. As a returning user, I want to resume onboarding where I left off so that I don't repeat steps

## Proposed Flow

| Step | Screen | Required? | Estimated Time |
|------|--------|-----------|----------------|
| 1 | Welcome + name | Yes | 15 seconds |
| 2 | Choose use case | Yes | 20 seconds |
| 3 | First action (guided) | Yes | 60 seconds |
| 4 | Invite team (skippable) | No | 30 seconds |

## Success Metrics

### Primary

- Onboarding completion rate > 85%
- Time-to-first-action < 3 minutes

### Secondary

- NPS score for onboarding > 40
- Support tickets related to onboarding reduced by 50%

## Timeline

- **Week 1-2**: Design and prototype
- **Week 3-4**: Engineering implementation
- **Week 5**: QA and user testing
- **Week 6**: Staged rollout (10% -> 50% -> 100%)

## Open Questions

- Should we A/B test the new flow against the current one?
- Do we need separate flows for B2B vs B2C users?
- What analytics events do we need for funnel tracking?
