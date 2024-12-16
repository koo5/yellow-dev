
import { sort_items } from './orderable.svelte';

let active_account_id = $state(null);
let accounts = $state({});
let accounts_ordered = $derived(sort_items(accounts));
let active_account = $derived(() => {
 if (active_account_id === null) return null;
 return accounts[active_account_id];
});



