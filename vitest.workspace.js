import { defineWorkspace } from 'vitest/config'

export default defineWorkspace([
  "./yellow-client/vitest.config.ts",
  "./yellow-admin/vite.config.js"
])
