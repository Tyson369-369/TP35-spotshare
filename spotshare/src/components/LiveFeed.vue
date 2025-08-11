<!-- src/components/LiveFeed.vue -->
<template>
  <div class="live-feed">
    <h2 class="feed-heading">
      <img src="@/assets/bell-icon.png" alt="Bell Icon" class="icon" />
      Live Feed
    </h2>
    <p class="sub">Real-time parking updates</p>

    <!-- Sample update -->
    <div class="feed-card-1">
      <div>
        <strong>Sarah M.</strong> leaving in <span class="time">7 min</span> on Flinders Ln (1P)
      </div>
      <button class="notify">Notify Me</button>
    </div>

    <div class="feed-card-2">
      <div class="feed-left">
        <img src="@/assets/clock-icon.jpg" alt="clock" class="icon" />
        <div class="feed-text">
          <p>
            <strong>James K.</strong> requested your spot at <span class="highlight">5:30 PM</span>
          </p>
          <p class="location">Collins St</p>
        </div>
      </div>

      <div class="action-buttons">
        <button class="approve-btn">✓ Approve</button>
        <button class="decline-btn">✕ Decline</button>
      </div>
    </div>

    <div class="feed-card-1">
      <div>
        <strong>Emma W.</strong> leaving in <span class="time">15 min</span> on Bourke St (2P)
      </div>
      <button class="notify">Notify Me</button>
    </div>

    <!-- Share button -->
    <div class="share-box">
      <p>Share your parking spot when you leave</p>
      <button class="share-btn">Share My Spot</button>
    </div>
  </div>
</template>

<style scoped>
.feed-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
}

.icon {
  height: 24px;
  width: 24px;
}

.live-feed {
  font-family: 'Segoe UI', sans-serif;
}

.sub {
  color: #777;
  margin-bottom: 1rem;
}

.feed-card-1 {
  background-color: #fff9e6;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time {
  color: #007aff;
}

.notify {
  background-color: #e0f0ff;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  color: #007aff;
  cursor: pointer;
}

.share-box {
  margin-top: 2rem;
  background-color: #eafaf1;
  padding: 1rem;
  border-radius: 10px;
  text-align: center;
}

.share-btn {
  margin-top: 0.5rem;
  background: linear-gradient(to right, #4cd964, #5ac8fa);
  border: none;
  color: white;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.feed-card-2 {
  background-color: #f4f9fc;
  padding: 1rem;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.feed-left {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.feed-text p {
  margin: 0;
  line-height: 1.4;
}

.location {
  font-size: 0.9rem;
  color: #666;
}

.highlight {
  color: #2ecc71; /* green */
  font-weight: 600;
}

.icon {
  width: 20px;
  height: 20px;
  margin-top: 3px;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  margin-left: 28px; /* aligns under text block */
}

.approve-btn {
  background-color: #e9f9ed;
  border: 1px solid #2ecc71;
  color: #2ecc71;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
}

.decline-btn {
  background-color: #fdeaea;
  border: 1px solid #e74c3c;
  color: #e74c3c;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
}
</style>
