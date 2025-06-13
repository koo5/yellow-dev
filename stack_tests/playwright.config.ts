import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
 testDir: './',
 fullyParallel: false,
 forbidOnly: !!process.env.CI,
 retries: process.env.CI ? 2 : 0,
 workers: 1,
 reporter: [
  ['html'],
  ['json', { outputFile: 'test-results/results.json' }]
 ],
 use: {
  trace: 'on-first-retry',
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
  ignoreHTTPSErrors: true
 },

 projects: [
  {
   name: 'chromium',
   use: { ...devices['Desktop Chrome'] },
  }
 ]
});