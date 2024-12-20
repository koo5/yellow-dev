
<!--
https://github.com/ghostebony/svelte-virtual/blob/main/src/lib/grid/Grid.svelte

<Grid itemCount={items.length} itemHeight={size} itemWidth={size}>
	{#snippet item({ index, style })}
		<div {style}>
			<Item {size} file={items[index].url} autoplay={false} />
		</div>
	{/snippet}
</Grid>

see also:
https://www.npmjs.com/package/svelte-inview
*↕️ Detects the scrolling direction.
-->
