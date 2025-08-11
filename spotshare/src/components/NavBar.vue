<template>
  <header class="navbar">
    <div class="logo">
      <img src="@/assets/spotshare-logo.png" alt="SpotShare Logo" class="logo-img" />
      <span class="logo-text">SpotShare</span>
    </div>
    <nav class="nav-links">
      <RouterLink to="/dashboard">Dashboard</RouterLink>
      <RouterLink to="/find-parking">Find Parking</RouterLink>
      <RouterLink to="/trends">Mobility Trends</RouterLink>
      <RouterLink to="/history">Find my Spot</RouterLink>
      <RouterLink to="/eco-score">Eco Score</RouterLink>
    </nav>
    <div class="profile-circle"></div>
  </header>
</template>

<script setup>
// Nothing needed here yet
</script>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background-color: #ffffff;
  border-bottom: 1px solid #ddd;
  font-family: 'Segoe UI', sans-serif;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-img {
  height: 32px;
  width: 32px;
  border-radius: 8px;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  text-decoration: none;
  color: #333;
  font-weight: 500;
}

.nav-links a.router-link-exact-active {
  color: #27ae60;
  border-bottom: 2px solid #27ae60;
}

.profile-circle {
  width: 35px;
  height: 35px;
  background-color: #ccc;
  border-radius: 50%;
}
</style>
