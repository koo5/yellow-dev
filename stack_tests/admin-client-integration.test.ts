import { test, expect, Page } from '@playwright/test';

test.describe('Admin-Client Integration', () => {
 let adminPage: Page;
 let clientPage: Page;

 test.beforeAll(async ({ browser }) => {
  adminPage = await browser.newPage();
  clientPage = await browser.newPage();
 });

 test.afterAll(async () => {
  await adminPage.close();
  await clientPage.close();
 });

 test('add user in admin and login in client simultaneously', async () => {
  // Navigate to both applications
  await Promise.all([
   adminPage.goto('http://localhost:4000'),
   clientPage.goto('http://localhost:3000')
  ]);

  // Wait for both pages to load
  await Promise.all([
   adminPage.waitForSelector('[data-testid="admin-login"]', { timeout: 10000 }),
   clientPage.waitForSelector('[data-testid="client-ready"]', { timeout: 10000 })
  ]);

  // Admin: Login as admin
  await adminPage.fill('[data-testid="admin-username"]', 'admin');
  await adminPage.fill('[data-testid="admin-password"]', 'admin');
  await adminPage.click('[data-testid="admin-login-button"]');

  // Admin: Wait for dashboard and navigate to users
  await adminPage.waitForSelector('[data-testid="admin-dashboard"]');
  await adminPage.click('[data-testid="users-menu"]');

  // Admin: Add new user
  await adminPage.click('[data-testid="add-user-button"]');
  await adminPage.fill('[data-testid="user-name-input"]', 'testuser');
  await adminPage.fill('[data-testid="user-password-input"]', 'testpass123');
  await adminPage.click('[data-testid="save-user-button"]');

  // Admin: Verify user was created
  await expect(adminPage.locator('[data-testid="user-list"]')).toContainText('testuser');

  // Client: Login with the newly created user
  await clientPage.fill('[data-testid="client-username"]', 'testuser');
  await clientPage.fill('[data-testid="client-password"]', 'testpass123');
  await clientPage.click('[data-testid="client-login-button"]');

  // Client: Verify successful login
  await expect(clientPage.locator('[data-testid="client-dashboard"]')).toBeVisible();
  await expect(clientPage.locator('[data-testid="user-profile"]')).toContainText('testuser');
 });
});