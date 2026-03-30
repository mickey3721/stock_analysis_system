<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f5f5f5;
  max-width: 100%;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  background: #f5f5f5;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  body {
    font-size: 14px;
  }
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}
::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 2px;
}
::-webkit-scrollbar-track {
  background: #f5f5f5;
}
</style>
