<template>
<<<<<<< HEAD
  <div id="app">
    <GoogleMap />
  </div>
=======
  <header>
    <img alt="Vue logo" class="logo" src="./assets/logo.svg" width="125" height="125" />

    <div class="wrapper">
      <HelloWorld msg="You did it!" />
    </div>
  </header>

  <main>
    <HelloWorld />
  </main>
>>>>>>> ff278876acecb12fd5451db24298f9212a7bbde2
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
