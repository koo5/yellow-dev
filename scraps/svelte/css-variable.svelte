<script>
 import { createEventDispatcher, onMount } from 'svelte';
 export let visible = true;
 const dispatch = createEventDispatcher();

 let size = 38;
 let dynamicColor = 'blue';

 onMount(() => {
  setInterval(() => {
   size = 38 + Math.sin(Date.now() / 200) * 20;
   dynamicColor = `hsl(${Math.sin(Date.now() / 200) * 180 + 180}, 100%, 50%)`;
  }, 10);
 });

 function handleKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
   event.preventDefault();
   dispatch('click');
  }
 }
</script>

<style>
 .scroll-down {
  position: fixed;
  display: flex;
  align-items: center;
  justify-content: center;
  right: 20px;
  bottom: 70px;
  min-width: var(--size);
  width: var(--size);
  min-height: var(--size);
  height: var(--size);
  padding: 10px;
  border: 2px solid #aaa;
  border-radius: 50%;
      background-color: var(--my-color);
  box-shadow: var(--shadow);
  cursor: pointer;
 }

 .scroll-down img {
  width: 32px;
  height: 32px;
 }
</style>

{#if visible}
 <div class="scroll-down" style="--size: {size}px; --my-color: {dynamicColor}; " role="button" tabindex="0" on:click on:keydown={handleKeydown}>
 {size}
  <img src="img/caret-down-gray.svg" alt="˅" />
 </div>
{/if}
