<template>
  <div id="app">
    <GoogleMap />
  </div>
</template>

<script>
import GoogleMap from './components/GoogleMap.vue'

export default {
  name: 'App',
  components: {
    GoogleMap,
  },
}
</script>

<style>
#app {
  text-align: center;
}
</style>
