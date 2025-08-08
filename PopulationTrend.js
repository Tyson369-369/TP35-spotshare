// PopulationTrend.js
d3.json("melbourne_trend.json").then(data => {
  const svg = d3.select("#background-trendline")
    .attr("class", "trendline-bg")
    .attr("width", window.innerWidth)
    .attr("height", 200);

  const margin = { top: 20, right: 30, bottom: 30, left: 40 };
  const width = +svg.attr("width") - margin.left - margin.right;
  const height = +svg.attr("height") - margin.top - margin.bottom;

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleLinear()
    .domain(d3.extent(data, d => d.year))
    .range([0, width]);

  const y = d3.scaleLinear()
    .domain([
      d3.min(data, d => d.greaterMelbourne) * 0.98,
      d3.max(data, d => d.greaterMelbourne) * 1.02
    ])
    .range([height, 0]);

  const line = d3.line()
    .x(d => x(d.year))
    .y(d => y(d.greaterMelbourne))
    .curve(d3.curveMonotoneX);

  g.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-opacity", 0.2)
    .attr("stroke-width", 2.5)
    .attr("d", line);

  // Tooltip on hover
  svg.on("mousemove", function(event) {
    const [mx] = d3.pointer(event);
    const year = Math.round(x.invert(mx - margin.left));
    const match = data.find(d => d.year === year);
    if (match) {
      svg.selectAll(".tooltip").remove();
      svg.append("text")
        .attr("class", "tooltip")
        .attr("x", mx)
        .attr("y", 40)
        .attr("fill", "black")
        .attr("opacity", 0.8)
        .style("font-size", "14px")
        .text(`📈 ${year}: ${match.greaterMelbourne.toLocaleString()}`);
    }
  });
});
