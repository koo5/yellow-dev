
interface Orderable
{
 order_key: number;
}



export function sort_items(itemsMap: Map<any, Orderable>) {
 check_consistency(itemsMap);
 let values = Object.values(itemsMap);
 warn_of_items_with_same_order_key(values);
 return values.sort((a, b) => a.order_key - b.order_key);
}


function check_consistency(map: Map<any, Orderable>) {
 warn_of_items_with_same_order_key(Object.values(map));
 warn_of_items_with_wrong_ids(map);
}


function warn_of_items_with_same_order_key(values: Orderable[]) {
 let order_keys = values.map(v => v.order_key);
 let order_keys_set = new Set(order_keys);
 if (order_keys.length !== order_keys_set.size) {
  console.warn('Items with duplicate order_key detected.');
  for (let item of values) {
   let found = false;
   for (let item2: Orderable of values) {
    if (item !== item2 && item.order_key === item2.order_key) {
     if (found) {
      console.warn('item', item, ' has same order_key as item', item2);
      break;
     }
     found = true;
    }
   }
  }
 }
}


function warn_of_items_with_wrong_ids(map: Map<any, Orderable>) {
 for (let key of Object.keys(map)) {
  if (key !== map[key].id) {
   console.warn('Item with wrong id detected:', key, map[key]);
  }
 }
}


