
import {flushSync} from 'svelte';
import {expect, test} from 'vitest';
import {
    accounts,
    active_account,
    accounts_ordered,
    active_account_id,
} from '$lib/accounts.svelte';


test('active_account_id', async () => {
    expect(active_account_id).toBe(null);
    flushSync();
    expect(active_account_id).toBe(null);
    active_account_id.set(1);
    flushSync();
    expect(active_account_id).toBe(1);
});

test('accounts', async () => {
    expect(accounts).toEqual({});
    flushSync();
    expect(accounts).toEqual({});
    accounts.set({1: {name: 'Alice'}});
    flushSync();
    expect(accounts).toEqual({1: {name: 'Alice'}});
});

test('accounts_ordered', async () => {
    expect(accounts_ordered).toEqual([]);
    flushSync();
    expect(accounts_ordered).toEqual([]);
    accounts.set(
        {
            1: {name: 'Alice', id: 1, order_key: 4},
            2: {name: 'Bob', id: 2, order_key: 2},
            3: {name: 'Charlie', id: 3, order_key: 3},
            4: {name: 'David', id: 4, order_key: 0},
        }
    );
    flushSync();
    expect(accounts_ordered).toEqual([
        {name: 'David', id: 4, order_key: 0},
        {name: 'Bob', id: 2, order_key: 2},
        {name: 'Charlie', id: 3, order_key: 3},
        {name: 'Alice', id: 1, order_key: 4},
    ]);
});


