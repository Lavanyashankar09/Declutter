# Technical

*Generated on 2026-02-05 16:18*

---

## From: api-test-9-25.log

- Redis reconnection issue - thought Sarah's PR addressed this, need follow up
  `#redis` `#bug` `#pr`

## From: api_responses_sample.json

- API endpoints documented with roles and permissions structure - staging environment with 47 users across admin/editor/viewer roles
  `#api` `#staging` `#roles`

## From: component.tsx

- UserDashboard component needs complete rewrite for new design system - memory leak during fetch, extract shared hook, add error boundary
  `#react` `#component` `#rewrite` `#memory-leak`

## From: dependencies_audit.csv

- Dependencies audit shows lodash should be removed, cmdk major version available, consider replacing cypress with playwright
  `#dependencies` `#audit` `#upgrade`

## From: quick_notes.md

- Use PgBouncer for connection pooling - lighter weight than pgpool-II
  `#database` `#postgresql` `#optimization`

- Docker compose watch for hot reload in dev, Jenkins pipeline takes 18min - ask DevOps about GitHub Actions
  `#docker` `#devops` `#ci`

- SSH tunnel command for staging DB: ssh -L 5433:staging-db.internal:5432 bastion.example.com
  `#ssh` `#database` `#staging`

- Git aliases for log, unstage, last commands
  `#git` `#aliases` `#productivity`

## From: random_thoughts.md

- New API design should use GraphQL instead of REST - need to think more about this
  `#api` `#graphql` `#design`

## From: misc_snippets.py

- Date parser utility with multiple format support, CSV to JSON converter, retry wrapper with exponential backoff needed
  `#python` `#utilities` `#date-parsing`

## From: schema_notes.sql

- Database schema needs normalization of permissions table, add indexes, fix timezone handling in created_at
  `#database` `#schema` `#migration`

## From: server.py

- Flask server needs refactoring - proper auth middleware, environment variables, pagination, email validation
  `#flask` `#python` `#refactor` `#auth`

## From: system_logs.txt

- System logs show slow query (523ms), rate limiting issues, and unhandled UserNotFoundError
  `#monitoring` `#performance` `#errors`

## From: env_config_notes.txt

- Comprehensive environment configuration reference for all services including database, Redis, AWS, auth, monitoring
  `#configuration` `#environment` `#devops`
