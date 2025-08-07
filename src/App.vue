<template>
  <div id="app">
    <nav>
      <router-link to="/">Map</router-link> |
      <router-link to="/chart">Parking statistics</router-link>
    </nav>

    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
#app {
  text-align: center;
}
</style>
