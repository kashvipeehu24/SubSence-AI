document.addEventListener('DOMContentLoaded', () => {
  const chartContainer = document.querySelector('[data-chart="spending"]');

  if (!chartContainer) return;

  const values = [68, 82, 74, 91, 96, 100];
  const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  const width = 560;
  const height = 220;
  const padding = { top: 18, right: 16, bottom: 36, left: 16 };

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Monthly spending trend chart');

  const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  const area = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  const points = [];

  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  values.forEach((value, index) => {
    const x = padding.left + (index / (values.length - 1)) * chartWidth;
    const normalized = (value - minValue) / (maxValue - minValue || 1);
    const y = padding.top + chartHeight - normalized * chartHeight;
    points.push({ x, y, value });
  });

  const lineD = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ');
  const areaD = `${lineD} L ${points[points.length - 1].x.toFixed(2)} ${height - padding.bottom} L ${points[0].x.toFixed(2)} ${height - padding.bottom} Z`;

  line.setAttribute('d', lineD);
  line.setAttribute('fill', 'none');
  line.setAttribute('stroke', '#63e4c0');
  line.setAttribute('stroke-width', '3');
  line.setAttribute('stroke-linecap', 'round');
  line.setAttribute('stroke-linejoin', 'round');

  area.setAttribute('d', areaD);
  area.setAttribute('fill', '#2a8f6d');

  svg.appendChild(area);
  svg.appendChild(line);

  points.forEach((point, index) => {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', point.x);
    circle.setAttribute('cy', point.y);
    circle.setAttribute('r', '5');
    circle.setAttribute('fill', '#4f8cff');
    circle.setAttribute('stroke', '#f4f7fb');
    circle.setAttribute('stroke-width', '2');
    svg.appendChild(circle);

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', point.x);
    label.setAttribute('y', height - 12);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', '#92a7c0');
    label.setAttribute('font-size', '12');
    label.textContent = labels[index];
    svg.appendChild(label);
  });

  chartContainer.appendChild(svg);
});
