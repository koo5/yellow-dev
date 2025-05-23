Build a Svelte 5 accordion component, name it Accordion2.svelte.  

* take a snippet for rendering the body of each item. and a snippet for rendering the "titleLeft" of each item and a snippet for rendering "titleRight" for each item. 

* take a list of items to render. 

* take a callback function named itemKeyGetter.
* - accordion will need this to maintain a list of expanded / collapsed state for each item 

* take a mode parameter which is either single or multi controlling if only one item can be expanded at a time or more 

* expand all / collapse all from the parent component
* - This will make it possible for the parent to expand all or collapse all when a media query changes.

* take a prop named defaultItemState which might be collapsed or expanded

Build a storybook page with example usages. 
