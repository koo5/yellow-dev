# Development Guidelines for Yellow Project

## Build, Lint & Test Commands
- Build: `npm run build` or `vite build` (client/admin)
- TypeCheck: `npm run typecheck` or `tsc --noEmit`
- Test (all): `npm test` or `vitest`
- Test (single): `vitest path/to/test.test.ts`
- Format: `prettier --config prettier-libersoft.json --write src/**/*.{js,ts,svelte}`

## Code Style
- Formatting: Prettier with custom config (1-space tabs, single quotes)
- Naming: camelCase for variables/functions, PascalCase for classes/interfaces
- Components: kebab-case.svelte files, camelCase props
- Files: kebab-case for components, camelCase for utilities
- Types: Prefer explicit typing, strict mode, but noImplicitAny disabled
- Errors: Custom error classes with descriptive names and inheritance
- Logging: Structured logging with Pino; include context data

## Architecture
- Small, focused components with clear responsibilities
- Svelte for UI components with TypeScript support
- Modules system for extensible functionality

This file is meant for Claude and other AI assistants to understand project conventions.