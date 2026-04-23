# Live in a Week — Phase 1 Milestones

## M1: Project Scaffolding ✅
- [x] Docker Compose (PostgreSQL + PgAdmin + Backend)
- [x] FastAPI skeleton with CORS
- [x] SQLAlchemy async engine + session
- [x] Alembic migrations setup
- [x] Config via pydantic-settings
- [x] Git init backend/
- [x] SQLAlchemy models (User, OTPCode, Task)

## M2: Auth System ✅
- [x] Auth service (OTP gen/verify, JWT)
- [x] WhatsApp service (send OTP via Meta API)
- [x] Auth API endpoints
- [x] Auth Pydantic schemas
- [x] `get_current_user` dependency

## M3: Task CRUD API ✅
- [x] Task service (CRUD + filters)
- [x] Task API endpoints
- [x] Task Pydantic schemas

## M4: Sync Engine ✅
- [x] Sync schemas (pull/push)
- [x] Sync service (version-based conflict resolution)
- [x] Sync API endpoints

## M5: WhatsApp Bot ✅
- [x] Webhook verification endpoint
- [x] Command parser
- [x] Task command handler
- [x] Message signature verification

## M6: Extension Sync Layer ← NEXT
- [ ] apiClient.ts (fetch + JWT)
- [ ] syncService.ts (pull/push/background)
- [ ] Modify chromeStorage.ts (cache tracking)
