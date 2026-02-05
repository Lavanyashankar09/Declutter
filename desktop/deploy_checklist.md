# Production Deploy Checklist

**Next deploy window: Saturday Feb 8, 2026 at 10pm EST**

## Pre-deploy
- [ ] All PRs merged to main
- [ ] Staging environment verified by QA
- [ ] Database migrations tested on staging
- [ ] Rollback plan documented
- [ ] On-call engineer confirmed (this week: Jamie)

## Deploy Steps
1. Enable maintenance mode
2. Run database migrations
3. Deploy backend services (auth-service first, then api-gateway)
4. Deploy frontend
5. Run smoke tests
6. Disable maintenance mode

## Post-deploy
- [ ] Monitor error rates for 30 min
- [ ] Check Datadog dashboards
- [ ] Send deploy notification to #engineering channel
- [ ] Update deploy log in Notion

## Notes
- The auth-service needs to go first because api-gateway depends on the new token format
- Last deploy had an issue with cache invalidation - keep an eye on Redis memory
- If anything goes wrong, rollback command: `./scripts/rollback.sh v2.3.1`
