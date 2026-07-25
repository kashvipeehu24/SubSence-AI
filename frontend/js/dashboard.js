document.addEventListener('DOMContentLoaded', () => {
  const statCards = document.querySelectorAll('.stat-card');
  const dashboardCards = document.querySelectorAll('.dashboard-card');
  const itemRows = document.querySelectorAll('.item-row');

  const revealElements = (elements, delay = 80) => {
    elements.forEach((element, index) => {
      element.style.opacity = '0';
      element.style.transform = 'translateY(18px)';

      setTimeout(() => {
        element.style.transition = 'all 0.45s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
      }, delay * index);
    });
  };

  revealElements(statCards, 90);
  revealElements(dashboardCards, 100);
  revealElements(itemRows, 60);

  document.querySelectorAll('.stat-card, .dashboard-card, .item-row').forEach((card) => {
    card.addEventListener('mouseenter', () => {
      card.style.transform = 'translateY(-4px)';
      card.style.borderColor = 'rgba(99, 228, 192, 0.35)';
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.borderColor = '';
    });
  });

  document.querySelectorAll('.stat-card h3').forEach((heading) => {
    const rawText = heading.textContent.trim();
    const numericValue = Number(rawText.replace(/[$,%]/g, '').replace(/,/g, ''));

    if (!Number.isFinite(numericValue)) return;

    const prefix = rawText.includes('$') ? '$' : '';
    const suffix = rawText.includes('%') ? '%' : '';
    const duration = 800;
    const stepTime = 24;
    const steps = Math.max(1, Math.round(duration / stepTime));
    const increment = numericValue / steps;
    let currentStep = 0;

    heading.textContent = `${prefix}0${suffix}`;

    const timer = setInterval(() => {
      currentStep += 1;
      const value = Math.min(Math.round(currentStep * increment), numericValue);
      heading.textContent = `${prefix}${value.toLocaleString()}${suffix}`;

      if (currentStep >= steps) {
        clearInterval(timer);
      }
    }, stepTime);
  });

  const healthRing = document.querySelector('.health-ring');
  if (healthRing) {
    const targetScore = 84;
    let currentScore = 0;

    const animateRing = setInterval(() => {
      currentScore += 1;
      healthRing.textContent = `${currentScore}%`;
      healthRing.style.background = `conic-gradient(var(--accent-2) ${currentScore}%, rgba(255,255,255,0.08) 0)`;

      if (currentScore >= targetScore) {
        clearInterval(animateRing);
        healthRing.textContent = `${targetScore}%`;
      }
    }, 18);
  }

  const trendChart = Array.from(document.querySelectorAll('.dashboard-card')).find((card) =>
    card.querySelector('h5')?.textContent.includes('Monthly Spending Trend')
  );

  const chartContainer = trendChart?.querySelector('div[style*="display: flex"]');
  const trendBars = chartContainer ? Array.from(chartContainer.children) : [];

  trendBars.forEach((bar, index) => {
    const style = bar.getAttribute('style') || '';
    const match = style.match(/height:\s*([0-9.]+%)/);
    const targetHeight = match ? match[1] : '0%';

    bar.style.height = '0%';
    bar.style.transition = 'height 0.6s ease';

    setTimeout(() => {
      bar.style.height = targetHeight;
    }, 220 + index * 90);
  });

  const downloadButton = document.querySelector('.navbar .btn-primary');
  if (downloadButton) {
    downloadButton.addEventListener('click', (event) => {
      event.preventDefault();
      const note = document.createElement('div');
      note.textContent = 'Report prepared for download';
      note.style.position = 'fixed';
      note.style.right = '20px';
      note.style.bottom = '20px';
      note.style.background = 'rgba(15, 27, 45, 0.95)';
      note.style.color = '#f4f7fb';
      note.style.padding = '0.8rem 1rem';
      note.style.borderRadius = '999px';
      note.style.border = '1px solid rgba(99, 228, 192, 0.3)';
      note.style.zIndex = '1000';
      document.body.appendChild(note);

      setTimeout(() => {
        note.remove();
      }, 1800);
    });
  }
});
