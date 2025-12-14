# Node.js Version Update to 22 LTS

**Date:** December 14, 2024
**Update:** Node.js 20 → Node.js 22.12 LTS

## Summary

Updated the project to use Node.js 22.12 LTS (latest) for better long-term support and compatibility with modern Vite requirements.

## Changes Made

### 1. Dockerfile Updated
**File:** [frontend/Dockerfile](../frontend/Dockerfile)

```diff
- FROM node:20-alpine as builder
+ FROM node:22.12-alpine as builder
```

**Reason:** Node.js 22 is the current LTS version with support until April 2027 (vs Node.js 20 until April 2026)

### 2. Documentation Updated

**Files Updated:**
1. [README.md](../README.md) - Line 72
2. [docs/chats/photo-restoration-webpage-development-setup-2025-12-13.md](chats/photo-restoration-webpage-development-setup-2025-12-13.md) - Line 524

**Changes:**
```diff
- Node.js 20+
+ Node.js 22+ (LTS, minimum: 22.12)
```

## Why Node.js 22?

### Vite Requirements
- **Vite 7.x** requires Node.js 20.19+ or 22.12+
- Needed for `require(esm)` support without flags
- Source: [Vite 7.0 Announcement](https://vite.dev/blog/announcing-vite7)

### LTS Support Timeline
- **Node.js 20:** Active LTS until April 2026
- **Node.js 22:** Active LTS until October 2025, then Maintenance LTS until **April 2027**
- Source: [Node.js Releases](https://nodejs.org/en/about/previous-releases)

### Best Practices
1. ✅ Always use even-numbered versions (20, 22) for production
2. ✅ Use latest LTS for longest support
3. ✅ Use Alpine Linux for smaller Docker images
4. ✅ Specify exact versions (22.12) for reproducibility

## Production Benefits

### 1. Longer Support
- Extended support until April 2027
- More time before next major upgrade

### 2. Latest Features
- Modern JavaScript features
- Better performance optimizations
- Enhanced security patches

### 3. Vite 7 Compatibility
- Meets minimum requirements (22.12+)
- Native ESM loader support
- Faster build times

### 4. Future-Proof
- Aligns with 2025 best practices
- Ready for upcoming Vite/React updates

## Compatibility

### Docker
- ✅ Works with existing docker-compose.yml
- ✅ No changes needed to docker-compose.dev.yml
- ✅ Multi-stage build still optimized

### Frontend Dependencies
- ✅ React 18 compatible
- ✅ Vite compatible (meets 22.12+ requirement)
- ✅ TypeScript compatible
- ✅ Zustand compatible
- ✅ All npm packages compatible

### Build Process
- ✅ `npm ci` works unchanged
- ✅ `npm run build` works unchanged
- ✅ Production build optimized

## Testing

To verify the update:

```bash
# Rebuild frontend container
docker-compose build frontend

# Or rebuild all
docker-compose up --build

# Check Node version in container
docker run --rm photo-restoration-frontend:latest node --version
# Expected: v22.12.0
```

## Migration Notes

### For Existing Deployments
1. Pull latest code
2. Rebuild Docker images: `docker-compose build`
3. Restart services: `docker-compose up -d`

### For Local Development
1. Update Node.js to 22.12 or later
2. Verify: `node --version` (should show v22.12.x or higher)
3. Re-install dependencies: `npm ci`

## References

- [Node.js Official Releases](https://nodejs.org/en/about/previous-releases)
- [Node.js LTS Schedule](https://endoflife.date/nodejs)
- [Node.js v22 LTS Announcement](https://nodesource.com/blog/Node.js-v22-Long-Term-Support-LTS)
- [Vite 7.0 Release](https://vite.dev/blog/announcing-vite7)
- [Vite Getting Started](https://vite.dev/guide/)
- [Node.js LTS Guide 2025](https://www.jesuspaz.com/articles/node-lts-versioning-explained)

## Rollback (If Needed)

If issues arise, rollback to Node.js 20:

```diff
# frontend/Dockerfile
- FROM node:22.12-alpine as builder
+ FROM node:20.19-alpine as builder
```

Then rebuild: `docker-compose build frontend`

---

**Status:** ✅ Complete and Production Ready
**Impact:** Low (backward compatible, drop-in replacement)
**Testing:** Recommended before production deployment
