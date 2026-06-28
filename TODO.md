# TODO - LetsQuiz Landing/Stats/FAQ Backend

## Phase 1: Contract alignment + correctness
- [ ] Update `/api/statistics/` response fields to exactly match spec.

- [ ] Fix landing page statistics subsection to match spec keys and dynamic values (no hardcoded satisfaction unless stored/configured).
- [ ] Refactor shared statistics calculation into `apps/landing/services.py` (single source of truth).

## Phase 2: Platform statistics
- [ ] Implement `top_categories`, `most_active_users`, `newest_quizzes` per spec (avoid empty placeholders).

## Phase 3: Performance + caching
- [ ] Optimize statistics calculations with aggregates; avoid N+1 loops.
- [ ] Ensure landing endpoint caching is coherent with dynamic stats (cache strategy refined).

## Phase 4: Security
- [ ] Harden newsletter/contact spam protection (server-side validations; ensure throttles are applied).
- [ ] Ensure admin-only endpoints use consistent permissions.

## Phase 5: Swagger/OpenAPI + documentation
- [ ] Add/enable Swagger/OpenAPI (drf-spectacular or drf-yasg depending on dependencies).
- [ ] Annotate endpoints with schema/serializer examples.

## Phase 6: Tests
- [ ] Update `apps/landing/tests.py` to assert spec-required fields for `/api/statistics/` and `/api/landing/`.
- [ ] Add tests for platform statistics fields presence.

## Phase 7: Verify
- [ ] Run migrations (if needed).
- [ ] Run `python manage.py test`.
- [ ] Quick manual request checks for each endpoint.

